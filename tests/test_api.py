import pytest

from webapp.app import create_app


@pytest.fixture(scope="module")
def client(matcher):
    app = create_app(matcher)
    app.testing = True
    return app.test_client()


SEEKER = {"skills": "Python, SQL", "experience": 3, "education": 15, "city": "Algiers", "salary": 60000}
JOB = {"skills": "Risk Management", "experience_min": 2, "experience_max": 5, "education": 15,
       "city": "Oran", "salary": 80000, "sector": "Finance"}


def test_frontend_is_served(matcher, tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id=root>Job Matching</div>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    c = create_app(matcher, frontend_dist=tmp_path).test_client()
    assert c.get("/").data == b"<div id=root>Job Matching</div>"
    assert c.get("/assets/app.js").data == b"console.log(1)"
    assert c.get("/some/client/route").data == b"<div id=root>Job Matching</div>"  # SPA fallback
    assert b"[project]" not in c.get("/../pyproject.toml").data  # no path traversal out of dist


def test_missing_frontend_build_explains_how_to_build(matcher, tmp_path):
    r = create_app(matcher, frontend_dist=tmp_path / "nope").test_client().get("/")
    assert r.status_code == 503 and b"npm run build" in r.data


@pytest.mark.parametrize("path", ["/api/stats", "/api/options", "/api/sectors", "/api/cities",
                                  "/api/skills", "/api/health"])
def test_metadata_endpoints(client, path):
    r = client.get(path)
    assert r.status_code == 200 and r.is_json


def test_skills_endpoint_not_empty(client):
    assert len(client.get("/api/skills").json) > 500


def test_options_use_canonical_values(client):
    opts = client.get("/api/options").json
    assert [e["value"] for e in opts["education_levels"]] == [0, 12, 15, 17, 19, 20]
    assert {c["value"] for c in opts["contract_types"]} == {"CDI", "CDD", "Internship", "Alternance", "Freelance"}
    assert "Finance" not in opts["sectors"] and "Banking & Finance" in opts["sectors"]
    for weights in opts["weights"].values():
        assert sum(weights.values()) == pytest.approx(100, abs=0.5)


@pytest.mark.parametrize("algorithm", ["astar", "greedy", "csp", "exhaustive"])
def test_seeker_search_without_sector_works(client, algorithm):
    """Regression: this request used to return HTTP 500."""
    r = client.post("/api/match/seeker-to-jobs", json={**SEEKER, "algorithm": algorithm})
    assert r.status_code == 200, r.json
    body = r.json
    assert body["algorithm"] == algorithm and len(body["matches"]) == 10
    m = body["matches"][0]
    assert isinstance(m["matched_skills"], list)
    assert m["type"] == "job" and set(m["breakdown"]) == {
        "sector", "contract_type", "education", "location", "experience", "salary", "skills"}


def test_finance_employer_search_finds_candidates(client):
    """Regression: 'Finance' (jobs) vs 'Banking & Finance' (seekers) used to return nothing."""
    r = client.post("/api/match/job-to-seekers", json=JOB)
    assert r.status_code == 200
    # A* treats sector as a weighted criterion, so other sectors may appear ...
    assert sum(m["sector"] == "Banking & Finance" for m in r.json["matches"]) >= 5
    # ... while the CSP enforces it as a hard constraint.
    r = client.post("/api/match/job-to-seekers", json={**JOB, "algorithm": "csp"})
    assert r.json["stats"]["relaxed_constraints"] == []
    assert all(m["sector"] == "Banking & Finance" for m in r.json["matches"])


def test_employer_search_considers_all_candidates(client):
    """Regression: only the first 100 seekers were ever scored."""
    r = client.post("/api/match/job-to-seekers", json={**JOB, "algorithm": "exhaustive"})
    assert r.json["stats"]["items_scored"] == 8124
    assert any(m["id"] > 100 for m in r.json["matches"])


def test_pagination(client):
    p1 = client.post("/api/match/seeker-to-jobs", json={**SEEKER, "limit": 5}).json
    p2 = client.post("/api/match/seeker-to-jobs", json={**SEEKER, "limit": 5, "offset": 5}).json
    both = client.post("/api/match/seeker-to-jobs", json={**SEEKER, "limit": 10}).json
    assert [m["match_score"] for m in p1["matches"] + p2["matches"]] == [m["match_score"] for m in both["matches"]]


@pytest.mark.parametrize("payload,fragment", [
    ({**SEEKER, "salary": "abc"}, "salary"),
    ({**SEEKER, "experience": -1}, "experience"),
    ({**SEEKER, "city": "Atlantis"}, "city"),
    ({**SEEKER, "contract_type": "Volunteer"}, "contract"),
    ({**SEEKER, "education": "Wizard"}, "education"),
    ({**SEEKER, "algorithm": "quantum"}, "algorithm"),
    ({**SEEKER, "limit": 0}, "limit"),
    ({**SEEKER, "skills": 42}, "skills"),
])
def test_validation_errors_are_400(client, payload, fragment):
    r = client.post("/api/match/seeker-to-jobs", json=payload)
    assert r.status_code == 400
    assert fragment in r.json["error"].lower()


def test_non_json_body_is_400(client):
    r = client.post("/api/match/seeker-to-jobs", data="x", content_type="text/plain")
    assert r.status_code == 400


def test_experience_range_validated(client):
    r = client.post("/api/match/job-to-seekers", json={**JOB, "experience_min": 5, "experience_max": 2})
    assert r.status_code == 400


def test_unknown_api_route_is_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.is_json


def test_assign_endpoint(client):
    r = client.post("/api/assign", json={"n_seekers": 15, "n_jobs": 6, "generations": 30})
    assert r.status_code == 200
    methods = [x["method"] for x in r.json["results"]]
    assert methods == ["optimal (Hungarian)", "greedy", "genetic algorithm"]


def test_assign_validation(client):
    assert client.post("/api/assign", json={"n_seekers": 10_000}).status_code == 400
