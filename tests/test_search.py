import numpy as np
import pytest

from matching import JOB_TO_SEEKER, SEEKER_TO_JOB

DIRS = (SEEKER_TO_JOB, JOB_TO_SEEKER)
K = 10


@pytest.mark.parametrize("direction", DIRS)
def test_astar_matches_exhaustive(matcher, queries, direction):
    for q in queries[direction]:
        exact = matcher.search(q, "exhaustive", k=K)
        astar = matcher.search(q, "astar", k=K)
        np.testing.assert_allclose(
            [h["match_score"] for h in astar.hits], [h["match_score"] for h in exact.hits], atol=1e-6
        )


@pytest.mark.parametrize("direction", DIRS)
def test_astar_scores_fewer_items_than_exhaustive(matcher, queries, direction):
    n_items = len(matcher.scorers[direction].items)
    scored = [matcher.search(q, "astar", k=K).stats.items_scored for q in queries[direction]]
    assert np.median(scored) < n_items / 4


@pytest.mark.parametrize("direction", DIRS)
def test_greedy_is_valid_but_not_better_than_optimal(matcher, queries, direction):
    for q in queries[direction][:15]:
        best = matcher.search(q, "exhaustive", k=K).hits
        greedy = matcher.search(q, "greedy", k=K).hits
        assert len(greedy) == K
        assert greedy[0]["match_score"] <= best[0]["match_score"] + 1e-9
        assert len({h["id"] for h in greedy}) == K


def test_seeker_search_returns_jobs_not_seekers(matcher):
    """Regression: the original notebook returned seeker ids for seeker->job searches."""
    q = matcher.make_query(SEEKER_TO_JOB, sector="Information Technology", contract_type="CDI",
                           education=12, city="Algiers", years=10, salary=50_000, skills=["Python", "Java"])
    job_ids = set(matcher.jobs["id"])
    for alg in ("astar", "greedy", "csp", "exhaustive"):
        hits = matcher.search(q, alg, k=5).hits
        assert hits and all(h["type"] == "job" and h["id"] in job_ids for h in hits), alg


def test_job_search_returns_seekers(matcher):
    q = matcher.query_from_job(1)
    seeker_ids = set(matcher.seekers["id"])
    hits = matcher.search(q, "astar", k=5).hits
    assert all(h["type"] == "seeker" and h["id"] in seeker_ids for h in hits)


def test_pagination_is_consistent(matcher, queries):
    q = queries[SEEKER_TO_JOB][0]
    full = matcher.search(q, "astar", k=20).hits
    page2 = matcher.search(q, "astar", k=10, offset=10).hits
    np.testing.assert_allclose([h["match_score"] for h in page2], [h["match_score"] for h in full[10:]])


def test_planted_match_is_ranked_first(matcher):
    """A seeker built to fit job X exactly should score 100 against X."""
    job = matcher.jobs[matcher.jobs["skills_listed"]].iloc[0]
    q = matcher.make_query(SEEKER_TO_JOB, sector=job.sector, contract_type=job.contract_type,
                           education=int(job.edu_value), city=job.city, years=float(job.exp_lo),
                           salary=float(job.salary), skills=list(job.skills))
    hits = matcher.search(q, "astar", k=5).hits
    assert hits[0]["match_score"] == pytest.approx(100.0)
    assert int(job.id) in {h["id"] for h in hits if h["match_score"] == pytest.approx(100.0)}


def test_breakdown_is_consistent_with_score(matcher, queries):
    for q in queries[JOB_TO_SEEKER][:5]:
        for h in matcher.search(q, "astar", k=3).hits:
            weighted = sum(v["score"] * v["weight"] for v in h["breakdown"].values()) / 100
            assert weighted == pytest.approx(h["match_score"], abs=0.5)
