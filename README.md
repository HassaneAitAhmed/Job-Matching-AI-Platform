# 🎯 Job Matching AI Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Tests](https://img.shields.io/badge/tests-pytest-green.svg)

**Job matching with A\* search, greedy best-first search, constraint satisfaction and a genetic algorithm**

</div>

---

## 📋 Table of Contents

- [Abstract](#-abstract)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [How Matching Works](#-how-matching-works)
- [Algorithms](#-algorithms)
- [Results](#-results)
- [Data](#-data)
- [Usage](#-usage)
- [Development](#-development)
- [Future Work](#-future-work)

---

## 📄 Abstract

The platform matches in both directions:
- **Job seekers** get the job postings that best fit their skills, experience, education, location and salary expectations.
- **Employers** get the candidates who best fit a posting.

It can also **assign a batch** of seekers to job posts, respecting how many posts each job has open.

The Algerian job market struggles to connect qualified candidates with suitable openings. Search is inefficient, skill descriptions aren't standardised, and opportunities are unevenly spread across regions. This project models matching as a search and optimisation problem. It compares classical AI techniques on that problem and measures each one against an exact baseline.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt     # Python 3.11+
python webapp/app.py                # http://127.0.0.1:5000
```

Or with Docker (gunicorn, one worker, four threads):

```bash
docker build -t job-matching . && docker run -p 8000:8000 job-matching   # http://localhost:8000
```

`python webapp/app.py` reads `HOST` (default `127.0.0.1`; set `0.0.0.0` to expose it), `PORT` (default `5000`) and `FLASK_DEBUG` (default `false`; development only). Start-up loads the data and builds the cluster trees once (about 3 s, about 150 MB).

---

## 📁 Project Structure

```
Job-Matching-AI-Platform/
├── matching/                 # The engine (one implementation shared by everything below)
│   ├── normalize.py          #   canonical sectors, contracts, education levels, city names
│   ├── data.py               #   loading/cleaning the CSVs, data quality report
│   ├── skills.py             #   skill vocabulary + TF-IDF soft matching
│   ├── scoring.py            #   cost model: exact costs and admissible cluster bounds
│   ├── tree.py               #   hierarchical cluster tree
│   ├── search.py             #   A*, greedy best-first, exhaustive baseline
│   ├── csp.py                #   constraint satisfaction with forward checking + relaxation
│   ├── ga.py                 #   batch assignment: GA, greedy, optimal (Hungarian)
│   ├── engine.py             #   Matcher: the public API
│   ├── evaluation.py         #   benchmarks and labelled-set metrics
│   └── __main__.py           #   CLI: python -m matching ...
├── webapp/                   # Flask UI + JSON API on top of matching.Matcher
├── notebooks/demo.ipynb      # Walkthrough of every algorithm (executed, with outputs)
├── tests/                    # pytest suite (correctness, optimality, API, regressions)
├── docs/
│   ├── BENCHMARKS.md         #   measured results (generated)
│   ├── DATA.md               #   data quality report (generated)
│   ├── LABELING.md           #   human relevance labelling workflow
│   └── CHANGELOG.md          #   v1 problems and how v2 fixed them
├── data/                     # jobs.csv, emplo.csv, algeria_distances.json
├── report.pdf                # Original project report (problem formulation and analysis)
├── Dockerfile, .github/workflows/ci.yml, pyproject.toml, requirements*.txt
```

---

## 🧮 How Matching Works

A match between a query and an item has a **cost** between 0 and 1. The score shown is `100 × (1 − cost)`. The cost is a weighted sum of seven criteria, each also between 0 and 1:

| Criterion | Cost | Seeker weight | Employer weight |
|---|---|---|---|
| Skills | 1 − share of the job's required skills that are covered (TF-IDF soft match) | 25% | 18.2% |
| Location | 1 − exp(−km / 250) using the 48-wilaya road-distance matrix | 15% | 18.2% |
| Sector | 0 if same sector, otherwise 1 | 14% | 13.6% |
| Contract type | 0 if same contract type, otherwise 1 | 12% | 9.1% |
| Education | 0.4 per level below the requirement (max 1) | 12% | 10.9% |
| Salary | linear from 0 (offer ≥ expectation) to 1 (offer 30% below) | 12% | 13.6% |
| Experience | proportional shortfall below the range; mild penalty above it (max 0.6) | 10% | 16.4% |

Fields left blank mean "no preference" and cost 0. A job that lists no skills (58% of postings) scores as a weak skills match. Every result returns a per-criterion breakdown, which the UI shows as bars.

Before scoring, both datasets are normalised into one vocabulary (`matching/normalize.py`):
- **Sectors:** `Finance` and `Banking & Finance` become one sector.
- **Contracts:** `Stage` and `Internship` become one contract type.
- **Education:** `Licence` and `License` become one level.
- **Cities:** accented spellings (`Sétif`, `Béjaïa`) resolve to the distance-matrix names. Djanet, In Salah and Timimoun map to their former parent wilaya.

---

## 🧠 Algorithms

### Cluster tree
Items are grouped by `sector → contract type → education → city` (1,239 nodes for jobs, 6,568 for seekers). Each node stores a summary of its items: value sets, min/max education, experience and salary, and the union of their skills.

### A* search (`search.py`)
- **States:** tree nodes and individual items (the goals).
- **g(n):** the exact cost of the criteria already fixed on the path.
- **h(n):** for every remaining criterion, its cost at the most favourable value in the cluster (closest city, highest salary, best possible skill coverage, and so on).

Each cost is monotone in the summarised quantity, so h never over-estimates (it is **admissible**) and it only tightens as clusters shrink (it is **consistent**). As a result, A* returns **exactly the optimal top-k**. The tests check this on 80 random queries, plus a check of the bound at every node.

### Greedy best-first search
Orders the frontier by h(n) alone. It does slightly less work per query but is not optimal (see [Results](#-results)).

### Constraint satisfaction (`csp.py`)
- **Variables:** the matched item's sector, contract, education, city, and the item itself.
- **Domains:** the values that actually occur in the tree.
- **Hard constraints:** same sector, same contract, education requirement met, distance ≤ *D* km, offer ≥ 90% of expectation, and experience within the range ± 2 years.

The solver uses backtracking with **node consistency**, **forward checking** on subtree summaries, and value ordering by lower bound. It ranks the solutions by soft score. If fewer than *k* solutions exist, it relaxes constraints one at a time and reports which ones.

### Genetic algorithm (`ga.py`)
Assigns a batch of seekers to job posts, respecting each job's number of `available posts`. This is a weighted bipartite matching problem, so the **Hungarian algorithm gives the exact optimum**. The GA is measured against it:
- one gene per seeker (a job, or none);
- tournament selection with k = 3;
- uniform crossover and reassign/swap mutation;
- capacity repair and elitism.

A simple greedy assignment is reported alongside.

---

## 📊 Results

All numbers come from [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md), generated by `python -m matching evaluate`.

| | A* | Greedy | CSP | Exhaustive |
|---|---|---|---|---|
| Top-10 identical to the optimum (seeker→job / job→seeker) | **100% / 100%** | 1% / 0% | 38% / 26%* | 100% (by definition) |
| Mean top-10 score vs optimum | 100% / 100% | 79% / 73% | 97% / 97%* | 100% |
| Median items scored per query (754 jobs / 8,124 seekers) | **10 / 16** | 10 / 11 | 35 / 38 | 754 / 8,124 |
| Median time per query | 5.5 / 11.8 ms | 5.7 / 36.1 ms | 4.0 / 4.9 ms | 0.5 / 1.5 ms |

\* The CSP is expected to differ from the optimum: it enforces hard constraints, and it had to relax them for 93% / 55% of these queries.

- **A\*** is exactly optimal while scoring about 0.2–1% of the items. On data this small, the single vectorised NumPy pass of the exhaustive baseline is still faster in milliseconds. A*'s advantage is the work it avoids, which matters with larger catalogues or more expensive scoring functions.
- **Planted-match recovery:** a query built from a job's own requirements ranks that job first 100% of the time. With noise added (blank fields, nearby city, perturbed salary and skills), it still ranks first 91% of the time and in the top 10 99.7% of the time.
- **GA vs optimal:** 100% of optimal on 20×8 batches, 99.7% on 40×15 and 92.4% on 100×40, taking 1–2 s. The Hungarian algorithm takes under 1 ms, and the greedy baseline reaches 99%. The GA is kept as a comparison point; `optimal_assignment` is the right production choice.

> The earlier README figures (92% / 78% / 85% accuracy, "40% reduction in hiring time", "72% more diverse shortlists") came from no evaluation in this repository and have been removed. Real relevance can only be measured with human labels; see [`docs/LABELING.md`](docs/LABELING.md).

---

## 🗂️ Data

| File | Rows |
|---|---|
| `data/jobs.csv` | 754 job postings |
| `data/emplo.csv` | 8,124 seekers |
| `data/algeria_distances.json` | road distances between the 48 wilayas |

The data was reportedly collected from Emploitic.com (via [emploitic-scraper](https://github.com/Typh00ns/emploitic-scraper)), LinkedIn (via Apify) and Google Forms. It was standardised with ChatGPT's help, with median/mode imputation.

**Caveats** (details in [`docs/DATA.md`](docs/DATA.md)):
- 58% of jobs list no skills. They make up 11 entire sectors, so the skills can't be imputed from similar postings.
- Jobs and seekers share only 45 exact skill names.
- Titles, departments and skills look randomly combined.
- 1,529 seekers looking for an internship have more than 10 years of experience.

The data therefore appears synthetic or heavily augmented. Treat the scores as demonstrations of the algorithms.

---

## 💻 Usage

### Web application
1. Choose **I'm a Job Seeker** or **I'm an Employer**.
2. Fill in the form and pick an algorithm (A* by default). Each result shows a breakdown by criterion; use **Load more** to page through.
3. The **Batch** section runs the GA against the optimal and greedy assignments.

### JSON API

```bash
curl -X POST localhost:5000/api/match/seeker-to-jobs -H "Content-Type: application/json" \
  -d '{"skills": "Inventory Management, SQL", "experience": 4, "education": 17, "city": "Oran",
       "salary": 70000, "sector": "Retail", "algorithm": "astar", "limit": 10, "offset": 0}'
```

| Endpoint | Purpose |
|---|---|
| `POST /api/match/seeker-to-jobs` | `skills`, `experience`, `education` (0/12/15/17/19/20 or a name), `city`, `salary`, `sector`, `contract_type`, `algorithm` (`astar` \| `greedy` \| `csp` \| `exhaustive`), `limit`, `offset`, `max_distance_km` (CSP) |
| `POST /api/match/job-to-seekers` | same, with `experience_min` / `experience_max` |
| `POST /api/assign` | `n_seekers`, `n_jobs`, `sector`, `seed`, `generations` |
| `GET /api/options`, `/api/stats`, `/api/skills`, `/api/sectors`, `/api/cities`, `/api/health` | metadata |

Invalid input returns HTTP 400 with `{"error": "..."}`.

### Python

```python
from matching import Matcher, SEEKER_TO_JOB

m = Matcher()
q = m.make_query(SEEKER_TO_JOB, skills=["Inventory Management", "SQL"], years=4,
                 education="Master", city="Oran", salary=70000, sector="Retail")
result = m.search(q, algorithm="astar", k=10)
for hit in result.hits:
    print(hit["id"], hit["title"], hit["match_score"], hit["breakdown"]["skills"])
```

### Notebook and CLI

```bash
jupyter notebook notebooks/demo.ipynb          # walkthrough of every algorithm
python -m matching search seeker_to_job --skills "SQL" --city Oran --years 3 --salary 60000
python -m matching evaluate [--quick]          # regenerate docs/BENCHMARKS.md
python -m matching data-report                 # regenerate docs/DATA.md
python -m matching label-sheet                 # create eval/to_label.csv for human labelling
python -m matching export-tree                 # dump the cluster trees as JSON into build/
```

### The original notebook
The original notebook, `finalversion.ipynb`, has been removed; the `matching` package and `notebooks/demo.ipynb` supersede it. It is still in the git history (`git show 7d4321b:finalversion.ipynb > finalversion.ipynb`). Its known problems are listed in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## 🛠️ Development

```bash
pip install -r requirements-dev.txt
python -m pytest                     # about 85 tests, ~40 s
```

The tests cover:
- vocabulary normalisation;
- per-criterion cost properties;
- admissibility of the bounds (bound ≤ exact cost for every item under a node);
- **A\* = exhaustive** on random queries;
- CSP solutions satisfying every hard constraint, with counts matching brute force;
- GA validity and its bound by the brute-force optimum;
- the API, including regression tests for the bugs fixed in this version (HTTP 500 on searches with no sector, only the first 100 rows being scored, the wrong education scale, `Finance` vs `Banking & Finance`).

CI (`.github/workflows/ci.yml`) runs the tests on Python 3.11–3.13, a quick benchmark, and a Docker build with a health check.

---

## 🔮 Future Work

- **Real, consented data** and a filled-in `eval/labels.csv`. Human relevance labels are the only way to tell whether the weights reflect good matches.
- Learn the criterion weights from those labels instead of fixing them by hand.
- Embedding-based skill similarity (for example multilingual sentence embeddings for French and Arabic job posts), and CV parsing.
- Integration with the national employment agency's data, and notifications.

---

## 📖 References

1. Emploitic: [emploitic.com](https://emploitic.com)
2. Apify LinkedIn profile scraper: [apify.com](https://apify.com/curious_coder/linkedin-profile-scraper)
3. Scraping tool: [Typh00ns/emploitic-scraper](https://github.com/Typh00ns/emploitic-scraper)
4. Russell & Norvig, *Artificial Intelligence: A Modern Approach*, chapters on informed search and CSPs
5. Kuhn, H. W. (1955). *The Hungarian method for the assignment problem*
