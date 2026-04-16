---
title: "Vector Databases for RAG"
date: "2024-03-08"
---

# Vector Databases for RAG

A vector database stores dense numerical vectors (embeddings) alongside metadata, enabling fast approximate nearest-neighbour (ANN) search at query time.

## Why Not a Traditional Database?

Traditional databases (SQL, NoSQL) store and retrieve data by exact matches or range queries. Semantic similarity search — "find documents whose *meaning* is closest to this query" — requires comparing vectors in high-dimensional space. This is fundamentally incompatible with B-tree or hash-based indexing.

Vector databases use specialised index structures (HNSW, IVF, LSH) that trade a small accuracy loss for orders-of-magnitude speed improvement over brute-force cosine comparison.

## ChromaDB

ChromaDB is the vector database used in this pipeline. Key properties:

- **Persistence**: stores vectors on disk (SQLite + Parquet) — survives restarts without re-indexing
- **Zero configuration**: runs in-process, no server required for local development
- **Metadata filtering**: supports exact-match `where` clauses on any metadata field (e.g., filter by `strategy="recursive"`)
- **Cosine similarity**: configured via `{"hnsw:space": "cosine"}` on the collection
- **Python-native API**: `chromadb` pip package, no Docker required

### Record Structure

Each vector record in ChromaDB holds:
- `id`: UUID (auto-generated)
- `embedding`: float32 list (384 dimensions for all-MiniLM-L6-v2)
- `document`: the raw chunk text
- `metadata`: dict containing filename, title, date, chunk_index, strategy, token_count, source_url

### Querying

```python
results = collection.query(
    query_embeddings=[query_vec],
    n_results=5,
    include=["documents", "metadatas", "distances"],
)
```

The returned distances are L2 distances in cosine space, which are converted to cosine similarity scores: `score = 1.0 - distance`.

## FAISS (Alternative)

FAISS (Facebook AI Similarity Search) is a C++ library with Python bindings for billion-scale ANN search.

### Comparison with ChromaDB

| Feature | ChromaDB | FAISS |
|---------|----------|-------|
| Persistence | Built-in | Manual (save/load index files) |
| Metadata storage | Built-in | External (requires separate store) |
| Filtering | Yes | No (post-filter only) |
| Scale | Up to ~10M vectors comfortably | Billions |
| Setup | Zero-config pip install | Requires index type selection |
| Best for | Development, moderate scale | Production, large scale |

For this pipeline, ChromaDB is preferred due to its integrated metadata support and persistence. FAISS would be appropriate for a production deployment with millions of documents.

## Cosine Similarity

Cosine similarity measures the cosine of the angle between two vectors:

```
similarity(A, B) = (A · B) / (||A|| × ||B||)
```

For normalised vectors (as produced by sentence-transformers with `normalize_embeddings=True`), this reduces to the dot product: `A · B`.

A score of 1.0 means identical direction (maximum similarity). A score of 0.0 means orthogonal (no semantic relationship). Negative scores indicate opposite meaning — rare in practice for natural language.

## ANN vs Exact Search

Exact cosine search is O(N×D) where N is the number of vectors and D is the dimension. For N=100,000 and D=384, this is ~38 million operations per query — feasible but slow.

ChromaDB's HNSW (Hierarchical Navigable Small World) index reduces this to O(log N) at query time, with a construction cost of O(N log N) at index time. The accuracy loss (recall@5 vs exact search) is typically >99% for well-tuned parameters.
