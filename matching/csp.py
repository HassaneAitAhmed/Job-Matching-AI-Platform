"""Constraint satisfaction formulation of matching.

Variables  -- the attributes of the matched item, in tree order:
              sector, contract_type, edu_value, city, then the item itself.
Domains    -- the values that actually occur (the children of each tree node);
              the tree is a table constraint, so only existing items are solutions.
Constraints (hard, all optional / tunable):
    C1 same sector           C2 same contract type
    C3 education requirement met
    C4 distance <= max_distance_km
    C5 salary: offer >= min_salary_ratio * expectation
    C6 experience within [lo - slack, hi + slack]

Solving: backtracking over the tree with
  * node consistency  -- unary constraints C1-C4 prune domain values;
  * forward checking  -- after each assignment the remaining subtree's summary
                          is checked against C5/C6; empty future domains prune;
  * value ordering    -- children are tried by their soft-cost lower bound.

All solutions are collected and ranked by the soft score from ``scoring``.
If fewer than ``k`` solutions exist, constraints are relaxed one at a time
(``RELAXATION_ORDER``) and the response reports which ones were dropped.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace

import numpy as np

from .scoring import JOB_TO_SEEKER, SEEKER_TO_JOB, _rank
from .search import Hit, SearchStats


@dataclass(frozen=True)
class Constraints:
    same_sector: bool = True
    same_contract: bool = True
    education: bool = True
    max_distance_km: float | None = 300.0
    min_salary_ratio: float | None = 0.9
    experience_slack: float | None = 2.0


RELAXATION_ORDER = (
    ("max_distance_km", None),
    ("experience_slack", None),
    ("min_salary_ratio", None),
    ("education", False),
    ("same_contract", False),
    ("same_sector", False),
)


class MatchingCSP:
    def __init__(self, scorer, tree, pq, constraints: Constraints = Constraints()):
        self.scorer = scorer
        self.tree = tree
        self.pq = pq
        self.q = pq.query
        self.c = constraints
        self.direction = scorer.direction

    # -- unary constraints on tree-level values (node consistency) ---------------
    def _value_ok(self, attr, value) -> bool:
        q, c = self.q, self.c
        if attr == "sector":
            return not (c.same_sector and q.sector is not None) or value == q.sector
        if attr == "contract_type":
            return not (c.same_contract and q.contract_type is not None) or value == q.contract_type
        if attr == "edu_value":
            if not c.education or q.edu_value is None:
                return True
            if self.direction == SEEKER_TO_JOB:
                return _rank(value) <= _rank(q.edu_value)
            return _rank(value) >= _rank(q.edu_value)
        return True

    def _city_ok(self, node) -> bool:
        """Unary distance constraint; city values are names, so check the node's city index."""
        if self.c.max_distance_km is None or self.pq.dist_row is None:
            return True
        idxs = node.summary.city_idxs
        idxs = idxs[idxs >= 0]
        return len(idxs) > 0 and float(self.pq.dist_row[idxs].min()) <= self.c.max_distance_km

    # -- forward checking on non-tree constraints over a subtree summary ---------
    def _future_feasible(self, s) -> bool:
        q, c = self.q, self.c
        if c.min_salary_ratio is not None and q.salary is not None:
            if self.direction == SEEKER_TO_JOB and s.salary_max < c.min_salary_ratio * q.salary:
                return False
            if self.direction == JOB_TO_SEEKER and q.salary < c.min_salary_ratio * s.salary_min:
                return False
        if c.experience_slack is not None:
            slack = c.experience_slack
            if self.direction == SEEKER_TO_JOB and q.years is not None:
                # need some job with lo - slack <= years <= hi + slack
                if q.years + slack < s.lo_min or q.years - slack > s.hi_max:
                    return False
            if self.direction == JOB_TO_SEEKER and q.exp_lo is not None:
                lo, hi = q.exp_lo, (q.exp_hi if q.exp_hi is not None else q.exp_lo)
                if s.hi_max < lo - slack or s.lo_min > hi + slack:
                    return False
        return True

    # -- full check of a candidate item (leaf) -------------------------------------
    def _item_mask(self, rows) -> np.ndarray:
        q, c, sc = self.q, self.c, self.scorer
        ok = np.ones(len(rows), dtype=bool)
        if c.min_salary_ratio is not None and q.salary is not None:
            if self.direction == SEEKER_TO_JOB:
                ok &= sc.salary[rows] >= c.min_salary_ratio * q.salary
            else:
                ok &= q.salary >= c.min_salary_ratio * sc.salary[rows]
        if c.experience_slack is not None:
            slack = c.experience_slack
            if self.direction == SEEKER_TO_JOB and q.years is not None:
                ok &= (sc.lo[rows] - slack <= q.years) & (q.years <= sc.hi[rows] + slack)
            if self.direction == JOB_TO_SEEKER and q.exp_lo is not None:
                lo, hi = q.exp_lo, (q.exp_hi if q.exp_hi is not None else q.exp_lo)
                y = sc.lo[rows]
                ok &= (lo - slack <= y) & (y <= hi + slack)
        return ok

    def solve(self, k: int):
        t0 = time.perf_counter()
        stats = SearchStats("csp")
        pruned_unary = pruned_forward = 0
        solutions: list[int] = []
        w = self.pq.weights

        def order(children):
            scored = []
            for v, child in children.items():
                lb = self.scorer.lower_bounds(self.pq, child.summary)
                scored.append((float(lb @ w), str(v), child))
            scored.sort(key=lambda t: (t[0], t[1]))
            return [t[2] for t in scored]

        def backtrack(node):
            nonlocal pruned_unary, pruned_forward
            stats.nodes_expanded += 1
            if node.is_leaf:
                rows = node.rows
                stats.items_scored += len(rows)
                solutions.extend(int(r) for r in rows[self._item_mask(rows)])
                return
            for child in order(node.children):
                stats.nodes_generated += 1
                ok = self._city_ok(child) if child.attr == "city" else self._value_ok(child.attr, child.value)
                if not ok:
                    pruned_unary += 1
                    continue
                if not self._future_feasible(child.summary):
                    pruned_forward += 1
                    continue
                backtrack(child)

        backtrack(self.tree.root)

        hits: list[Hit] = []
        if solutions:
            rows = np.array(solutions)
            costs = self.scorer.costs(self.pq, rows)
            total = costs @ w
            ids = self.scorer.items["id"].to_numpy()[rows]
            for i in np.lexsort((ids, total))[:k]:
                hits.append(Hit(int(rows[i]), costs[i], float(total[i])))
        stats.extra = {
            "solutions": len(solutions),
            "pruned_by_node_consistency": pruned_unary,
            "pruned_by_forward_checking": pruned_forward,
        }
        stats.elapsed_ms = 1000 * (time.perf_counter() - t0)
        return hits, stats


def solve_with_relaxation(scorer, tree, pq, k: int, constraints: Constraints = Constraints()):
    """Solve; if fewer than k solutions, relax constraints in RELAXATION_ORDER."""
    relaxed: list[str] = []
    current = constraints
    total_ms = 0.0
    while True:
        hits, stats = MatchingCSP(scorer, tree, pq, current).solve(k)
        total_ms += stats.elapsed_ms
        if len(hits) >= k:
            break
        step = next(((name, val) for name, val in RELAXATION_ORDER if getattr(current, name) != val), None)
        if step is None:
            break
        current = replace(current, **{step[0]: step[1]})
        relaxed.append(step[0])
    stats.elapsed_ms = total_ms
    stats.extra["relaxed_constraints"] = relaxed
    stats.extra["constraints"] = {k_: v for k_, v in current.__dict__.items()}
    return hits, stats
