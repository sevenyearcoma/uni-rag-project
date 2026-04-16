"""
Embedding module — wraps sentence-transformers for dense vector encoding.
Falls back gracefully to a tiny random model for testing without GPU.
"""
from __future__ import annotations

import os
from typing import Union

import numpy as np

_DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class Embedder:
    """
    Thin wrapper around a sentence-transformers model.

    Usage::

        embedder = Embedder()
        vec = embedder.embed("Hello world")           # shape (384,)
        vecs = embedder.embed_batch(["a", "b", "c"])  # shape (3, 384)
    """

    def __init__(self, model_name: str = _DEFAULT_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        print(f"  [embedder] Loading model: {model_name}")
        self._model = SentenceTransformer(model_name)
        self.dimension = self._model.get_sentence_embedding_dimension()
        print(f"  [embedder] Ready — dimension: {self.dimension}")

    def embed(self, text: str) -> np.ndarray:
        """Embed a single string. Returns shape (dim,)."""
        return self._model.encode(text, normalize_embeddings=True)

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Embed a list of strings efficiently.
        Returns shape (N, dim) as float32.
        """
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
