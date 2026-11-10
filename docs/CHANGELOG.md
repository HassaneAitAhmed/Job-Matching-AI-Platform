# Changelog: v2

This file replaces the earlier `IMPLEMENTATION_SUMMARY.md`. That version described the web app as "production-ready" with "zero security vulnerabilities". In fact the app ran a fixed weighted formula, labelled it "Greedy Best-First Search", scored only the first 100 rows, and returned HTTP 500 for the default seeker search.

## Problems found in v1 and how they were fixed

| Problem | Fix | Guarded by |
|---|---|---|
| Notebook model files stored job IDs under `employee_ids` and vice versa; the seeker→job CSP and A* walked the seeker model and returned seeker IDs | New `matching` package; the tree records which entity it holds; seeker queries search the job tree | `test_seeker_search_returns_jobs_not_seekers` |
| Web app used none of the algorithms | The API runs A*, greedy, CSP or exhaustive (`algorithm` parameter), plus GA batch assignment | `test_seeker_search_without_sector_works[*]` |
| HTTP 500 when a job had no skills (58% of jobs) | Missing values handled when loading; unlisted skills scored as a weak match and flagged in the UI | same |
| Only `head(100)` rows were scored | All items are considered (A* prunes with bounds) | `test_employer_search_considers_all_candidates` |
| Form sent education 9/12/14/16/18; data uses 12/15/17/19/20 | Education levels come from `/api/options` | `test_options_use_canonical_values` |
| `Finance` vs `Banking & Finance`, `Stage` vs `Internship`, `License` vs `Licence`, accented cities missing from the distance matrix | `matching/normalize.py` | `test_every_dataset_value_is_resolved`, `test_finance_employer_search_finds_candidates` |
| GA lowercased city names, so every distance lookup failed | One shared cost model | `test_scoring.py` |
| `PairGA.run()` never called; the "GA" timing measured a linear scan | GA solves batch assignment and is compared with the Hungarian optimum | `test_ga.py` |
| A* heuristic terms constant (lists passed where scalars were expected); h double-counted g; results were clusters | Bounds computed from cluster summaries, proven admissible and checked; A* returns ranked items | `test_bounds_never_overestimate`, `test_astar_matches_exhaustive` |
| CSP returned the first DFS hits, unranked; the distance matrix was unused | Node consistency + forward checking, distance constraint, ranking, relaxation | `test_csp.py` |
| `/api/skills` always returned `[]` | Returns the 626-skill vocabulary | `test_skills_endpoint_not_empty` |
| No input validation (bad input gave HTTP 500) | Typed parsing; HTTP 400 with a message | `test_validation_errors_are_400` |
| `innerHTML` with data values | DOM built with `textContent` | - |
| `load_data()` only ran under `__main__` (broke under `flask run` / gunicorn) | `create_app()` factory | Docker job in CI |
| 17 MB of generated JSON committed; original notebook superseded | Trees are built in memory at start-up (~3 s); `python -m matching export-tree` dumps them; `finalversion.ipynb` removed (recover with `git show 7d4321b:finalversion.ipynb`) | - |
| Unsupported metrics in the README and UI | Replaced with measured numbers in [BENCHMARKS.md](BENCHMARKS.md) | `python -m matching evaluate` |

## Not done, because it needs people or data

- **Real data:** the bundled data looks synthetic ([DATA.md](DATA.md)).
- **Human relevance labels:** the tooling is ready ([LABELING.md](LABELING.md)), but the labels need people.
- **Imputing missing job skills:** the jobs without skills make up entire sectors, so there are no similar postings to borrow from.
