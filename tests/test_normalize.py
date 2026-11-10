import pytest

from matching.normalize import (
    CityResolver,
    canonical_contract,
    canonical_education,
    canonical_sector,
    education_rank,
    fold,
    split_skills,
)


def test_fold_strips_accents_and_apostrophes():
    assert fold("Béjaïa") == "bejaia"
    assert fold("M’sila") == "m'sila"
    assert fold("  Tizi   Ouzou ") == "tizi ouzou"
    assert fold(float("nan")) == ""


def test_sector_aliases_unify_datasets():
    assert canonical_sector("Finance") == canonical_sector("Banking & Finance") == "Banking & Finance"
    assert canonical_sector("Healthcare") == "Healthcare"
    assert canonical_sector("") is None


@pytest.mark.parametrize("raw,expected", [("Stage", "Internship"), ("Internship", "Internship"),
                                          ("cdi", "CDI"), ("Alternance", "Alternance")])
def test_contract_aliases(raw, expected):
    assert canonical_contract(raw) == expected


def test_unknown_contract_rejected():
    with pytest.raises(ValueError):
        canonical_contract("Volunteer")


@pytest.mark.parametrize("raw,expected", [
    ("License", 15), ("Licence", 15), ("Baccalaureate", 12), ("Ingénieur d'État", 19),
    ("Doctorat", 20), ("No Formal Education", 0), (17, 17), ("12", 12), (18, 17), (14, 12),
])
def test_education(raw, expected):
    assert canonical_education(raw) == expected


def test_education_rank_is_ordinal():
    assert [education_rank(v) for v in (0, 12, 15, 17, 19, 20)] == [0, 1, 2, 3, 4, 5]


def test_city_resolver():
    r = CityResolver(["Bejaia", "M'Sila", "Setif", "Illizi", "Tizi Ouzou"])
    assert r.resolve("Béjaïa") == "Bejaia"
    assert r.resolve("Bejaïa") == "Bejaia"
    assert r.resolve("M’sila") == "M'Sila"
    assert r.resolve("Sétif") == "Setif"
    assert r.resolve("Djanet") == "Illizi"
    assert r.resolve("Tizi-Ouzou") == "Tizi Ouzou"
    assert r.resolve("Atlantis") is None


def test_split_skills():
    assert split_skills("Python, SQL,,  python , Git") == ["Python", "SQL", "Git"]
    assert split_skills(float("nan")) == []


def test_every_dataset_value_is_resolved(matcher):
    assert matcher.dataset.issues == {"unresolved_cities": [], "unknown_contracts": [], "unknown_education": []}
    assert set(matcher.jobs["contract_type"]) == set(matcher.seekers["contract_type"])
    assert set(matcher.jobs["sector"]) == set(matcher.seekers["sector"])
