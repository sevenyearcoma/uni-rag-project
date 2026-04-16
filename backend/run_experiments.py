"""
Automated experiment runner — satisfies the "5 experiments" requirement.

Each experiment varies ONE parameter while holding others constant, then
measures precision@5, RAGAS faithfulness, and answer relevance.
Results are appended to eval/experiment_log.csv.

Experiments:
  1. Chunking strategy    : fixed_size  vs recursive
  2. Chunk size           : 128 tokens  vs 256 tokens  (fixed strategy)
  3. Overlap fraction     : 10%         vs 25%          (fixed, 256 tok)
  4. Top-k retrieval      : k=3         vs k=5          (fixed, 256 tok, 15% overlap)
  5. Embedding model      : all-MiniLM-L6-v2 vs paraphrase-MiniLM-L6-v2

Usage:
    cd backend
    python run_experiments.py [--qa-file eval/qa_dataset.json] [--log eval/experiment_log.csv]

Note: Each experiment re-indexes the corpus and runs 30 QA pairs through
      the pipeline, so this script takes several minutes to complete.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from ingest.loader import load_directory
from retrieval.chunker import fixed_size_chunk, recursive_chunk
from retrieval.embedder import Embedder
from retrieval.vector_store import VectorStore
from generation.llm import generate_answer
from eval.evaluator import precision_at_k, ragas_faithfulness, ragas_relevance

QA_FILE    = Path("eval/qa_dataset.json")
LOG_FILE   = Path("eval/experiment_log.csv")
DOCS_DIR   = Path("data/sample_docs")
LOG_FIELDS = [
    "timestamp", "component_changed",
    "parameter_before", "parameter_after",
    "metric_before", "metric_after", "observation",
]


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def build_and_index(
    docs_dir: Path,
    embedder: Embedder,
    strategy: str = "fixed",
    chunk_size: int = 256,
    overlap: float = 0.15,
) -> VectorStore:
    """Re-index corpus with given parameters. Returns a fresh VectorStore."""
    store = VectorStore(embedder, persist_dir=f"./faiss_db_exp_{strategy}_{chunk_size}_{int(overlap*100)}")
    store.clear()

    documents = load_directory(docs_dir)
    chunker = fixed_size_chunk if strategy == "fixed" else recursive_chunk
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunker(doc.text, doc.metadata, chunk_size=chunk_size, overlap=overlap))

    store.add_chunks(all_chunks)
    return store


def evaluate(
    store: VectorStore,
    qa_data: list[dict],
    k: int = 5,
    strategy_filter: str | None = None,
) -> tuple[float, float, float]:
    """
    Run QA pairs against *store* and return (avg_precision@k, avg_faithfulness, avg_relevance).
    """
    prec, faith, relev = [], [], []

    for item in qa_data:
        question      = item["question"]
        relevant_docs = set(item.get("relevant_docs", []))
        where = {"strategy": strategy_filter} if strategy_filter else None

        chunks = store.query(question, k=k, where=where)
        filenames = [c["metadata"].get("filename", "") for c in chunks]

        p = precision_at_k(filenames, relevant_docs, k)

        result = generate_answer(question, chunks)
        f = ragas_faithfulness(result["answer"], chunks)
        r = ragas_relevance(question, result["answer"])

        prec.append(p);  faith.append(f);  relev.append(r)

    n = len(qa_data)
    return (
        round(sum(prec)  / n, 3),
        round(sum(faith) / n, 3),
        round(sum(relev) / n, 3),
    )


def log_row(log_path: Path, row: dict) -> None:
    write_header = not log_path.exists() or log_path.stat().st_size == 0
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def metric_str(p: float, f: float, r: float, k: int = 5) -> str:
    return f"P@{k}={p:.3f}, faithfulness={f:.3f}, relevance={r:.3f}"


# ---------------------------------------------------------------------------
# Experiment definitions
# ---------------------------------------------------------------------------

def experiment_1_strategy(qa_data, log_path, k=5):
    """Exp 1: Fixed-size vs Recursive chunking strategy."""
    print("\n[Exp 1] Chunking strategy: fixed_size vs recursive")

    emb   = Embedder()
    store_a = build_and_index(DOCS_DIR, emb, strategy="fixed",     chunk_size=256, overlap=0.15)
    p_a, f_a, r_a = evaluate(store_a, qa_data, k=k, strategy_filter="fixed_size")

    store_b = build_and_index(DOCS_DIR, emb, strategy="recursive", chunk_size=256, overlap=0.15)
    p_b, f_b, r_b = evaluate(store_b, qa_data, k=k, strategy_filter="recursive")

    log_row(log_path, {
        "timestamp":          datetime.now().isoformat(),
        "component_changed":  "chunking_strategy",
        "parameter_before":   "fixed_size",
        "parameter_after":    "recursive",
        "metric_before":      metric_str(p_a, f_a, r_a),
        "metric_after":       metric_str(p_b, f_b, r_b),
        "observation":        (
            "Recursive chunking produces sentence-aligned chunks; "
            "fixed-size is faster and more deterministic. "
            f"Precision delta: {p_b - p_a:+.3f}"
        ),
    })
    print(f"  fixed:     {metric_str(p_a, f_a, r_a)}")
    print(f"  recursive: {metric_str(p_b, f_b, r_b)}")


def experiment_2_chunk_size(qa_data, log_path, k=5):
    """Exp 2: Chunk size 128 vs 256 tokens (fixed strategy)."""
    print("\n[Exp 2] Chunk size: 128 vs 256 tokens")

    emb   = Embedder()
    store_a = build_and_index(DOCS_DIR, emb, strategy="fixed", chunk_size=128, overlap=0.15)
    p_a, f_a, r_a = evaluate(store_a, qa_data, k=k)

    store_b = build_and_index(DOCS_DIR, emb, strategy="fixed", chunk_size=256, overlap=0.15)
    p_b, f_b, r_b = evaluate(store_b, qa_data, k=k)

    log_row(log_path, {
        "timestamp":          datetime.now().isoformat(),
        "component_changed":  "chunk_size",
        "parameter_before":   "128 tokens",
        "parameter_after":    "256 tokens",
        "metric_before":      metric_str(p_a, f_a, r_a),
        "metric_after":       metric_str(p_b, f_b, r_b),
        "observation":        (
            "Larger chunks carry more context per vector, improving faithfulness. "
            "Smaller chunks are more precise but may miss surrounding context. "
            f"Precision delta: {p_b - p_a:+.3f}"
        ),
    })
    print(f"  128 tok: {metric_str(p_a, f_a, r_a)}")
    print(f"  256 tok: {metric_str(p_b, f_b, r_b)}")


def experiment_3_overlap(qa_data, log_path, k=5):
    """Exp 3: Overlap 10% vs 25% (fixed, 256 tokens)."""
    print("\n[Exp 3] Overlap: 10% vs 25%")

    emb   = Embedder()
    store_a = build_and_index(DOCS_DIR, emb, strategy="fixed", chunk_size=256, overlap=0.10)
    p_a, f_a, r_a = evaluate(store_a, qa_data, k=k)

    store_b = build_and_index(DOCS_DIR, emb, strategy="fixed", chunk_size=256, overlap=0.25)
    p_b, f_b, r_b = evaluate(store_b, qa_data, k=k)

    log_row(log_path, {
        "timestamp":          datetime.now().isoformat(),
        "component_changed":  "overlap_fraction",
        "parameter_before":   "10%",
        "parameter_after":    "25%",
        "metric_before":      metric_str(p_a, f_a, r_a),
        "metric_after":       metric_str(p_b, f_b, r_b),
        "observation":        (
            "Higher overlap reduces boundary effects where a sentence spans two chunks, "
            "at the cost of more redundant vectors and a larger index. "
            f"Precision delta: {p_b - p_a:+.3f}"
        ),
    })
    print(f"  10% overlap: {metric_str(p_a, f_a, r_a)}")
    print(f"  25% overlap: {metric_str(p_b, f_b, r_b)}")


def experiment_4_top_k(qa_data, log_path):
    """Exp 4: Top-k retrieval k=3 vs k=5 (fixed, 256 tok, 15% overlap)."""
    print("\n[Exp 4] Top-k retrieval: k=3 vs k=5")

    emb   = Embedder()
    store = build_and_index(DOCS_DIR, emb, strategy="fixed", chunk_size=256, overlap=0.15)

    p_a, f_a, r_a = evaluate(store, qa_data, k=3)
    p_b, f_b, r_b = evaluate(store, qa_data, k=5)

    log_row(log_path, {
        "timestamp":          datetime.now().isoformat(),
        "component_changed":  "top_k",
        "parameter_before":   "k=3",
        "parameter_after":    "k=5",
        "metric_before":      metric_str(p_a, f_a, r_a, k=3),
        "metric_after":       metric_str(p_b, f_b, r_b, k=5),
        "observation":        (
            "Increasing k provides more context to the LLM, improving recall "
            "but increasing prompt length and latency. "
            f"Precision@k delta: {p_b - p_a:+.3f}"
        ),
    })
    print(f"  k=3: {metric_str(p_a, f_a, r_a, k=3)}")
    print(f"  k=5: {metric_str(p_b, f_b, r_b, k=5)}")


def experiment_5_embedding_model(qa_data, log_path, k=5):
    """Exp 5: Embedding model — all-MiniLM-L6-v2 vs paraphrase-MiniLM-L6-v2."""
    print("\n[Exp 5] Embedding model: all-MiniLM-L6-v2 vs paraphrase-MiniLM-L6-v2")

    from retrieval.embedder import Embedder

    # Model A — default
    emb_a   = Embedder("all-MiniLM-L6-v2")
    store_a = VectorStore(emb_a, persist_dir="./faiss_db_exp_minilm_all")
    store_a.clear()
    docs = load_directory(DOCS_DIR)
    chunks_a = []
    for doc in docs:
        chunks_a.extend(fixed_size_chunk(doc.text, doc.metadata, chunk_size=256, overlap=0.15))
    store_a.add_chunks(chunks_a)
    p_a, f_a, r_a = evaluate(store_a, qa_data, k=k)

    # Model B — paraphrase variant (same dimension, different training objective)
    emb_b   = Embedder("paraphrase-MiniLM-L6-v2")
    store_b = VectorStore(emb_b, persist_dir="./faiss_db_exp_minilm_para")
    store_b.clear()
    chunks_b = []
    for doc in docs:
        chunks_b.extend(fixed_size_chunk(doc.text, doc.metadata, chunk_size=256, overlap=0.15))
    store_b.add_chunks(chunks_b)
    p_b, f_b, r_b = evaluate(store_b, qa_data, k=k)

    log_row(log_path, {
        "timestamp":          datetime.now().isoformat(),
        "component_changed":  "embedding_model",
        "parameter_before":   "all-MiniLM-L6-v2",
        "parameter_after":    "paraphrase-MiniLM-L6-v2",
        "metric_before":      metric_str(p_a, f_a, r_a),
        "metric_after":       metric_str(p_b, f_b, r_b),
        "observation":        (
            "all-MiniLM is fine-tuned on diverse semantic similarity pairs; "
            "paraphrase-MiniLM targets paraphrase detection. "
            "Performance may differ on domain-specific corpora. "
            f"Precision delta: {p_b - p_a:+.3f}"
        ),
    })
    print(f"  all-MiniLM:        {metric_str(p_a, f_a, r_a)}")
    print(f"  paraphrase-MiniLM: {metric_str(p_b, f_b, r_b)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run 5-experiment evaluation suite.")
    parser.add_argument("--qa-file", default=str(QA_FILE))
    parser.add_argument("--log",     default=str(LOG_FILE))
    parser.add_argument(
        "--experiments",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4, 5],
        help="Which experiments to run (1-5). Default: all.",
    )
    args = parser.parse_args()

    qa_data  = json.loads(Path(args.qa_file).read_text(encoding="utf-8"))
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    exp_map = {
        1: experiment_1_strategy,
        2: experiment_2_chunk_size,
        3: experiment_3_overlap,
        4: experiment_4_top_k,
        5: experiment_5_embedding_model,
    }

    print(f"Running {len(args.experiments)} experiment(s) against {len(qa_data)} QA pairs.")
    print(f"Results → {log_path}\n")

    for exp_num in args.experiments:
        fn = exp_map.get(exp_num)
        if fn is None:
            print(f"[warn] Unknown experiment {exp_num}, skipping.")
            continue
        if exp_num == 4:
            fn(qa_data, log_path)          # no k arg — compares k internally
        else:
            fn(qa_data, log_path)

    print(f"\nAll done. Experiment log: {log_path}")


if __name__ == "__main__":
    main()
