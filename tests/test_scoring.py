import numpy as np
import pytest

from matching import JOB_TO_SEEKER, SEEKER_TO_JOB
from matching.scoring import (
    WEIGHTS,
    education_cost,
    experience_cost,
    location_cost,
    salary_cost,
)

DIRS = (SEEKER_TO_JOB, JOB_TO_SEEKER)


def test_weights_sum_to_one():
    for w in WEIGHTS.values():
        assert w.sum() == pytest.approx(1.0)


def test_scalar_costs_are_bounded_and_monotone():
    assert education_cost(15, 15) == 0 and education_cost(20, 12) == 0
    assert education_cost(12, 15) < education_cost(12, 17) <= 1
    assert experience_cost(3, 2, 5) == 0
    assert experience_cost(1, 2, 5) < experience_cost(0, 2, 5) <= 1
    assert 0 < experience_cost(8, 2, 5) < experience_cost(30, 2, 5) <= 0.6
    assert salary_cost(50_000, 60_000) == 0
    assert salary_cost(50_000, 45_000) < salary_cost(50_000, 40_000) <= 1
    assert salary_cost(50_000, 10_000) == 1
    assert location_cost(0) == 0 and location_cost(100) < location_cost(500) < 1
    assert location_cost(float("inf")) == 1


@pytest.mark.parametrize("direction", DIRS)
def test_exact_costs_in_unit_interval(matcher, queries, direction):
    scorer = matcher.scorers[direction]
    for q in queries[direction][:10]:
        c = scorer.costs(scorer.prepare(q))
        assert np.isfinite(c).all()
        assert (c >= 0).all() and (c <= 1).all()


@pytest.mark.parametrize("direction", DIRS)
def test_singleton_bound_equals_exact_cost(matcher, queries, direction):
    scorer, tree = matcher.scorers[direction], matcher.trees[direction]
    rng = np.random.default_rng(0)
    for q in queries[direction][:15]:
        pq = scorer.prepare(q)
        rows = rng.choice(len(scorer.items), size=25, replace=False)
        exact = scorer.costs(pq, rows)
        for r, e in zip(rows, exact):
            lb = scorer.lower_bounds(pq, tree.summarize(np.array([r])))
            np.testing.assert_allclose(lb, e, atol=1e-9)


@pytest.mark.parametrize("direction", DIRS)
def test_bounds_never_overestimate(matcher, queries, direction):
    """Admissibility: for every node, bound <= exact cost of every item below it."""
    scorer, tree = matcher.scorers[direction], matcher.trees[direction]
    nodes = []
    stack = [tree.root]
    while stack:
        n = stack.pop()
        nodes.append(n)
        stack.extend(n.children.values())
    rng = np.random.default_rng(1)
    sample = [nodes[i] for i in rng.choice(len(nodes), size=min(150, len(nodes)), replace=False)] + [tree.root]
    for q in queries[direction][:8]:
        pq = scorer.prepare(q)
        all_costs = scorer.costs(pq)
        for node in sample:
            lb = scorer.lower_bounds(pq, node.summary)
            item_min = all_costs[node.rows].min(axis=0)
            assert (lb <= item_min + 1e-9).all(), (node.path(), lb, item_min)


def test_soft_skill_matching(matcher):
    v = matcher.vocab
    names = lambda ids: {v.display[i].lower() for i in ids}  # noqa: E731
    assert "supply chain management" in names(v.related("Supply Chain"))
    assert "scada systems" in names(v.related("SCADA"))
    assert "objective-c" not in names(v.related("C"))
    assert "retail buying" not in names(v.related("Media Buying"))
