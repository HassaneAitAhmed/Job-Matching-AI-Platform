import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from matching import JOB_TO_SEEKER, SEEKER_TO_JOB, Matcher, Query  # noqa: E402


@pytest.fixture(scope="session")
def matcher():
    return Matcher()


def random_queries(matcher, direction, n, seed=0):
    """Queries built from dataset rows, with random fields dropped ("no preference")."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        if direction == SEEKER_TO_JOB:
            sid = int(rng.choice(matcher.seekers["id"].tolist()))
            q = matcher.query_from_seeker(sid)
        else:
            jid = int(rng.choice(matcher.jobs["id"].tolist()))
            q = matcher.query_from_job(jid)
        fields = q.__dict__.copy()
        for f in ("sector", "contract_type", "edu_value", "city", "salary"):
            if rng.random() < 0.3:
                fields[f] = None
        if rng.random() < 0.2:
            fields["skills"] = ()
        out.append(Query(**fields))
    return out


@pytest.fixture(scope="session")
def queries(matcher):
    return {
        SEEKER_TO_JOB: random_queries(matcher, SEEKER_TO_JOB, 40, seed=1),
        JOB_TO_SEEKER: random_queries(matcher, JOB_TO_SEEKER, 40, seed=2),
    }
