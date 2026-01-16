# Ai-project
job matching Ai project
# Heuristic
- Start with two datasets: job offers and job seekers
- For each pair, assign a matching score based on:
  - Skills required by the offer
  - Skills existing in the seeker
- Store results in a matrix where:
  - Columns = Jobs
  - Rows = Seekers
- State representation: Pair from matrix
- Initial state: Pair with highest score
- Each depth represents a job
- Goal state: All jobs assigned to best available seeker
- Child nodes: New job with all unassigned seekers
- Path selection: Choose node with highest cumulative score
- Final result: Path from root to leaf containing all matches



# JobSeeker–JobOffer Matching via CSP & Soft Ranking

This project demonstrates a Constraint Satisfaction Problem (CSP) approach to matching job seekers with job offers, combining **hard constraint propagation** with a **soft scoring** function to select the top *k* candidates.

---

## Table of Contents

1. [Overview](#overview)
2. [CSP Formulation](#csp-formulation)

   * [Variables & Domains](#variables--domains)
   * [Variable Ordering](#variable-ordering)
3. [Constraint Propagation](#constraint-propagation)
4. [Backtracking Semantics](#backtracking-semantics)
5. [Soft Constraints & Top-*k* Selection](#soft-constraints--top-k-selection)
6. [Pipeline Implementation](#pipeline-implementation)
7. [Example Usage](#example-usage)
8. [Installation & Running](#installation--running)
9. [License](#license)

---

## Overview

Given a **job offer** with fixed requirements (sector, location, minimum experience, education level, required skills, salary range) and a pool of **job seekers** (each with the same set of attributes plus an ID), the goal is to:

1. **Filter** out all seekers who violate any *hard* requirement.
2. **Score** the remaining candidates on *soft* criteria via a weighted evaluation function.
3. **Select** the top *k* seekers by score.

This hybrid CSP + ranking method ensures maximal early pruning of the candidate set and efficient selection of the best matches.

---

## CSP Formulation

### Variables & Domains

* **Variables**: one per requirement:

  ```text
  V = [ Sector, Location, Experience, Education, Skills, Salary ]
  ```

* **Domains**: at each step, the domain is the current list of remaining seekers. Assigning a variable means filtering that list to those whose attribute matches the offer.

### Variable Ordering

To maximize pruning, we apply constraints in this fixed order:

```text
Sector → Location → Experience → Education → Skills → Salary
```

By filtering on **Sector** first, we immediately restrict to the smallest relevant cluster, speeding up later checks.

---

## Constraint Propagation

1. **Assign** each variable to the job offer’s requirement.
2. **Filter** the candidate list by that requirement.
3. **Check**: if the list becomes empty at any point, stop and report failure (no matches).

This is equivalent to forward-checking in classic CSPs.

---

## Backtracking Semantics

Since the job’s requirements are fixed, any failure on a hard constraint means there is no alternative to try—so the algorithm simply aborts and returns an empty list.

---

## Soft Constraints & Top-*k* Selection

Once all hard constraints are satisfied (i.e., the candidate set is non-empty), we compute for each seeker:

```python
score_job(seeker, job_offer)
```

This function is a weighted sum of: salary proximity, skill overlap, experience surplus, education match, etc. We then sort by descending score and pick the top *k*.

---

## Pipeline Implementation

```python
from typing import List


def match_top_k(
    job_offer: JobOffer,
    seekers: List[JobSeeker],
    k: int = 3
) -> List[JobSeeker]:
    # Ordered hard-constraint tests
    tests = [
        lambda s: s.job_interest   == job_offer.sector,
        lambda s: s.location       == job_offer.location,
        lambda s: s.experience     >= job_offer.min_experience,
        lambda s: s.education_level>= job_offer.education_level,
        lambda s: job_offer.required_skills.issubset(s.skills),
        lambda s: job_offer.salary_range[0] <= s.salary <= job_offer.salary_range[1],
    ]

    candidates = list(seekers)

    # Apply each hard filter in order
    for test in tests:
        candidates = [s for s in candidates if test(s)]
        if not candidates:
            return []   # CSP failure

    # Score & select top-k
    scored = [(s, score_job(s, job_offer)) for s in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s,_ in scored[:k]]
```

---
