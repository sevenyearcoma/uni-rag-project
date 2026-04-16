"""
FastAPI backend for the RAG pipeline.

Endpoints:
  POST /ingest    — load documents from a directory, chunk, embed, index
  POST /query     — embed query, retrieve top-k, generate grounded answer
  GET  /health    — quick check + vector count
  GET  /stats     — model name, persist dir, total vectors
  DELETE /index   — wipe the index (useful when re-ingesting with different params)

The embedder and vector store are initialised once at startup and reused
across requests — loading the sentence-transformer model on every request
would be extremely slow.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

# Late import so dotenv is loaded first
from ingest.loader import load_directory
from retrieval.chunker import fixed_size_chunk, recursive_chunk, ChunkStrategy
from retrieval.embedder import Embedder
from retrieval.vector_store import VectorStore
from generation.llm import generate_answer

# ---------------------------------------------------------------------------
# Global singletons (initialised once at startup)
# ---------------------------------------------------------------------------

_embedder: Embedder | None = None
_store: VectorStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _embedder, _store
    print("[startup] Initialising embedder and vector store…")
    _embedder = Embedder()
    _store = VectorStore(_embedder)
    yield
    print("[shutdown] Goodbye.")


app = FastAPI(
    title="RAG Pipeline API",
    version="1.0.0",
    description="Grounded, cited Retrieval-Augmented Generation backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    directory: str = Field(
        default="./data/sample_docs",
        description="Path to directory containing PDF / Markdown files.",
    )
    strategy: str = Field(
        default="fixed",
        description="Chunking strategy: 'fixed' or 'recursive'.",
    )
    chunk_size: int = Field(default=256, ge=100, le=512)
    overlap: float = Field(default=0.15, ge=0.10, le=0.25)
    clear_first: bool = Field(
        default=False,
        description="If true, wipe the existing index before ingesting.",
    )


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    k: int = Field(default=5, ge=1, le=20)
    strategy_filter: str | None = Field(
        default=None,
        description="Filter retrieved chunks by strategy: 'fixed_size' or 'recursive'.",
    )


class IngestResponse(BaseModel):
    documents_loaded: int
    chunks_created: int
    total_vectors: int
    strategy: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks: list[dict]
    provider: str
    model: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "vectors": _store.count() if _store else 0}


@app.get("/stats")
async def stats():
    if _store is None:
        raise HTTPException(503, "Vector store not ready")
    return {
        "total_vectors": _store.count(),
        "embedding_model": _embedder.model_name if _embedder else None,
        "chroma_dir": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    if _store is None or _embedder is None:
        raise HTTPException(503, "Service not ready")

    doc_dir = Path(req.directory)
    if not doc_dir.exists():
        raise HTTPException(400, f"Directory not found: {req.directory}")

    if req.clear_first:
        _store.clear()

    # Load documents
    documents = load_directory(doc_dir)
    if not documents:
        raise HTTPException(400, "No supported documents found in directory (PDF / Markdown only).")

    # Chunk documents
    all_chunks = []
    chunker = fixed_size_chunk if req.strategy == "fixed" else recursive_chunk

    for doc in documents:
        chunks = chunker(
            doc.text,
            doc.metadata,
            chunk_size=req.chunk_size,
            overlap=req.overlap,
        )
        all_chunks.extend(chunks)

    # Index
    _store.add_chunks(all_chunks)

    return IngestResponse(
        documents_loaded=len(documents),
        chunks_created=len(all_chunks),
        total_vectors=_store.count(),
        strategy=req.strategy,
    )


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if _store is None:
        raise HTTPException(503, "Vector store not ready — run /ingest first.")

    if _store.count() == 0:
        raise HTTPException(400, "Vector store is empty — run /ingest first.")

    # Build optional metadata filter
    where = None
    if req.strategy_filter:
        where = {"strategy": req.strategy_filter}

    chunks = _store.query(req.query, k=req.k, where=where)
    result = generate_answer(req.query, chunks)

    return QueryResponse(**result)


@app.delete("/index")
async def clear_index():
    if _store is None:
        raise HTTPException(503, "Service not ready")
    _store.clear()
    return {"status": "cleared", "total_vectors": 0}
