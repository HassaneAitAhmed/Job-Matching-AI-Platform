import pytest

from matching import JOB_TO_SEEKER, SEEKER_TO_JOB
from matching.csp import Constraints, MatchingCSP
from matching.normalize import education_rank


def _check_seeker_to_job(matcher, q, hits, c: Constraints):
    dist, idx = matcher.dataset.distances, matcher.dataset.city_index
    for h in hits:
        job = matcher.jobs.set_index("id").loc[h["id"]]
        if c.same_sector and q.sector:
            assert job.sector == q.sector
        if c.same_contract and q.contract_type:
            assert job.contract_type == q.contract_type
        if c.education and q.edu_value is not None:
            assert education_rank(job.edu_value) <= education_rank(q.edu_value)
        if c.max_distance_km is not None and q.city:
            assert dist[idx[q.city], idx[job.city]] <= c.max_distance_km
        if c.min_salary_ratio is not None and q.salary:
            assert job.salary >= c.min_salary_ratio * q.salary
        if c.experience_slack is not None and q.years is not None:
            assert job.exp_lo - c.experience_slack <= q.years <= job.exp_hi + c.experience_slack


def test_csp_solutions_satisfy_hard_constraints(matcher, queries):
    c = Constraints()
    scorer, tree = matcher.scorers[SEEKER_TO_JOB], matcher.trees[SEEKER_TO_JOB]
    for q in queries[SEEKER_TO_JOB]:
        hits, stats = MatchingCSP(scorer, tree, scorer.prepare(q), c).solve(k=50)
        described = [matcher._describe(SEEKER_TO_JOB, h, scorer.weights) for h in hits]
        _check_seeker_to_job(matcher, q, described, c)
        assert stats.extra["solutions"] >= len(hits)


def test_csp_counts_match_brute_force(matcher):
    """Pruning must not lose solutions: compare with filtering every job directly."""
    q = matcher.make_query(SEEKER_TO_JOB, sector="Information Technology", education=17, city="Algiers",
                           years=4, salary=60_000)
    c = Constraints()
    scorer, tree = matcher.scorers[SEEKER_TO_JOB], matcher.trees[SEEKER_TO_JOB]
    _, stats = MatchingCSP(scorer, tree, scorer.prepare(q), c).solve(k=1)
    j = matcher.jobs
    d = matcher.dataset.distances[matcher.dataset.city_index["Algiers"]][j.city_idx]
    brute = (
        (j.sector == q.sector)
        & (j.edu_value.map(education_rank) <= education_rank(17))
        & (d <= c.max_distance_km)
        & (j.salary >= c.min_salary_ratio * q.salary)
        & (j.exp_lo - c.experience_slack <= 4) & (4 <= j.exp_hi + c.experience_slack)
    ).sum()
    assert stats.extra["solutions"] == brute
    assert stats.extra["pruned_by_node_consistency"] > 0


def test_csp_relaxes_when_infeasible(matcher):
    q = matcher.make_query(SEEKER_TO_JOB, sector="Fisheries", contract_type="CDI", education=0,
                           city="Tamanrasset", years=40, salary=900_000)
    result = matcher.search(q, "csp", k=5)
    assert len(result.hits) == 5
    assert result.stats.extra["relaxed_constraints"]


def test_csp_job_to_seeker(matcher):
    q = matcher.query_from_job(5)
    result = matcher.search(q, "csp", k=5)
    assert all(h["type"] == "seeker" for h in result.hits)
    if not result.stats.extra["relaxed_constraints"]:
        assert all(h["sector"] == q.sector for h in result.hits)


@pytest.mark.parametrize("direction", [SEEKER_TO_JOB, JOB_TO_SEEKER])
def test_csp_ranked_by_score(matcher, queries, direction):
    for q in queries[direction][:10]:
        scores = [h["match_score"] for h in matcher.search(q, "csp", k=10).hits]
        assert scores == sorted(scores, reverse=True)
