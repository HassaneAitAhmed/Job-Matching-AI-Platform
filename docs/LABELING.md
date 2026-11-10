# Human relevance labels

The benchmarks in [BENCHMARKS.md](BENCHMARKS.md) show that the algorithms are correct: A* is optimal, the CSP respects its constraints, and the GA is measured against the true optimum. They can't show whether the *cost model* agrees with what a recruiter or a job seeker would call a good match. Only human judgement can do that.

## Workflow

1. Generate a sheet:

   ```bash
   python -m matching label-sheet --queries 25
   ```

   This writes `eval/to_label.csv`. For each of 25 seeker queries and 25 job queries, it pools the top 5 results from A*, greedy and the CSP, plus 3 random items, in shuffled order. Because of the shuffling, labellers can't tell which algorithm proposed what.

2. Fill in the `relevance` column for each row:

   | value | meaning |
   |---|---|
   | 3 | excellent match: would apply / would interview |
   | 2 | good match |
   | 1 | weak match |
   | 0 | irrelevant |

   Ideally, two people label each row independently and you keep the rounded mean. Leave a row blank if you can't judge it.

3. Save the file as `eval/labels.csv` and commit it.

4. Re-run `python -m matching evaluate`. Section 4 of [BENCHMARKS.md](BENCHMARKS.md) then reports P@10, nDCG@10 and the fraction of results that were judged, for every algorithm.

With labels in place, the next step is to tune the weights in `matching/scoring.py` against nDCG, holding out part of the queries for validation.
