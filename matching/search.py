"""Best-first search over the cluster tree: A*, greedy best-first, and an exhaustive baseline.

State space: tree nodes plus individual items (goal states).  Expanding an
inner node generates its children; expanding a leaf generates its items.

* ``g(n)`` -- exact cost of the criteria already decided on the path
  (every item below a node shares those values);
* ``h(n)`` -- lower bound of the remaining criteria over the node's items.

Because the bounds never over-estimate and only tighten as clusters shrink,
A* pops goal items in non-decreasing order of true cost: its top-k equals the
exhaustive top-k (verified in ``tests/test_search.py``).  Greedy best-first
orders the frontier by ``h`` alone, which is faster but not optimal.
"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field

import numpy as np

from .scoring import CRITERIA
from .tree import LEVEL_CRITERION

_ITEM, _NODE = 0, 1


@dataclass
class SearchStats:
    algorithm: str
    nodes_expanded: int = 0
    nodes_generated: int = 0
    items_scored: int = 0
    max_frontier: int = 0
    elapsed_ms: float = 0.0
    extra: dict = field(default_factory=dict)

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "extra"}
        d["elapsed_ms"] = round(self.elapsed_ms, 3)
        d.update(self.extra)
        return d


@dataclass
class Hit:
    row: int
    costs: np.ndarray       # per-criterion exact costs
    cost: float             # weighted total
    path: list = field(default_factory=list)


def exhaustive(scorer, pq, k: int) -> tuple[list[Hit], SearchStats]:
    t0 = time.perf_counter()
    costs = scorer.costs(pq)
    total = costs @ pq.weights
    ids = scorer.items["id"].to_numpy()
    order = np.lexsort((ids, total))[:k]
    hits = [Hit(int(r), costs[r], float(total[r])) for r in order]
    stats = SearchStats("exhaustive", items_scored=len(total), elapsed_ms=1000 * (time.perf_counter() - t0))
    return hits, stats


def best_first(scorer, tree, pq, k: int, greedy: bool = False) -> tuple[list[Hit], SearchStats]:
    t0 = time.perf_counter()
    stats = SearchStats("greedy" if greedy else "astar")
    w = pq.weights
    ids = scorer.items["id"].to_numpy()
    crit_pos = {c: i for i, c in enumerate(CRITERIA)}
    counter = itertools.count()

    def node_priority(node):
        lb = scorer.lower_bounds(pq, node.summary)
        decided = np.zeros(len(CRITERIA), dtype=bool)
        for attr, _ in node.path():
            decided[crit_pos[LEVEL_CRITERION[attr]]] = True
        g = float(lb[decided] @ w[decided])
        h = float(lb[~decided] @ w[~decided])
        return (h if greedy else g + h), g, h

    frontier = []
    f, _, _ = node_priority(tree.root)
    heapq.heappush(frontier, (f, _NODE, 0, next(counter), tree.root))
    hits: list[Hit] = []

    while frontier and len(hits) < k:
        stats.max_frontier = max(stats.max_frontier, len(frontier))
        _, kind, _, _, payload = heapq.heappop(frontier)
        if kind == _ITEM:
            hits.append(payload)
            continue
        node = payload
        stats.nodes_expanded += 1
        if node.is_leaf:
            rows = node.rows
            costs = scorer.costs(pq, rows)
            total = costs @ w
            stats.items_scored += len(rows)
            path = node.path()
            for r, c_row, c in zip(rows, costs, total):
                hit = Hit(int(r), c_row, float(c), path)
                # Every criterion is decided for an item, so its h is 0.
                prio = 0.0 if greedy else float(c)
                heapq.heappush(frontier, (prio, _ITEM, int(ids[r]), next(counter), hit))
        else:
            for child in node.children.values():
                f, _, _ = node_priority(child)
                stats.nodes_generated += 1
                heapq.heappush(frontier, (f, _NODE, 0, next(counter), child))

    stats.elapsed_ms = 1000 * (time.perf_counter() - t0)
    return hits, stats
