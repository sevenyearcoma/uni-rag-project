"""
FAISS vector store with a JSON metadata sidecar.

Originally I planned to use ChromaDB here, but it requires building a C++
extension (hnswlib) on Windows and that immediately failed without the Visual
Studio build tools installed. Switched to faiss-cpu which has pre-built wheels
and just works.

FAISS doesn't store metadata natively, so I keep a parallel JSON file
(metadata.json) where index position N in FAISS maps to position N in the
JSON array. It's simple but it means I have to keep them in sync — adding
is fine, but deleting individual vectors would be a mess. For this project
that's not a concern.

Using IndexFlatIP (exact inner-product search). The vectors are L2-normalised
before storage so inner-product == cosine similarity. For the chunk counts in
this project, exact search is fast enough — no need for approximate indexing.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from .chunker import Chunk
from .embedder import Embedder

_PERSIST_DIR  = os.getenv("FAISS_PERSIST_DIR", "./faiss_db")
_INDEX_FILE   = "index.faiss"
_META_FILE    = "metadata.json"


class VectorStore:
    """
    Manages a FAISS flat inner-product index alongside a JSON metadata store.

    Typical flow::

        store = VectorStore(embedder)
        store.add_chunks(chunks)
        results = store.query("What is RAG?", k=5)
    """

    def __init__(self, embedder: Embedder, persist_dir: str = _PERSIST_DIR):
        self.embedder    = embedder
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self._index_path = self.persist_dir / _INDEX_FILE
        self._meta_path  = self.persist_dir / _META_FILE

        self._dim = embedder.dimension
        self._load()
        print(f"  [vector_store] FAISS ready — {self.count()} vectors stored")

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load index + metadata from disk, or create fresh ones."""
        if self._index_path.exists() and self._meta_path.exists():
            self._index: faiss.IndexFlatIP = faiss.read_index(str(self._index_path))
            with open(self._meta_path, encoding="utf-8") as f:
                raw = json.load(f)
            # raw is a list of {"id": str, "text": str, "metadata": dict}
            self._records: list[dict[str, Any]] = raw
        else:
            # IndexFlatIP: exact inner-product search (= cosine for unit vecs)
            self._index = faiss.IndexFlatIP(self._dim)
            self._records = []

    def _save(self) -> None:
        """Flush index and metadata to disk."""
        faiss.write_index(self._index, str(self._index_path))
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(self._records, f, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[Chunk], batch_size: int = 128) -> None:
        """Embed and index a list of Chunk objects."""
        if not chunks:
            return

        texts     = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        embeddings: np.ndarray = self.embedder.embed_batch(
            texts, batch_size=batch_size, show_progress=True
        )
        # sentence-transformers already L2-normalises when normalize_embeddings=True
        # but let's be explicit so inner-product == cosine similarity
        faiss.normalize_L2(embeddings)

        self._index.add(embeddings.astype("float32"))

        for text, meta in zip(texts, metadatas):
            self._records.append({"id": str(uuid.uuid4()), "text": text, "metadata": meta})

        self._save()
        print(f"  [vector_store] Indexed {len(chunks)} chunks — total: {self.count()}")

    def clear(self) -> None:
        """Delete all vectors and metadata."""
        self._index = faiss.IndexFlatIP(self._dim)
        self._records = []
        self._save()
        print("  [vector_store] Index cleared.")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query(
        self,
        query_text: str,
        k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the top-k most similar chunks for *query_text*.

        Args:
            query_text: The user's question.
            k:          Number of results to return.
            where:      Optional metadata equality filter, e.g. {"strategy": "recursive"}.
                        Applied as a post-filter after FAISS retrieval (fetches k*10 then
                        filters down to k).

        Returns:
            List of dicts: {"text", "metadata", "score", "id"}
        """
        if self.count() == 0:
            return []

        q_vec = self.embedder.embed(query_text).reshape(1, -1).astype("float32")
        faiss.normalize_L2(q_vec)

        # Over-fetch when filtering so we can still return k results after pruning
        fetch_k = min(self.count(), k * 10 if where else k)
        scores_arr, indices_arr = self._index.search(q_vec, fetch_k)

        hits: list[dict[str, Any]] = []
        for score, idx in zip(scores_arr[0], indices_arr[0]):
            if idx < 0:
                continue  # FAISS pads with -1 when fewer than k vectors exist
            record = self._records[idx]

            # Post-filter
            if where:
                if not all(record["metadata"].get(key) == val for key, val in where.items()):
                    continue

            hits.append({
                "text":     record["text"],
                "metadata": record["metadata"],
                "score":    round(float(score), 4),
                "id":       record["id"],
            })

            if len(hits) == k:
                break

        return hits

    def count(self) -> int:
        return self._index.ntotal
