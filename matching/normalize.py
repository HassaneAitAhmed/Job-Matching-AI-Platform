"""Canonical vocabularies.

The two datasets were cleaned separately and disagree on spelling
(``Finance`` vs ``Banking & Finance``, ``Internship`` vs ``Stage``,
``Licence`` vs ``License``, ``Sétif`` vs ``Setif`` ...).  Every value that
enters the engine goes through one of the functions below so that both
sides speak the same language.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

# ---------------------------------------------------------------------------
# Sectors
# ---------------------------------------------------------------------------

_SECTOR_ALIASES = {
    "finance": "Banking & Finance",
    "banking": "Banking & Finance",
    "banking & finance": "Banking & Finance",
    "banking and finance": "Banking & Finance",
    "it": "Information Technology",
}

# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

CONTRACT_TYPES = {
    "CDI": "CDI (permanent)",
    "CDD": "CDD (fixed-term)",
    "Internship": "Internship (stage)",
    "Alternance": "Alternance (work-study)",
    "Freelance": "Freelance",
}

_CONTRACT_ALIASES = {
    "cdi": "CDI",
    "permanent": "CDI",
    "cdd": "CDD",
    "fixed-term": "CDD",
    "stage": "Internship",
    "internship": "Internship",
    "intern": "Internship",
    "alternance": "Alternance",
    "apprenticeship": "Alternance",
    "freelance": "Freelance",
}

# ---------------------------------------------------------------------------
# Education (value = years of study, as in the datasets' ``edu_value``)
# ---------------------------------------------------------------------------

EDUCATION_LEVELS = [
    (0, "No formal education"),
    (12, "Baccalaureate"),
    (15, "Licence"),
    (17, "Master"),
    (19, "Ingénieur d'État"),
    (20, "Doctorat"),
]
EDUCATION_VALUES = [v for v, _ in EDUCATION_LEVELS]

_EDUCATION_ALIASES = {
    "no formal education": 0,
    "none": 0,
    "bac": 12,
    "baccalaureate": 12,
    "baccalaureat": 12,
    "licence": 15,
    "license": 15,
    "bachelor": 15,
    "master": 17,
    "ingenieur d'etat": 19,
    "ingenieur": 19,
    "engineer": 19,
    "doctorat": 20,
    "doctorate": 20,
    "phd": 20,
}

# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------

# Towns that appear in the data but are not in the 48-wilaya distance matrix.
# They are mapped to the wilaya they belonged to before the 2019/2021 reforms,
# which is a reasonable proxy for distance.
_CITY_PARENT_WILAYA = {
    "djanet": "Illizi",
    "in salah": "Tamanrasset",
    "timimoun": "Adrar",
}


def fold(text: object) -> str:
    """Lowercase, strip accents, unify apostrophes and whitespace."""
    if text is None:
        return ""
    return _fold_str(str(text))


@lru_cache(maxsize=65536)
def _fold_str(s: str) -> str:
    if s.lower() == "nan":
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def canonical_sector(value: object) -> str | None:
    key = fold(value)
    if not key:
        return None
    if key in _SECTOR_ALIASES:
        return _SECTOR_ALIASES[key]
    # Keep the dataset's own capitalisation for everything else.
    return str(value).strip()


def canonical_contract(value: object) -> str | None:
    key = fold(value)
    if not key:
        return None
    if key in _CONTRACT_ALIASES:
        return _CONTRACT_ALIASES[key]
    raise ValueError(f"Unknown contract type: {value!r}")


def canonical_education(value: object) -> int | None:
    """Accept a level name or a numeric ``edu_value`` and return the canonical value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return None
        return _snap_education(float(value))
    key = fold(value)
    if not key:
        return None
    try:
        return _snap_education(float(key))
    except ValueError:
        pass
    if key in _EDUCATION_ALIASES:
        return _EDUCATION_ALIASES[key]
    raise ValueError(f"Unknown education level: {value!r}")


def _snap_education(v: float) -> int:
    """Map a number to the highest canonical level that does not exceed it."""
    if v < 0:
        raise ValueError(f"Education value cannot be negative: {v}")
    best = EDUCATION_VALUES[0]
    for level in EDUCATION_VALUES:
        if level <= v:
            best = level
    return best


def education_rank(value: float) -> int:
    """Ordinal position (0..5) of an education value."""
    rank = 0
    for i, level in enumerate(EDUCATION_VALUES):
        if level <= value:
            rank = i
    return rank


def education_label(value: float) -> str:
    return EDUCATION_LEVELS[education_rank(value)][1]


class CityResolver:
    """Map any spelling of a city onto a key of the distance matrix."""

    def __init__(self, matrix_cities):
        self.cities = sorted(matrix_cities)
        self._by_fold = {fold(c): c for c in self.cities}
        for alias, parent in _CITY_PARENT_WILAYA.items():
            if fold(parent) in self._by_fold:
                self._by_fold.setdefault(alias, self._by_fold[fold(parent)])

    def resolve(self, value: object) -> str | None:
        key = fold(value)
        if not key:
            return None
        if key in self._by_fold:
            return self._by_fold[key]
        # Tolerate hyphens / missing spaces ("Tizi-Ouzou", "SidiBelAbbes").
        squashed = re.sub(r"[\s\-']", "", key)
        for k, city in self._by_fold.items():
            if re.sub(r"[\s\-']", "", k) == squashed:
                return city
        return None


def split_skills(value: object) -> list[str]:
    """Split a comma separated skill string, dropping blanks; preserves display case."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set, frozenset)):
        parts = [str(v) for v in value]
    else:
        s = str(value)
        if s.lower() == "nan":
            return []
        parts = s.split(",")
    out, seen = [], set()
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip()
        if p and fold(p) not in seen:
            seen.add(fold(p))
            out.append(p)
    return out
