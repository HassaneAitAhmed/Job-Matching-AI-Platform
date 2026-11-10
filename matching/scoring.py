"""The matching cost model.

A match between a query (a seeker looking for jobs, or a job looking for
candidates) and an item costs ``sum_c w_c * cost_c`` with every ``cost_c`` in
[0, 1]; the match score shown to users is ``100 * (1 - cost)``.

Every criterion is implemented twice:

* ``ItemScorer.costs`` -- the exact cost for a batch of items (vectorised);
* ``ItemScorer.lower_bounds`` -- a lower bound valid for *every* item in a
  cluster, computed from the cluster summary.

Each per-criterion cost is monotone in the summarised quantity (e.g. the
salary cost only decreases as the offered salary increases), so evaluating it
at the most favourable extreme of the cluster gives a bound that never
over-estimates.  On a single-item cluster the bound equals the exact cost.
These two properties make the A* heuristic admissible and consistent (see
``tests/test_search.py``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .normalize import EDUCATION_VALUES, education_rank

SEEKER_TO_JOB = "seeker_to_job"
JOB_TO_SEEKER = "job_to_seeker"
DIRECTIONS = (SEEKER_TO_JOB, JOB_TO_SEEKER)

CRITERIA = ("sector", "contract_type", "education", "location", "experience", "salary", "skills")

# Relative importance per perspective (from the original problem formulation),
# normalised to sum to 1.
_RAW_WEIGHTS = {
    SEEKER_TO_JOB: {"sector": 0.14, "contract_type": 0.12, "education": 0.12, "location": 0.15,
                    "experience": 0.10, "salary": 0.12, "skills": 0.25},
    JOB_TO_SEEKER: {"sector": 0.15, "contract_type": 0.10, "education": 0.12, "location": 0.20,
                    "experience": 0.18, "salary": 0.15, "skills": 0.20},
}
WEIGHTS = {
    d: np.array([w[c] / sum(w.values()) for c in CRITERIA]) for d, w in _RAW_WEIGHTS.items()
}

# Tunable shape parameters.
LOCATION_SCALE_KM = 250.0     # cost = 1 - exp(-km / scale): 50 km -> 0.18, 250 km -> 0.63
EDU_COST_PER_LEVEL = 0.4      # one level below requirement -> 0.4, three or more -> 1.0
OVER_EXP_PER_YEAR = 0.06      # mild penalty per year above the maximum ...
OVER_EXP_CAP = 0.6            # ... capped so over-qualified people are never fully excluded
SALARY_TOLERANCE = 0.3        # offer 30 % below expectation -> full salary cost
UNLISTED_SKILLS_COST = 0.7    # no skills listed: treated as a weak match (~1/3 coverage)

_EDU_RANK = {v: education_rank(v) for v in EDUCATION_VALUES}


@dataclass
class Query:
    """What the user asks for. ``None`` / empty means "no preference"."""

    direction: str
    sector: str | None = None
    contract_type: str | None = None
    edu_value: int | None = None
    city: str | None = None
    years: float | None = None      # seeker queries: years of experience
    exp_lo: float | None = None     # job queries: required experience range
    exp_hi: float | None = None
    salary: float | None = None     # expected (seeker) or offered (job)
    skills: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")
        self.skills = tuple(self.skills)
        if self.exp_lo is not None and self.exp_hi is not None and self.exp_hi < self.exp_lo:
            raise ValueError("exp_hi must be >= exp_lo")


# ---------------------------------------------------------------------------
# Scalar building blocks (shared by exact costs and bounds)
# ---------------------------------------------------------------------------

def education_cost(have: float, required: float) -> float:
    gap = _rank(required) - _rank(have)
    return min(1.0, EDU_COST_PER_LEVEL * gap) if gap > 0 else 0.0


def under_experience_cost(years: float, lo: float) -> float:
    return min(1.0, (lo - years) / max(lo, 1.0))


def over_experience_cost(years: float, hi: float) -> float:
    return min(OVER_EXP_CAP, OVER_EXP_PER_YEAR * (years - hi))


def experience_cost(years: float, lo: float, hi: float) -> float:
    if years < lo:
        return under_experience_cost(years, lo)
    if years > hi:
        return over_experience_cost(years, hi)
    return 0.0


def salary_cost(expected: float, offered: float) -> float:
    if expected <= 0 or offered >= expected:
        return 0.0
    return min(1.0, (expected - offered) / (SALARY_TOLERANCE * expected))


def location_cost(km: float) -> float:
    if not math.isfinite(km):
        return 1.0
    return 1.0 - math.exp(-km / LOCATION_SCALE_KM)


def _rank(value: float) -> int:
    r = _EDU_RANK.get(value)
    return r if r is not None else education_rank(value)


# ---------------------------------------------------------------------------
# Prepared query + scorer over one side of the market
# ---------------------------------------------------------------------------

@dataclass
class PreparedQuery:
    query: Query
    weights: np.ndarray
    dist_row: np.ndarray | None          # km from query city to every matrix city
    skill_match: frozenset | None        # SEEKER_TO_JOB: vocab ids matching any query skill
    skill_match_vec: object | None
    skill_reqs: list | None              # JOB_TO_SEEKER: per required skill, vocab ids that satisfy it
    skill_reqs_mat: object | None


class ItemScorer:
    """Scores queries against the items of one side (jobs or seekers)."""

    def __init__(self, items, direction, distances, city_index, vocab):
        self.direction = direction
        self.items = items
        self.distances = distances
        self.city_index = city_index
        self.vocab = vocab
        self.weights = WEIGHTS[direction]

        self.sector = items["sector"].to_numpy(dtype=object)
        self.contract = items["contract_type"].to_numpy(dtype=object)
        self.edu_rank = np.array([_rank(v) for v in items["edu_value"]], dtype=float)
        self.city_idx = items["city_idx"].to_numpy(dtype=int)
        if direction == SEEKER_TO_JOB:     # items are jobs
            self.lo = items["exp_lo"].to_numpy(dtype=float)
            self.hi = items["exp_hi"].to_numpy(dtype=float)
        else:                              # items are seekers
            self.lo = self.hi = items["years"].to_numpy(dtype=float)
        self.salary = items["salary"].to_numpy(dtype=float)
        self.skill_ids = list(items["skill_ids"])
        self.skill_count = np.array([len(s) for s in self.skill_ids], dtype=float)
        self.skill_matrix = vocab.item_matrix(self.skill_ids)

    # -- query preparation ---------------------------------------------------
    def prepare(self, q: Query) -> PreparedQuery:
        if q.direction != self.direction:
            raise ValueError("query direction does not match scorer")
        dist_row = None
        if q.city is not None:
            ci = self.city_index.get(q.city)
            dist_row = self.distances[ci] if ci is not None else np.full(len(self.distances), np.inf)
        match = match_vec = reqs = reqs_mat = None
        if q.skills:
            if self.direction == SEEKER_TO_JOB:
                match = self.vocab.related_union(q.skills)
                match_vec = self.vocab.indicator(match)
            else:
                reqs = [self.vocab.related(s) for s in q.skills]
                reqs_mat = self.vocab.item_matrix(reqs)
        return PreparedQuery(q, self.weights, dist_row, match, match_vec, reqs, reqs_mat)

    # -- exact costs -------------------------------------------------------------
    def costs(self, pq: PreparedQuery, idx: np.ndarray | None = None) -> np.ndarray:
        """Per-criterion exact costs, shape (n, len(CRITERIA))."""
        q = pq.query
        sel = slice(None) if idx is None else idx
        n = len(self.sector) if idx is None else len(idx)
        out = np.zeros((n, len(CRITERIA)))

        if q.sector is not None:
            out[:, 0] = self.sector[sel] != q.sector
        if q.contract_type is not None:
            out[:, 1] = self.contract[sel] != q.contract_type
        if q.edu_value is not None:
            qr = _rank(q.edu_value)
            gap = (self.edu_rank[sel] - qr) if self.direction == SEEKER_TO_JOB else (qr - self.edu_rank[sel])
            out[:, 2] = np.clip(EDU_COST_PER_LEVEL * gap, 0.0, 1.0)
        if pq.dist_row is not None:
            ci = self.city_idx[sel]
            km = np.where(ci >= 0, pq.dist_row[np.maximum(ci, 0)], np.inf)
            with np.errstate(over="ignore"):
                out[:, 3] = np.where(np.isfinite(km), 1.0 - np.exp(-km / LOCATION_SCALE_KM), 1.0)
        if self.direction == SEEKER_TO_JOB:
            if q.years is not None:
                out[:, 4] = _vec_experience(q.years, self.lo[sel], self.hi[sel])
            if q.salary is not None:
                out[:, 5] = _vec_salary(np.full(n, q.salary), self.salary[sel])
        else:
            if q.exp_lo is not None:
                lo = q.exp_lo
                hi = q.exp_hi if q.exp_hi is not None else lo
                out[:, 4] = _vec_experience(self.lo[sel], lo, hi)
            if q.salary is not None:
                out[:, 5] = _vec_salary(self.salary[sel], np.full(n, q.salary))
        if q.skills:
            out[:, 6] = self._skill_costs(pq, idx)
        return out

    def _skill_costs(self, pq, idx):
        X = self.skill_matrix if idx is None else self.skill_matrix[idx]
        counts = self.skill_count if idx is None else self.skill_count[idx]
        if self.direction == SEEKER_TO_JOB:
            covered = np.asarray((X @ pq.skill_match_vec.T).todense()).ravel()
            with np.errstate(divide="ignore", invalid="ignore"):
                cost = 1.0 - np.minimum(1.0, covered / counts)
        else:
            n_req = len(pq.skill_reqs)
            hits = (X @ pq.skill_reqs_mat.T).toarray() > 0
            cost = 1.0 - hits.sum(axis=1) / n_req
        return np.where(counts == 0, UNLISTED_SKILLS_COST, cost)

    # -- bounds over a cluster ---------------------------------------------------
    def lower_bounds(self, pq: PreparedQuery, s) -> np.ndarray:
        """Per-criterion lower bounds over every item summarised by ``s``."""
        q = pq.query
        lb = np.zeros(len(CRITERIA))
        if q.sector is not None:
            lb[0] = 0.0 if q.sector in s.sectors else 1.0
        if q.contract_type is not None:
            lb[1] = 0.0 if q.contract_type in s.contracts else 1.0
        if q.edu_value is not None:
            if self.direction == SEEKER_TO_JOB:
                lb[2] = education_cost(q.edu_value, s.edu_min)
            else:
                lb[2] = education_cost(s.edu_max, q.edu_value)
        if pq.dist_row is not None:
            valid = s.city_idxs[s.city_idxs >= 0]
            km = float(pq.dist_row[valid].min()) if len(valid) else math.inf
            lb[3] = location_cost(km)
        if self.direction == SEEKER_TO_JOB:
            if q.years is not None:
                y = q.years
                if y < s.lo_min:
                    lb[4] = under_experience_cost(y, s.lo_min)
                elif y > s.hi_max:
                    lb[4] = over_experience_cost(y, s.hi_max)
            if q.salary is not None:
                lb[5] = salary_cost(q.salary, s.salary_max)
        else:
            if q.exp_lo is not None:
                lo = q.exp_lo
                hi = q.exp_hi if q.exp_hi is not None else lo
                if s.hi_max < lo:          # every candidate is under-experienced
                    lb[4] = under_experience_cost(s.hi_max, lo)
                elif s.lo_min > hi:        # every candidate is over-experienced
                    lb[4] = over_experience_cost(s.lo_min, hi)
            if q.salary is not None:
                lb[5] = salary_cost(s.salary_min, q.salary)
        if q.skills:
            best = math.inf
            if s.any_unlisted:
                best = UNLISTED_SKILLS_COST
            if s.any_listed:
                if self.direction == SEEKER_TO_JOB:
                    covered = len(s.skill_union & pq.skill_match)
                    best = min(best, 1.0 - min(1.0, covered / s.skill_min_count))
                else:
                    covered = sum(1 for r in pq.skill_reqs if not s.skill_union.isdisjoint(r))
                    best = min(best, 1.0 - covered / len(pq.skill_reqs))
            lb[6] = best
        return lb


def _vec_experience(years, lo, hi):
    years, lo, hi = np.broadcast_arrays(
        np.asarray(years, dtype=float), np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
    )
    under = np.minimum(1.0, (lo - years) / np.maximum(lo, 1.0))
    over = np.minimum(OVER_EXP_CAP, OVER_EXP_PER_YEAR * (years - hi))
    return np.where(years < lo, under, np.where(years > hi, over, 0.0))


def _vec_salary(expected, offered):
    expected = np.asarray(expected, dtype=float)
    offered = np.asarray(offered, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        raw = np.minimum(1.0, (expected - offered) / (SALARY_TOLERANCE * expected))
    return np.where((expected <= 0) | (offered >= expected), 0.0, raw)


def breakdown(costs_row: np.ndarray, weights: np.ndarray) -> dict:
    """Per-criterion score (0-100) and weight (%) for display."""
    return {
        c: {"score": round(100 * (1 - float(costs_row[i])), 1), "weight": round(100 * float(weights[i]), 1)}
        for i, c in enumerate(CRITERIA)
    }
