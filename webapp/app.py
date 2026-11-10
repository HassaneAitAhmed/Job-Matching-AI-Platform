"""
Job Matching AI Platform - Flask web application.

Serves the UI and a JSON API on top of ``matching.Matcher`` (A*, greedy
best-first, CSP, exhaustive baseline, and GA batch assignment).

Run locally:   python webapp/app.py            (http://127.0.0.1:5000)
Production:    gunicorn "webapp.app:create_app()"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # allow `python webapp/app.py` without installing the package
    sys.path.insert(0, str(ROOT))

from matching import JOB_TO_SEEKER, SEEKER_TO_JOB, Matcher  # noqa: E402
from matching.csp import Constraints  # noqa: E402
from matching.engine import ALGORITHMS  # noqa: E402

MAX_LIMIT = 50
MAX_OFFSET = 500
MAX_SKILLS = 30


class ValidationError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def _body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    return data


def _number(data, key, *, required=False, minimum=0.0, maximum=None, integer=False):
    raw = data.get(key)
    if raw is None or raw == "":
        if required:
            raise ValidationError(f"'{key}' is required")
        return None
    if isinstance(raw, bool):
        raise ValidationError(f"'{key}' must be a number")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"'{key}' must be a number") from None
    if value != value or value in (float("inf"), float("-inf")):
        raise ValidationError(f"'{key}' must be a finite number")
    if minimum is not None and value < minimum:
        raise ValidationError(f"'{key}' must be >= {minimum:g}")
    if maximum is not None and value > maximum:
        raise ValidationError(f"'{key}' must be <= {maximum:g}")
    return int(value) if integer else value


def _text(data, key):
    raw = data.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ValidationError(f"'{key}' must be a string")
    raw = raw.strip()
    return raw or None


def _skills(data):
    raw = data.get("skills", "")
    if isinstance(raw, list):
        parts = [str(s) for s in raw]
    elif isinstance(raw, str):
        parts = raw.split(",")
    else:
        raise ValidationError("'skills' must be a comma-separated string or a list")
    parts = [p.strip() for p in parts if p and p.strip()]
    if len(parts) > MAX_SKILLS:
        raise ValidationError(f"At most {MAX_SKILLS} skills are allowed")
    return parts


def _search_options(data):
    algorithm = (_text(data, "algorithm") or "astar").lower()
    if algorithm not in ALGORITHMS:
        raise ValidationError(f"'algorithm' must be one of {list(ALGORITHMS)}")
    limit = _number(data, "limit", minimum=1, maximum=MAX_LIMIT, integer=True) or 10
    offset = _number(data, "offset", minimum=0, maximum=MAX_OFFSET, integer=True) or 0
    max_km = _number(data, "max_distance_km", minimum=0, maximum=5000)
    constraints = Constraints(max_distance_km=max_km if max_km is not None else Constraints().max_distance_km)
    return algorithm, limit, offset, constraints


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(matcher: Matcher | None = None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    m = matcher or Matcher()
    app.config["MATCHER"] = m

    def run_search(direction, query_kwargs, data):
        algorithm, limit, offset, constraints = _search_options(data)
        try:
            query = m.make_query(direction, **query_kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from None
        result = m.search(query, algorithm=algorithm, k=limit, offset=offset, constraints=constraints)
        return jsonify({
            "direction": direction,
            "algorithm": algorithm,
            "offset": offset,
            "limit": limit,
            "matches": result.hits,
            "has_more": len(result.hits) == limit,
            "stats": result.stats.as_dict(),
        })

    @app.errorhandler(ValidationError)
    def _bad_request(exc):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(HTTPException)
    def _http_error(exc):
        if request.path.startswith("/api/"):
            return jsonify({"error": exc.description}), exc.code
        return exc

    @app.errorhandler(Exception)
    def _server_error(exc):  # pragma: no cover - safety net
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/stats")
    def stats():
        return jsonify(m.stats())

    @app.route("/api/options")
    def options():
        return jsonify(m.options())

    @app.route("/api/sectors")
    def sectors():
        return jsonify(m.options()["sectors"])

    @app.route("/api/cities")
    def cities():
        return jsonify(m.options()["cities"])

    @app.route("/api/skills")
    def skills():
        return jsonify(sorted(m.vocab.display, key=str.lower))

    @app.route("/api/match/seeker-to-jobs", methods=["POST"])
    def seeker_to_jobs():
        data = _body()
        return run_search(SEEKER_TO_JOB, {
            "skills": _skills(data),
            "years": _number(data, "experience", maximum=60),
            "education": _number(data, "education", maximum=30),
            "city": _text(data, "city"),
            "salary": _number(data, "salary", maximum=10_000_000),
            "sector": _text(data, "sector"),
            "contract_type": _text(data, "contract_type"),
        }, data)

    @app.route("/api/match/job-to-seekers", methods=["POST"])
    def job_to_seekers():
        data = _body()
        lo = _number(data, "experience_min", maximum=60)
        hi = _number(data, "experience_max", maximum=60)
        if lo is not None and hi is not None and hi < lo:
            raise ValidationError("'experience_max' must be >= 'experience_min'")
        if lo is None and hi is not None:
            lo = 0.0
        return run_search(JOB_TO_SEEKER, {
            "skills": _skills(data),
            "exp_lo": lo,
            "exp_hi": hi if hi is not None else lo,
            "education": _number(data, "education", maximum=30),
            "city": _text(data, "city"),
            "salary": _number(data, "salary", maximum=10_000_000),
            "sector": _text(data, "sector"),
            "contract_type": _text(data, "contract_type"),
        }, data)

    @app.route("/api/assign", methods=["POST"])
    def assign():
        data = _body()
        n_seekers = _number(data, "n_seekers", minimum=2, maximum=200, integer=True) or 40
        n_jobs = _number(data, "n_jobs", minimum=1, maximum=100, integer=True) or 15
        seed = _number(data, "seed", minimum=0, maximum=2**31 - 1, integer=True) or 0
        generations = _number(data, "generations", minimum=1, maximum=1000, integer=True) or 200
        try:
            out = m.assign(n_seekers, n_jobs, sector=_text(data, "sector"), seed=seed,
                           ga_params={"generations": generations})
        except ValueError as exc:
            raise ValidationError(str(exc)) from None
        return jsonify(out)

    return app


if __name__ == "__main__":
    print("Starting Job Matching AI Platform...")
    application = create_app()
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    application.run(debug=debug_mode, host=host, port=port)
