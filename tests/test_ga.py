import itertools

import numpy as np
import pytest

from matching.ga import AssignmentGA, greedy_assignment, is_valid, optimal_assignment, total_score


def brute_force(S, cap):
    n, m = S.shape
    best = 0.0
    for genes in itertools.product(range(-1, m), repeat=n):
        g = np.array(genes)
        if is_valid(g, cap):
            best = max(best, total_score(S, g))
    return best


@pytest.mark.parametrize("seed", range(5))
def test_optimal_is_truly_optimal_on_small_instances(seed):
    rng = np.random.default_rng(seed)
    S = rng.random((5, 3))
    cap = rng.integers(1, 3, size=3)
    opt = optimal_assignment(S, cap)
    assert is_valid(opt.genes, cap)
    assert opt.total == pytest.approx(brute_force(S, cap))


@pytest.mark.parametrize("seed", range(3))
def test_ga_and_greedy_are_valid_and_bounded_by_optimal(seed):
    rng = np.random.default_rng(seed)
    S = rng.random((30, 10))
    cap = rng.integers(1, 4, size=10)
    opt = optimal_assignment(S, cap)
    greedy = greedy_assignment(S, cap)
    ga = AssignmentGA(S, cap, generations=60, seed=seed).run()
    for res in (greedy, ga):
        assert is_valid(res.genes, cap)
        assert res.total <= opt.total + 1e-9
    assert ga.total >= 0.8 * opt.total
    assert ga.history == sorted(ga.history)  # elitism => best never decreases


def test_matcher_assign(matcher):
    out = matcher.assign(n_seekers=20, n_jobs=8, seed=3, ga_params={"generations": 40})
    methods = {r["method"]: r for r in out["results"]}
    assert methods["optimal (Hungarian)"]["pct_of_optimal"] == 100.0
    assert methods["genetic algorithm"]["pct_of_optimal"] <= 100.0
    assert methods["greedy"]["pct_of_optimal"] <= 100.0
    seeker_ids, job_ids = set(matcher.seekers["id"]), set(matcher.jobs["id"])
    for p in out["optimal_pairs"]:
        assert p["seeker_id"] in seeker_ids and p["job_id"] in job_ids
