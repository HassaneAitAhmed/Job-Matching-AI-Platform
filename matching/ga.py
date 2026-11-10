"""Batch assignment of seekers to job posts.

Given a pair-score matrix ``S`` (seekers x jobs, values in [0, 1]) and the
number of open posts per job, find an assignment (each seeker gets at most
one job, each job at most ``posts`` seekers) maximising the total score.

This is a weighted bipartite matching problem, so the optimum is computable
exactly (``optimal_assignment``, Hungarian algorithm via SciPy).  The genetic
algorithm is kept as a comparison point and is reported as a fraction of
that optimum, next to a simple greedy baseline.

Chromosome: one gene per seeker = job index or -1 (unassigned).
Operators : tournament selection (k=3), uniform crossover, reassign/swap
            mutation, capacity repair + random fill, elitism.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass
class AssignmentResult:
    method: str
    genes: np.ndarray           # job index per seeker, -1 = unassigned
    total: float
    elapsed_ms: float
    history: list | None = None
    generations_to_best: int | None = None


def total_score(S, genes) -> float:
    mask = genes >= 0
    return float(S[np.flatnonzero(mask), genes[mask]].sum())


def is_valid(genes, capacity) -> bool:
    counts = np.bincount(genes[genes >= 0], minlength=len(capacity))
    return bool((counts <= capacity).all())


def optimal_assignment(S, capacity) -> AssignmentResult:
    t0 = time.perf_counter()
    slots = np.repeat(np.arange(S.shape[1]), capacity)
    rows, cols = linear_sum_assignment(S[:, slots], maximize=True)
    genes = np.full(S.shape[0], -1)
    genes[rows] = slots[cols]
    return AssignmentResult("optimal (Hungarian)", genes, total_score(S, genes), 1000 * (time.perf_counter() - t0))


def greedy_assignment(S, capacity) -> AssignmentResult:
    t0 = time.perf_counter()
    remaining = capacity.copy()
    genes = np.full(S.shape[0], -1)
    for flat in np.argsort(-S, axis=None, kind="stable"):
        i, j = divmod(int(flat), S.shape[1])
        if genes[i] < 0 and remaining[j] > 0:
            genes[i] = j
            remaining[j] -= 1
    return AssignmentResult("greedy", genes, total_score(S, genes), 1000 * (time.perf_counter() - t0))


class AssignmentGA:
    def __init__(self, S, capacity, pop_size=60, generations=200, mutation_rate=0.02,
                 tournament_k=3, elite=2, seed=0):
        self.S = np.asarray(S, dtype=float)
        self.capacity = np.asarray(capacity, dtype=int)
        self.n, self.m = self.S.shape
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.k = tournament_k
        self.elite = elite
        self.rng = np.random.default_rng(seed)

    def _repair(self, genes):
        counts = np.bincount(genes[genes >= 0], minlength=self.m)
        for j in np.flatnonzero(counts > self.capacity[: len(counts)]):
            holders = np.flatnonzero(genes == j)
            drop = self.rng.choice(holders, size=counts[j] - self.capacity[j], replace=False)
            genes[drop] = -1
        remaining = self.capacity - np.bincount(genes[genes >= 0], minlength=self.m)
        for i in self.rng.permutation(np.flatnonzero(genes < 0)):
            open_jobs = np.flatnonzero(remaining > 0)
            if not len(open_jobs):
                break
            j = self.rng.choice(open_jobs)
            genes[i] = j
            remaining[j] -= 1
        return genes

    def _random_individual(self):
        return self._repair(np.full(self.n, -1))

    def _fitness(self, pop):
        return np.array([total_score(self.S, g) for g in pop])

    def _tournament(self, pop, fit):
        idx = self.rng.choice(len(pop), size=self.k, replace=False)
        return pop[idx[np.argmax(fit[idx])]]

    def _crossover(self, a, b):
        mask = self.rng.random(self.n) < 0.5
        return self._repair(np.where(mask, a, b)), self._repair(np.where(mask, b, a))

    def _mutate(self, genes):
        g = genes.copy()
        for i in np.flatnonzero(self.rng.random(self.n) < self.mutation_rate):
            if self.rng.random() < 0.5:
                g[i] = self.rng.integers(self.m)              # reassign (repair fixes capacity)
            else:
                other = self.rng.integers(self.n)
                g[i], g[other] = g[other], g[i]               # swap two seekers' jobs
        return self._repair(g)

    def run(self) -> AssignmentResult:
        t0 = time.perf_counter()
        pop = np.array([self._random_individual() for _ in range(self.pop_size)])
        fit = self._fitness(pop)
        best_i = int(np.argmax(fit))
        best, best_fit, best_gen = pop[best_i].copy(), float(fit[best_i]), 0
        history = [best_fit]
        for gen in range(1, self.generations + 1):
            elite_idx = np.argsort(-fit)[: self.elite]
            children = [pop[i].copy() for i in elite_idx]
            while len(children) < self.pop_size:
                c1, c2 = self._crossover(self._tournament(pop, fit), self._tournament(pop, fit))
                children.append(self._mutate(c1))
                if len(children) < self.pop_size:
                    children.append(self._mutate(c2))
            pop = np.array(children)
            fit = self._fitness(pop)
            i = int(np.argmax(fit))
            if fit[i] > best_fit + 1e-12:
                best, best_fit, best_gen = pop[i].copy(), float(fit[i]), gen
            history.append(best_fit)
        return AssignmentResult("genetic algorithm", best, best_fit, 1000 * (time.perf_counter() - t0),
                                history, best_gen)
