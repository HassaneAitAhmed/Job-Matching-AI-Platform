"""Loading and cleaning the job and seeker datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .normalize import (
    CityResolver,
    canonical_contract,
    canonical_education,
    canonical_sector,
    fold,
    split_skills,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Dataset:
    jobs: pd.DataFrame
    seekers: pd.DataFrame
    cities: list[str]
    distances: np.ndarray          # km, shape (n_cities, n_cities)
    city_index: dict[str, int]
    resolver: CityResolver
    issues: dict


def load_distances(path: Path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    cities = sorted(raw)
    index = {c: i for i, c in enumerate(cities)}
    n = len(cities)
    dist = np.full((n, n), np.inf)
    for a, row in raw.items():
        for b, km in row.items():
            if b in index:
                dist[index[a], index[b]] = float(km)
    # Fill any one-directional entries and the diagonal.
    dist = np.minimum(dist, dist.T)
    np.fill_diagonal(dist, 0.0)
    return cities, index, dist


def _int_or(value, default):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def load_dataset(data_dir: Path | str = DATA_DIR) -> Dataset:
    data_dir = Path(data_dir)
    cities, city_index, dist = load_distances(data_dir / "algeria_distances.json")
    resolver = CityResolver(cities)
    issues: dict = {"unresolved_cities": set(), "unknown_contracts": set(), "unknown_education": set()}

    def resolve_city(raw):
        c = resolver.resolve(raw)
        if c is None and fold(raw):
            issues["unresolved_cities"].add(str(raw))
        return c

    def contract(raw):
        try:
            return canonical_contract(raw)
        except ValueError:
            issues["unknown_contracts"].add(str(raw))
            return None

    def education(raw_value, raw_label):
        for v in (raw_value, raw_label):
            try:
                e = canonical_education(v)
                if e is not None:
                    return e
            except ValueError:
                continue
        issues["unknown_education"].add(f"{raw_label!r}/{raw_value!r}")
        return 0

    # ---- jobs -----------------------------------------------------------
    raw_jobs = pd.read_csv(data_dir / "jobs.csv")
    jobs = pd.DataFrame({
        "id": raw_jobs["job_Id"].astype(int),
        "title": raw_jobs["job title"].fillna("Untitled").astype(str),
        "department": raw_jobs["department"].fillna("").astype(str),
        "sector": raw_jobs["sector"].map(canonical_sector),
        "contract_type": raw_jobs["type of contract"].map(contract),
        "edu_value": [education(v, l) for v, l in zip(raw_jobs["edu_value"], raw_jobs["education requirement"])],
        "city_raw": raw_jobs["job location"].fillna("").astype(str),
        "city": raw_jobs["job location"].map(resolve_city),
        "exp_lo": [_int_or(v, 0) for v in raw_jobs["experience_min_req"]],
        "exp_hi": [_int_or(v, 0) for v in raw_jobs["experience_max_req"]],
        "salary": pd.to_numeric(raw_jobs["salary"], errors="coerce").fillna(0).astype(float),
        "posts": [max(1, _int_or(v, 1)) for v in raw_jobs["available posts"]],
        "skills": raw_jobs["technical_skills"].map(split_skills),
    })
    jobs["exp_hi"] = np.maximum(jobs["exp_lo"], jobs["exp_hi"])
    jobs["skills_listed"] = jobs["skills"].map(bool)

    # ---- seekers ----------------------------------------------------------
    raw_emp = pd.read_csv(data_dir / "emplo.csv")
    seekers = pd.DataFrame({
        "id": raw_emp["employee_Id"].astype(int),
        "gender": raw_emp["gender"].fillna("").astype(str),
        "age": [_int_or(v, 0) for v in raw_emp["age"]],
        "department": raw_emp["department"].fillna("").astype(str),
        "sector": raw_emp["sector"].map(canonical_sector),
        "contract_type": raw_emp["contract_type"].map(contract),
        "edu_value": [education(v, l) for v, l in zip(raw_emp["edu_value"], raw_emp["highest_education"])],
        "city_raw": raw_emp["city"].fillna("").astype(str),
        "city": raw_emp["city"].map(resolve_city),
        "years": [_int_or(v, 0) for v in raw_emp["years_experience"]],
        "salary": pd.to_numeric(raw_emp["salary"], errors="coerce").fillna(0).astype(float),
        "skills": raw_emp["technical_skills"].map(split_skills),
        "languages": raw_emp["language_proficiency"].map(split_skills),
    })
    seekers["skills_listed"] = seekers["skills"].map(bool)

    for df in (jobs, seekers):
        df["sector"] = df["sector"].fillna("Unknown")
        df["contract_type"] = df["contract_type"].fillna("Unknown")
        df["city_idx"] = [city_index.get(c, -1) if c else -1 for c in df["city"]]
        df.reset_index(drop=True, inplace=True)

    issues = {k: sorted(v) for k, v in issues.items()}
    return Dataset(jobs, seekers, cities, dist, city_index, resolver, issues)


def data_quality_report(data_dir: Path | str = DATA_DIR) -> str:
    """Plain-text report of known problems in the raw CSVs (see docs/DATA.md)."""
    data_dir = Path(data_dir)
    j = pd.read_csv(data_dir / "jobs.csv")
    e = pd.read_csv(data_dir / "emplo.csv")
    with open(data_dir / "algeria_distances.json", encoding="utf-8") as f:
        matrix = set(json.load(f))

    lines = ["# Data quality report", ""]
    lines.append(f"- Jobs: {len(j)} rows; seekers: {len(e)} rows; distance matrix: {len(matrix)} cities.")
    missing = j["technical_skills"].isna()
    lines.append(
        f"- Jobs with no technical skills: {int(missing.sum())} ({missing.mean():.0%}). "
        f"They cover whole sectors ({', '.join(sorted(j.loc[missing, 'sector'].unique()))}), "
        "so skills cannot be imputed from similar postings. The engine scores them as a weak skills match and the UI flags them."
    )
    sj = {s.strip() for x in j["technical_skills"].dropna() for s in x.split(",")}
    se = {s.strip() for x in e["technical_skills"].dropna() for s in x.split(",")}
    lines.append(f"- Distinct skill names: jobs {len(sj)}, seekers {len(se)}, shared exactly: {len(sj & se)}.")
    lines.append(
        f"- Sector labels only in jobs: {sorted(set(j.sector) - set(e.sector))}; "
        f"only in seekers: {sorted(set(e.sector) - set(j.sector))}."
    )
    lines.append(
        f"- Contract labels jobs: {sorted(j['type of contract'].unique())}; "
        f"seekers: {sorted(e['contract_type'].unique())}."
    )
    lines.append(
        f"- Education labels jobs: {sorted(j['education requirement'].unique())}; "
        f"seekers: {sorted(e['highest_education'].unique())}."
    )
    cities = set(j["job location"].dropna()) | set(e["city"].dropna())
    lines.append(f"- City spellings not literally in the distance matrix: {sorted(cities - matrix)}.")
    stage_senior = int(((e.contract_type == "Stage") & (e.years_experience > 10)).sum())
    lines.append(f"- Seekers looking for an internship (Stage) with >10 years of experience: {stage_senior}.")
    lines.append(f"- Internship seekers (Stage) holding a Doctorat: "
                 f"{int(((e.contract_type == 'Stage') & (e.highest_education == 'Doctorat')).sum())}.")
    mismatch = (j["job title"] != j["department"]).mean()
    lines.append(f"- Jobs whose department differs from their title: {mismatch:.0%} (e.g. row 2: "
                 f"{j.loc[1, 'job title']!r} in department {j.loc[1, 'department']!r}).")
    lines.append("")
    lines.append(
        "These patterns (random-looking title/department/skill combinations, implausible "
        "experience/contract pairs) suggest the datasets were synthetically generated or heavily "
        "augmented. Scores produced on them demonstrate the algorithms; they are not evidence of "
        "real-world matching quality."
    )
    return "\n".join(lines)
