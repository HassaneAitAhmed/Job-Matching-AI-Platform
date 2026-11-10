"""Evaluation harness.

There is no ground truth for "good match" in the bundled data, so the
benchmarks measure what *can* be measured honestly:

1. Planted-match recovery: build a query from a known item (optionally with
   noise) and check where that item is ranked.  Tests that the cost model and
   the search behave sensibly; it is *not* a measure of real-world relevance.
2. Agreement with the exhaustive optimum, and speed, for each algorithm.
3. GA vs the exact optimum (Hungarian) and a greedy baseline on batch assignment.
4. If human relevance labels exist (``eval/labels.csv``), precision@k and nDCG@k.
   ``make_labeling_sheet`` produces the file to label.
"""

from __future__ import annotations

import csv
import math
import platform
import random
import time
from pathlib import Path

import numpy as np

from .scoring import JOB_TO_SEEKER, SEEKER_TO_JOB, Query

SEARCH_ALGORITHMS = ("astar", "greedy", "csp", "exhaustive")


# ---------------------------------------------------------------------------
# Query generators
# ---------------------------------------------------------------------------

def _nearby_city(matcher, city, rng, max_km=200):
    ds = matcher.dataset
    i = ds.city_index[city]
    near = [c for c, j in ds.city_index.items() if 0 < ds.distances[i, j] <= max_km]
    return rng.choice(near) if near else city


