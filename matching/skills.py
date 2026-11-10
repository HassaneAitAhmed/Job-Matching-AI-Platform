"""Skill vocabulary with TF-IDF based soft matching.

Exact string matching is too strict for this data: jobs and seekers share
only ~45 of ~620 distinct skill names.  Two skill phrases are considered to
match when they are equal after folding, or when the cosine similarity of
their word-level TF-IDF vectors is at least ``threshold`` (so ``Supply
Chain`` matches ``Supply Chain Management`` and ``SCADA`` matches ``SCADA
Systems``, but ``Media Buying`` does not match ``Retail Buying``).

The relation is symmetric, which lets the search code derive admissible
bounds from the union of skills in a cluster.
"""

from __future__ import annotations

import re

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from .normalize import fold

DEFAULT_THRESHOLD = 0.7

# Keep "c#", "e-commerce", "ar/vr", "node.js" as single tokens so that "C" does
# not match "Objective-C".
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#./-]*[a-z0-9+#]|[a-z0-9]")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text) if t not in ENGLISH_STOP_WORDS]


class SkillVocab:
    def __init__(self, phrases, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold
        display: dict[str, str] = {}
        for p in phrases:
            key = fold(p)
            if key and key not in display:
                display[key] = str(p).strip()
        self.keys = sorted(display)
        self.display = [display[k] for k in self.keys]
        self.index = {k: i for i, k in enumerate(self.keys)}

        self._vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            lowercase=False,
            token_pattern=None,
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(self.keys)  # L2-normalised rows

    def __len__(self) -> int:
        return len(self.keys)

    def ids(self, phrases) -> frozenset[int]:
        """Vocabulary ids of the phrases that are in the vocabulary (exact, folded)."""
        out = set()
        for p in phrases:
            i = self.index.get(fold(p))
            if i is not None:
                out.add(i)
        return frozenset(out)

    def related(self, phrase: str) -> frozenset[int]:
        """Ids of every vocabulary skill that soft-matches ``phrase``."""
        key = fold(phrase)
        if not key:
            return frozenset()
        out = set()
        if key in self.index:
            out.add(self.index[key])
        vec = self._vectorizer.transform([key])
        if vec.nnz:
            sims = (self._matrix @ vec.T).toarray().ravel()
            out.update(np.flatnonzero(sims >= self.threshold - 1e-9).tolist())
        return frozenset(out)

    def related_union(self, phrases) -> frozenset[int]:
        out: set[int] = set()
        for p in phrases:
            out |= self.related(p)
        return frozenset(out)

    def indicator(self, ids) -> sparse.csr_matrix:
        """1 x V binary row vector."""
        ids = sorted(ids)
        data = np.ones(len(ids), dtype=np.float32)
        return sparse.csr_matrix((data, ([0] * len(ids), ids)), shape=(1, len(self)))

    def item_matrix(self, id_sets) -> sparse.csr_matrix:
        """N x V binary matrix, one row per item."""
        rows, cols = [], []
        for r, ids in enumerate(id_sets):
            for c in ids:
                rows.append(r)
                cols.append(c)
        data = np.ones(len(rows), dtype=np.float32)
        return sparse.csr_matrix((data, (rows, cols)), shape=(len(id_sets), len(self)))
