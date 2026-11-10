"""High-level API used by the web app, the notebook, the tests and the benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import csp as csp_mod
from . import ga as ga_mod
from .data import DATA_DIR, load_dataset
from .normalize import (
    CONTRACT_TYPES,
    EDUCATION_LEVELS,
    canonical_contract,
    canonical_education,
    canonical_sector,
    education_label,
    fold,
)
from .scoring import CRITERIA, JOB_TO_SEEKER, SEEKER_TO_JOB, WEIGHTS, ItemScorer, Query, breakdown
from .search import SearchStats, best_first, exhaustive
from .skills import SkillVocab
from .tree import ClusterTree

ALGORITHMS = ("astar", "greedy", "csp", "exhaustive")


@dataclass
class MatchResult:
    direction: str
    algorithm: str
    hits: list            # list of dicts (see Matcher._describe)
    stats: SearchStats


class Matcher:
    def __init__(self, data_dir: Path | str = DATA_DIR):
        ds = load_dataset(data_dir)
        self.dataset = ds
        self.jobs = ds.jobs
        self.seekers = ds.seekers
        self.vocab = SkillVocab(
            [s for lst in ds.jobs["skills"] for s in lst] + [s for lst in ds.seekers["skills"] for s in lst]
        )
        for df in (self.jobs, self.seekers):
            df["skill_ids"] = [self.vocab.ids(lst) for lst in df["skills"]]

        self.scorers = {
            SEEKER_TO_JOB: ItemScorer(self.jobs, SEEKER_TO_JOB, ds.distances, ds.city_index, self.vocab),
            JOB_TO_SEEKER: ItemScorer(self.seekers, JOB_TO_SEEKER, ds.distances, ds.city_index, self.vocab),
        }
        self.trees = {
            SEEKER_TO_JOB: ClusterTree(self.jobs, entity="job"),
            JOB_TO_SEEKER: ClusterTree(self.seekers, entity="seeker"),
        }
        self._job_row = {int(i): r for r, i in enumerate(self.jobs["id"])}
        self._seeker_row = {int(i): r for r, i in enumerate(self.seekers["id"])}

    @classmethod
    def from_default_data(cls) -> "Matcher":
        return cls(DATA_DIR)

    # ------------------------------------------------------------------ queries
    def make_query(self, direction, *, sector=None, contract_type=None, education=None, city=None,
                   years=None, exp_lo=None, exp_hi=None, salary=None, skills=()) -> Query:
        """Build a Query from loosely-typed user input; raises ValueError on bad values."""
        city_c = None
        if city not in (None, ""):
            city_c = self.dataset.resolver.resolve(city)
            if city_c is None:
                raise ValueError(f"Unknown city: {city!r}")
        return Query(
            direction=direction,
            sector=canonical_sector(sector),
            contract_type=canonical_contract(contract_type),
            edu_value=canonical_education(education),
            city=city_c,
            years=years,
            exp_lo=exp_lo,
            exp_hi=exp_hi,
            salary=salary,
            skills=tuple(skills),
        )

    def query_from_seeker(self, seeker_id: int) -> Query:
        r = self.seekers.iloc[self._seeker_row[seeker_id]]
        return Query(SEEKER_TO_JOB, r.sector, r.contract_type, int(r.edu_value), r.city,
                     years=float(r.years), salary=float(r.salary), skills=tuple(r.skills))

    def query_from_job(self, job_id: int) -> Query:
        r = self.jobs.iloc[self._job_row[job_id]]
        return Query(JOB_TO_SEEKER, r.sector, r.contract_type, int(r.edu_value), r.city,
                     exp_lo=float(r.exp_lo), exp_hi=float(r.exp_hi), salary=float(r.salary),
                     skills=tuple(r.skills))

    # ------------------------------------------------------------------ search
    def search(self, query: Query, algorithm: str = "astar", k: int = 10, offset: int = 0,
               constraints: csp_mod.Constraints | None = None) -> MatchResult:
        if algorithm not in ALGORITHMS:
            raise ValueError(f"algorithm must be one of {ALGORITHMS}")
        scorer = self.scorers[query.direction]
        tree = self.trees[query.direction]
        pq = scorer.prepare(query)
        want = k + offset
        if algorithm == "exhaustive":
            hits, stats = exhaustive(scorer, pq, want)
        elif algorithm == "astar":
            hits, stats = best_first(scorer, tree, pq, want)
        elif algorithm == "greedy":
            hits, stats = best_first(scorer, tree, pq, want, greedy=True)
            # Greedy finds items in discovery order; show them best-first.
            hits.sort(key=lambda h: h.cost)
        else:
            hits, stats = csp_mod.solve_with_relaxation(scorer, tree, pq, want, constraints or csp_mod.Constraints())
        hits = hits[offset:]
        return MatchResult(query.direction, algorithm, [self._describe(query.direction, h, pq.weights, pq) for h in hits], stats)

    def _matched_skills(self, pq, skills) -> list:
        """The item's skills that (soft-)match the query's skills."""
        if pq is None or not pq.query.skills:
            return []
        accept = pq.skill_match if pq.skill_match is not None else frozenset().union(*pq.skill_reqs)
        return [s for s in skills if self.vocab.index.get(fold(s)) in accept]

    def _describe(self, direction, hit, weights, pq=None) -> dict:
        if direction == SEEKER_TO_JOB:
            r = self.jobs.iloc[hit.row]
            d = {
                "type": "job",
                "id": int(r.id),
                "title": r.title,
                "department": r.department,
                "experience_required": [int(r.exp_lo), int(r.exp_hi)],
                "education_required": education_label(r.edu_value),
                "salary": float(r.salary),
                "posts": int(r.posts),
            }
        else:
            r = self.seekers.iloc[hit.row]
            d = {
                "type": "seeker",
                "id": int(r.id),
                "department": r.department,
                "experience_years": int(r.years),
                "education": education_label(r.edu_value),
                "salary_expectation": float(r.salary),
                "languages": list(r.languages),
            }
        d.update({
            "sector": r.sector,
            "contract_type": r.contract_type,
            "city": r.city or r.city_raw,
            "skills": list(r.skills),
            "matched_skills": self._matched_skills(pq, r.skills),
            "skills_listed": bool(r.skills_listed),
            "match_score": round(100 * (1 - hit.cost), 2),
            "breakdown": breakdown(hit.costs, weights),
        })
        return d

    # ------------------------------------------------------------------ batch assignment
    def pair_scores(self, seeker_rows, job_rows) -> np.ndarray:
        """Mutual score in [0, 1]: mean of the seeker's and the employer's perspective."""
        s_rows = np.asarray(seeker_rows)
        j_rows = np.asarray(job_rows)
        S = np.zeros((len(s_rows), len(j_rows)))
        s2j = self.scorers[SEEKER_TO_JOB]
        j2s = self.scorers[JOB_TO_SEEKER]
        for a, r in enumerate(s_rows):
            pq = s2j.prepare(self.query_from_seeker(int(self.seekers["id"].iloc[r])))
            S[a] += 1 - s2j.costs(pq, j_rows) @ pq.weights
        for b, r in enumerate(j_rows):
            pq = j2s.prepare(self.query_from_job(int(self.jobs["id"].iloc[r])))
            S[:, b] += 1 - j2s.costs(pq, s_rows) @ pq.weights
        return S / 2

    def assign(self, n_seekers=40, n_jobs=15, sector=None, seed=0, ga_params=None) -> dict:
        rng = np.random.default_rng(seed)
        sector = canonical_sector(sector)
        s_pool = np.flatnonzero((self.seekers["sector"] == sector).to_numpy()) if sector else np.arange(len(self.seekers))
        j_pool = np.flatnonzero((self.jobs["sector"] == sector).to_numpy()) if sector else np.arange(len(self.jobs))
        if not len(s_pool) or not len(j_pool):
            raise ValueError("No seekers or jobs in that sector")
        s_rows = rng.choice(s_pool, size=min(n_seekers, len(s_pool)), replace=False)
        j_rows = rng.choice(j_pool, size=min(n_jobs, len(j_pool)), replace=False)
        S = self.pair_scores(s_rows, j_rows)
        cap = self.jobs["posts"].to_numpy()[j_rows].astype(int)

        opt = ga_mod.optimal_assignment(S, cap)
        greedy = ga_mod.greedy_assignment(S, cap)
        ga = ga_mod.AssignmentGA(S, cap, seed=seed, **(ga_params or {})).run()

        def pack(res):
            out = {
                "method": res.method,
                "total_score": round(res.total, 4),
                "pct_of_optimal": round(100 * res.total / opt.total, 2) if opt.total else 100.0,
                "assigned": int((res.genes >= 0).sum()),
                "elapsed_ms": round(res.elapsed_ms, 2),
            }
            if res.generations_to_best is not None:
                out["generations_to_best"] = res.generations_to_best
            return out

        pairs = []
        for i in np.argsort(-S[np.arange(len(s_rows)), np.maximum(opt.genes, 0)]):
            j = opt.genes[i]
            if j < 0:
                continue
            pairs.append({
                "seeker_id": int(self.seekers["id"].iloc[s_rows[i]]),
                "job_id": int(self.jobs["id"].iloc[j_rows[j]]),
                "job_title": self.jobs["title"].iloc[j_rows[j]],
                "score": round(100 * S[i, j], 2),
                "ga_agrees": bool(ga.genes[i] == j),
            })
        return {
            "n_seekers": len(s_rows),
            "n_jobs": len(j_rows),
            "total_posts": int(cap.sum()),
            "results": [pack(opt), pack(greedy), pack(ga)],
            "ga_history": [round(v, 4) for v in ga.history[:: max(1, len(ga.history) // 50)]],
            "optimal_pairs": pairs[:25],
        }

    # ------------------------------------------------------------------ metadata
    def options(self) -> dict:
        sectors = sorted((set(self.jobs["sector"]) | set(self.seekers["sector"])) - {"Unknown"})
        cities = sorted(set(c for c in self.jobs["city"].dropna()) | set(c for c in self.seekers["city"].dropna()))
        return {
            "sectors": sectors,
            "cities": cities,
            "contract_types": [{"value": k, "label": v} for k, v in CONTRACT_TYPES.items()],
            "education_levels": [{"value": v, "label": l} for v, l in EDUCATION_LEVELS],
            "algorithms": list(ALGORITHMS),
            "criteria": list(CRITERIA),
            "weights": {d: {c: round(100 * float(w[i]), 1) for i, c in enumerate(CRITERIA)} for d, w in WEIGHTS.items()},
        }

    def stats(self) -> dict:
        return {
            "total_jobs": len(self.jobs),
            "total_seekers": len(self.seekers),
            "sectors": len(self.options()["sectors"]),
            "cities": len(self.options()["cities"]),
            "jobs_without_skills": int((~self.jobs["skills_listed"]).sum()),
            "skill_vocabulary": len(self.vocab),
            "tree_nodes": {d: t.n_nodes for d, t in self.trees.items()},
        }
