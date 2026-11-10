"""Hierarchical feature-based clustering of items (jobs or seekers).

Items are grouped level by level on ``HIERARCHY``; every node stores a
``Summary`` of the items below it (value sets and min/max ranges) from which
admissible cost bounds are derived.  Leaves hold item row indices.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HIERARCHY = ("sector", "contract_type", "edu_value", "city")
# Which scoring criterion each tree level decides.
LEVEL_CRITERION = {"sector": "sector", "contract_type": "contract_type", "edu_value": "education", "city": "location"}


@dataclass
class Summary:
    n: int
    sectors: frozenset
    contracts: frozenset
    edu_min: float
    edu_max: float
    city_idxs: np.ndarray
    lo_min: float          # min experience requirement (jobs) / min years (seekers)
    hi_max: float          # max experience requirement (jobs) / max years (seekers)
    salary_min: float
    salary_max: float
    skill_union: frozenset
    skill_min_count: int   # smallest non-empty skill list
    any_listed: bool
    any_unlisted: bool


class Node:
    __slots__ = ("level", "attr", "value", "children", "rows", "summary", "parent")

    def __init__(self, level, attr, value, rows, summary, parent=None):
        self.level = level        # depth; root = 0
        self.attr = attr          # attribute decided to reach this node (None at root)
        self.value = value
        self.children: dict = {}
        self.rows = rows          # np.ndarray of item row indices
        self.summary = summary
        self.parent = parent

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def path(self):
        out, node = [], self
        while node is not None and node.attr is not None:
            out.append((node.attr, node.value))
            node = node.parent
        return out[::-1]


class ClusterTree:
    def __init__(self, items, entity: str, hierarchy=HIERARCHY):
        self.entity = entity              # "job" or "seeker" -- what the ids refer to
        self.hierarchy = tuple(hierarchy)
        self.items = items
        self._sector = items["sector"].to_numpy(dtype=object)
        self._contract = items["contract_type"].to_numpy(dtype=object)
        self._edu = items["edu_value"].to_numpy(dtype=float)
        self._city = items["city_idx"].to_numpy(dtype=int)
        if "exp_lo" in items:
            self._lo = items["exp_lo"].to_numpy(dtype=float)
            self._hi = items["exp_hi"].to_numpy(dtype=float)
        else:
            self._lo = self._hi = items["years"].to_numpy(dtype=float)
        self._salary = items["salary"].to_numpy(dtype=float)
        self._skills = list(items["skill_ids"])
        self._columns = {a: items[a].to_numpy(dtype=object) for a in self.hierarchy}
        self.n_nodes = 0
        self.root = self._build(np.arange(len(items)), 0, None, None, None)

    def summarize(self, rows: np.ndarray) -> Summary:
        union: set = set()
        min_count = 0
        any_listed = any_unlisted = False
        for r in rows:
            s = self._skills[r]
            if s:
                any_listed = True
                union |= s
                min_count = len(s) if min_count == 0 else min(min_count, len(s))
            else:
                any_unlisted = True
        return Summary(
            n=len(rows),
            sectors=frozenset(self._sector[rows]),
            contracts=frozenset(self._contract[rows]),
            edu_min=float(self._edu[rows].min()),
            edu_max=float(self._edu[rows].max()),
            city_idxs=np.unique(self._city[rows]),
            lo_min=float(self._lo[rows].min()),
            hi_max=float(self._hi[rows].max()),
            salary_min=float(self._salary[rows].min()),
            salary_max=float(self._salary[rows].max()),
            skill_union=frozenset(union),
            skill_min_count=min_count,
            any_listed=any_listed,
            any_unlisted=any_unlisted,
        )

    def _build(self, rows, level, attr, value, parent):
        node = Node(level, attr, value, rows, self.summarize(rows), parent)
        self.n_nodes += 1
        if level < len(self.hierarchy):
            nxt = self.hierarchy[level]
            col = self._columns[nxt][rows]
            for v in sorted(set(col), key=str):
                sub = rows[col == v]
                node.children[v] = self._build(sub, level + 1, nxt, v, node)
        return node

    def leaves(self):
        stack = [self.root]
        while stack:
            n = stack.pop()
            if n.is_leaf:
                yield n
            else:
                stack.extend(n.children.values())

    def to_dict(self, node: Node | None = None) -> dict:
        """JSON-serialisable view (for inspection / the notebook)."""
        node = node or self.root
        s = node.summary
        d = {
            "summary": {
                "n": s.n,
                "sectors": sorted(map(str, s.sectors)),
                "contracts": sorted(map(str, s.contracts)),
                "edu_range": [s.edu_min, s.edu_max],
                "experience_range": [s.lo_min, s.hi_max],
                "salary_range": [s.salary_min, s.salary_max],
                "n_skills": len(s.skill_union),
            }
        }
        if node.is_leaf:
            d[f"{self.entity}_ids"] = [int(i) for i in self.items["id"].to_numpy()[node.rows]]
        else:
            d["split_on"] = self.hierarchy[node.level]
            d["children"] = {str(k): self.to_dict(c) for k, c in node.children.items()}
        if node is self.root:
            d["entity"] = self.entity
            d["hierarchy"] = list(self.hierarchy)
        return d