def planted_query(matcher, direction, row, rng, noisy=False) -> Query:
    if direction == SEEKER_TO_JOB:
        j = matcher.jobs.iloc[row]
        skills = list(j.skills)
        years = (j.exp_lo + j.exp_hi) / 2
        q = dict(sector=j.sector, contract_type=j.contract_type, edu_value=int(j.edu_value), city=j.city,
                 years=float(years), salary=float(j.salary), skills=tuple(skills))
    else:
        s = matcher.seekers.iloc[row]
        skills = list(s.skills)
        k = min(len(skills), rng.randint(2, 4))
        skills = rng.sample(skills, k)
        q = dict(sector=s.sector, contract_type=s.contract_type, edu_value=int(s.edu_value), city=s.city,
                 exp_lo=float(max(0, s.years - 1)), exp_hi=float(s.years + 1), salary=float(s.salary),
                 skills=tuple(skills))
    if noisy:
        if rng.random() < 0.3:
            q["sector"] = None
        if rng.random() < 0.3:
            q["contract_type"] = None
        if rng.random() < 0.5:
            q["city"] = _nearby_city(matcher, q["city"], rng)
        q["salary"] = q["salary"] * rng.uniform(0.9, 1.1)
        if q["skills"]:
            keep = max(1, len(q["skills"]) // 2)
            q["skills"] = tuple(rng.sample(list(q["skills"]), keep))
        if direction == SEEKER_TO_JOB:
            q["years"] = max(0.0, q["years"] + rng.choice([-1, 0, 1]))
    return Query(direction=direction, **q)


def dataset_queries(matcher, direction, n, seed=0) -> list[Query]:
    """Real items from the *other* side used as queries, with random fields left blank."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if direction == SEEKER_TO_JOB:
            q = matcher.query_from_seeker(int(rng.choice(matcher.seekers["id"].tolist())))
        else:
            q = matcher.query_from_job(int(rng.choice(matcher.jobs["id"].tolist())))
        fields = q.__dict__.copy()
        for f in ("sector", "contract_type", "edu_value", "city", "salary"):
            if rng.random() < 0.3:
                fields[f] = None
        out.append(Query(**fields))
    return out


# ---------------------------------------------------------------------------
# 1. Planted-match recovery
# ---------------------------------------------------------------------------

def planted_recovery(matcher, direction, n=200, noisy=False, seed=0, depth=50,
                     algorithms=("astar", "greedy", "csp")) -> dict:
    rng = random.Random(seed)
    items = matcher.jobs if direction == SEEKER_TO_JOB else matcher.seekers
    pool = np.flatnonzero(items["skills_listed"].to_numpy())
    rows = rng.sample(pool.tolist(), min(n, len(pool)))
    scorer = matcher.scorers[direction]
    res = {a: {"hit@1": 0, "hit@10": 0, "rr": 0.0} for a in algorithms}
    tie_ranks = []
    for row in rows:
        q = planted_query(matcher, direction, row, rng, noisy)
        target = int(items["id"].iloc[row])
        pq = scorer.prepare(q)
        total = scorer.costs(pq) @ pq.weights
        better = int((total < total[row] - 1e-12).sum())
        ties = int((np.abs(total - total[row]) <= 1e-12).sum()) - 1
        tie_ranks.append(1 + better + ties / 2)
        for a in algorithms:
            ids = [h["id"] for h in matcher.search(q, a, k=depth).hits]
            if target in ids:
                r = ids.index(target) + 1
                res[a]["hit@1"] += r == 1
                res[a]["hit@10"] += r <= 10
                res[a]["rr"] += 1 / r
    m = len(rows)
    out = {a: {"hit@1": v["hit@1"] / m, "hit@10": v["hit@10"] / m, "MRR@50": v["rr"] / m} for a, v in res.items()}
    out["_expected_rank_median"] = float(np.median(tie_ranks))
    out["_n"] = m
    return out


# ---------------------------------------------------------------------------
# 2. Agreement with the optimum + speed
# ---------------------------------------------------------------------------

def agreement_and_speed(matcher, direction, n=100, k=10, seed=0) -> dict:
    queries = dataset_queries(matcher, direction, n, seed)
    for q in queries[:3]:  # warm-up
        for a in SEARCH_ALGORITHMS:
            matcher.search(q, a, k=k)
    rows = {a: {"ms": [], "wall_ms": [], "scored": [], "expanded": [], "optimal_topk": 0,
                "score_ratio": [], "relaxed": 0} for a in SEARCH_ALGORITHMS}
    for q in queries:
        best = matcher.search(q, "exhaustive", k=k)
        best_scores = np.array([h["match_score"] for h in best.hits])
        for a in SEARCH_ALGORITHMS:
            t0 = time.perf_counter()
            r = matcher.search(q, a, k=k)
            rows[a]["wall_ms"].append(1000 * (time.perf_counter() - t0))
            rows[a]["ms"].append(r.stats.elapsed_ms)
            rows[a]["scored"].append(r.stats.items_scored)
            rows[a]["expanded"].append(r.stats.nodes_expanded)
            scores = np.array([h["match_score"] for h in r.hits])
            if len(scores) == len(best_scores) and np.allclose(scores, best_scores, atol=1e-6):
                rows[a]["optimal_topk"] += 1
            if len(scores):
                rows[a]["score_ratio"].append(scores.mean() / best_scores.mean())
            if r.stats.extra.get("relaxed_constraints"):
                rows[a]["relaxed"] += 1
    out = {}
    for a, v in rows.items():
        out[a] = {
            "median_ms": float(np.median(v["ms"])),
            "p95_ms": float(np.percentile(v["ms"], 95)),
            "median_wall_ms": float(np.median(v["wall_ms"])),
            "median_items_scored": float(np.median(v["scored"])),
            "median_nodes_expanded": float(np.median(v["expanded"])),
            "optimal_topk_rate": v["optimal_topk"] / n,
            "mean_score_vs_optimal": float(np.mean(v["score_ratio"])) if v["score_ratio"] else float("nan"),
            "relaxed_rate": v["relaxed"] / n,
        }
    out["_n"] = n
    out["_items"] = len(matcher.scorers[direction].items)
    return out


# ---------------------------------------------------------------------------
# 3. Batch assignment
# ---------------------------------------------------------------------------

def assignment_benchmark(matcher, sizes=((20, 8), (40, 15), (100, 40)), seeds=range(5), generations=200) -> list:
    out = []
    for n_s, n_j in sizes:
        acc = {}
        for seed in seeds:
            r = matcher.assign(n_s, n_j, seed=seed, ga_params={"generations": generations})
            for x in r["results"]:
                acc.setdefault(x["method"], {"pct": [], "ms": []})
                acc[x["method"]]["pct"].append(x["pct_of_optimal"])
                acc[x["method"]]["ms"].append(x["elapsed_ms"])
        out.append({
            "size": f"{n_s} seekers x {n_j} jobs",
            **{m: {"mean_pct_of_optimal": float(np.mean(v["pct"])), "min_pct": float(np.min(v["pct"])),
                   "mean_ms": float(np.mean(v["ms"]))} for m, v in acc.items()},
        })
    return out


# ---------------------------------------------------------------------------
# 4. Human labels
# ---------------------------------------------------------------------------

def make_labeling_sheet(matcher, out_path, n_queries=25, k=5, seed=0):
    """Pool the top-k of every algorithm plus random items for each query; humans fill `relevance` (0-3)."""
    rng = random.Random(seed)
    rows = []
    for direction in (SEEKER_TO_JOB, JOB_TO_SEEKER):
        src = matcher.seekers if direction == SEEKER_TO_JOB else matcher.jobs
        other = matcher.jobs if direction == SEEKER_TO_JOB else matcher.seekers
        for qid in rng.sample(src["id"].tolist(), n_queries):
            q = matcher.query_from_seeker(qid) if direction == SEEKER_TO_JOB else matcher.query_from_job(qid)
            pool = set()
            for a in ("astar", "greedy", "csp"):
                pool.update(h["id"] for h in matcher.search(q, a, k=k).hits)
            pool.update(rng.sample(other["id"].tolist(), 3))
            for cid in sorted(pool, key=lambda _: rng.random()):
                rows.append({
                    "direction": direction, "query_id": qid, "query": _summary(matcher, direction, qid, query=True),
                    "candidate_id": cid, "candidate": _summary(matcher, direction, cid, query=False),
                    "relevance": "", "notes": "",
                })
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _summary(matcher, direction, item_id, query):
    is_seeker = (direction == SEEKER_TO_JOB) == query
    if is_seeker:
        s = matcher.seekers.set_index("id").loc[item_id]
        return (f"seeker | {s.sector} | {s.contract_type} | edu {s.edu_value} | {s.city} | {s.years}y | "
                f"{s.salary:.0f} DZD | {', '.join(s.skills)}")
    j = matcher.jobs.set_index("id").loc[item_id]
    return (f"job: {j.title} | {j.sector} | {j.contract_type} | edu {j.edu_value} | {j.city} | "
            f"{j.exp_lo}-{j.exp_hi}y | {j.salary:.0f} DZD | {', '.join(j.skills) or '(no skills listed)'}")


def labeled_metrics(matcher, labels_path, k=10, relevant_at=2) -> dict:
    labels: dict = {}
    with open(labels_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["relevance"].strip() == "":
                continue
            labels.setdefault((r["direction"], int(r["query_id"])), {})[int(r["candidate_id"])] = int(r["relevance"])
    if not labels:
        return {}
    out = {}
    for a in ("astar", "greedy", "csp", "exhaustive"):
        p_at_k, ndcg, judged = [], [], []
        for (direction, qid), rel in labels.items():
            q = matcher.query_from_seeker(qid) if direction == SEEKER_TO_JOB else matcher.query_from_job(qid)
            ids = [h["id"] for h in matcher.search(q, a, k=k).hits]
            gains = [rel.get(i, 0) for i in ids]
            judged.append(sum(i in rel for i in ids) / len(ids))
            p_at_k.append(sum(g >= relevant_at for g in gains) / k)
            dcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(gains))
            ideal = sorted(rel.values(), reverse=True)[:k]
            idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
            ndcg.append(dcg / idcg if idcg else 0.0)
        out[a] = {f"P@{k}": float(np.mean(p_at_k)), f"nDCG@{k}": float(np.mean(ndcg)),
                  "judged_fraction": float(np.mean(judged))}
    out["_queries"] = len(labels)
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def run_all(matcher, quick=False, labels_path=None) -> str:
    n_planted = 60 if quick else 300
    n_agree = 30 if quick else 200
    lines = ["# Benchmarks", "",
             f"Generated by `python -m matching evaluate{' --quick' if quick else ''}` on Python {platform.python_version()} "
             f"({platform.system()} {platform.machine()}). Re-run it after changing the model.", "",
             "> The bundled datasets appear to be synthetic (see [DATA.md](DATA.md)). These numbers "
             "describe algorithm behaviour, not real-world hiring quality.", ""]

    lines += ["## 1. Planted-match recovery", "",
              "A query is built from a known item (a job's own requirements, or a seeker's own profile), and "
              "we record where that item is ranked. In the *noisy* variant, sector or contract may be blank, "
              "the city may be swapped for one within 200 km, and salary, skills and experience are "
              "perturbed. This checks that the model is sensible; it does not measure real-world relevance.", ""]
    for direction in (SEEKER_TO_JOB, JOB_TO_SEEKER):
        for noisy in (False, True):
            r = planted_recovery(matcher, direction, n=n_planted, noisy=noisy)
            lines.append(f"**{direction}, {'noisy' if noisy else 'exact'}** (n={r['_n']}, "
                         f"median rank of the source item among all items, ties split: "
                         f"{r['_expected_rank_median']:.1f})")
            lines.append("")
            lines.append("| algorithm | hit@1 | hit@10 | MRR@50 |")
            lines.append("|---|---|---|---|")
            for a in ("astar", "greedy", "csp"):
                v = r[a]
                lines.append(f"| {a} | {v['hit@1']:.1%} | {v['hit@10']:.1%} | {v['MRR@50']:.3f} |")
            lines.append("")

    lines += ["## 2. Agreement with the exhaustive optimum, and speed", "",
              "These queries are real items from the other side of the market, with sector, contract, "
              "education, city or salary each left blank 30% of the time. k = 10. *Optimal top-k* means the "
              "algorithm's 10 scores equal the exhaustive top 10. Times are for the algorithm only "
              "(`stats.elapsed_ms`). The exhaustive baseline is a vectorised NumPy pass, which is why it is "
              "fast on 754 / 8,124 items. A* wins on *items scored*, which is what matters when scoring is "
              "expensive or the catalogue is large.", ""]
    for direction in (SEEKER_TO_JOB, JOB_TO_SEEKER):
        r = agreement_and_speed(matcher, direction, n=n_agree)
        lines.append(f"**{direction}** (n={r['_n']} queries over {r['_items']} items)")
        lines.append("")
        lines.append("| algorithm | optimal top-k | mean score vs optimal | median ms | p95 ms | "
                     "median items scored | median nodes expanded | CSP relaxed |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for a in SEARCH_ALGORITHMS:
            v = r[a]
            relaxed = f"{v['relaxed_rate']:.0%}" if a == "csp" else "-"
            lines.append(f"| {a} | {v['optimal_topk_rate']:.0%} | {v['mean_score_vs_optimal']:.1%} | "
                         f"{v['median_ms']:.2f} | {v['p95_ms']:.2f} | {v['median_items_scored']:.0f} | "
                         f"{v['median_nodes_expanded']:.0f} | {relaxed} |")
        lines.append("")
    lines.append("The CSP is *expected* to differ from the optimum: it removes items that break a hard "
                 "constraint, even when they would score well on the soft criteria.")
    lines.append("")

    lines += ["## 3. Batch assignment: GA vs optimal", "",
              "Random batches of seekers and job postings; each job accepts up to its number of `available "
              "posts`. Pair score = mean of the seeker's and the employer's perspective. Optimal = Hungarian "
              "algorithm (`scipy.optimize.linear_sum_assignment`). GA: population 60, 200 generations, "
              "5 seeds per size.", ""]
    lines.append("| batch | method | mean % of optimal | worst % | mean ms |")
    lines.append("|---|---|---|---|---|")
    sizes = ((20, 8), (40, 15)) if quick else ((20, 8), (40, 15), (100, 40))
    for row in assignment_benchmark(matcher, sizes=sizes, seeds=range(3 if quick else 5)):
        for m in ("optimal (Hungarian)", "greedy", "genetic algorithm"):
            v = row[m]
            lines.append(f"| {row['size']} | {m} | {v['mean_pct_of_optimal']:.1f}% | {v['min_pct']:.1f}% | "
                         f"{v['mean_ms']:.1f} |")
    lines.append("")

    lines += ["## 4. Human relevance labels", ""]
    if labels_path and Path(labels_path).exists():
        r = labeled_metrics(matcher, labels_path)
        if r:
            lines.append(f"{r['_queries']} labelled queries; relevance >= 2 counts as relevant.")
            lines.append("")
            lines.append("| algorithm | P@10 | nDCG@10 | judged fraction |")
            lines.append("|---|---|---|---|")
            for a in ("astar", "greedy", "csp", "exhaustive"):
                v = r[a]
                lines.append(f"| {a} | {v['P@10']:.3f} | {v['nDCG@10']:.3f} | {v['judged_fraction']:.0%} |")
        else:
            lines.append("`eval/labels.csv` exists but has no filled-in `relevance` values yet.")
    else:
        lines.append("Not available yet. Run `python -m matching label-sheet` and have people fill in the "
                     "`relevance` column (0 = irrelevant ... 3 = excellent). Save the result as "
                     "`eval/labels.csv`, then re-run the evaluation. Only human labels can show whether the "
                     "scores reflect real matching quality.")
    lines.append("")
    return "\n".join(lines)
