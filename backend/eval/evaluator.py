"""
Evaluation module for the RAG pipeline.

Metrics:
  - precision@k  — fraction of top-k retrieved chunks that are relevant
  - RAGAS-style faithfulness  — does the answer stay grounded in context?
  - RAGAS-style answer relevance — how relevant is the answer to the question?

Usage::

    python -m eval.evaluator --qa-file eval/qa_dataset.json --k 5
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on path when run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval.embedder import Embedder
from retrieval.vector_store import VectorStore
from generation.llm import generate_answer


# ---------------------------------------------------------------------------
# Precision @ k
# ---------------------------------------------------------------------------

def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """
    Fraction of the top-k retrieved docs that are actually relevant.

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs or filenames.
        relevant_ids:  Set of ground-truth relevant doc IDs / filenames.
        k:             Cut-off rank.
    """
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / k if k > 0 else 0.0


# ---------------------------------------------------------------------------
# RAGAS-style scoring (LLM-as-judge, lightweight)
# ---------------------------------------------------------------------------

_FAITHFULNESS_PROMPT = """\
You are evaluating whether an AI-generated answer is faithful to the provided context.
Score from 0.0 (completely unfaithful) to 1.0 (fully supported by context).
Respond with ONLY a float, nothing else.

Context:
{context}

Answer:
{answer}

Faithfulness score:"""

_RELEVANCE_PROMPT = """\
You are evaluating whether an AI-generated answer is relevant to the question.
Score from 0.0 (irrelevant) to 1.0 (fully relevant and complete).
Respond with ONLY a float, nothing else.

Question: {question}

Answer:
{answer}

Relevance score:"""


def _llm_score(prompt: str) -> float:
    """Ask the LLM to return a float score."""
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=8,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            return float(resp.content[0].text.strip())
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=8,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            return float(resp.choices[0].message.content.strip())
    except (ValueError, KeyError, Exception):
        return 0.0
    return 0.0


def ragas_faithfulness(answer: str, chunks: list[dict]) -> float:
    context = "\n\n".join(c["text"] for c in chunks)
    prompt = _FAITHFULNESS_PROMPT.format(context=context[:4000], answer=answer)
    return _llm_score(prompt)


def ragas_relevance(question: str, answer: str) -> float:
    prompt = _RELEVANCE_PROMPT.format(question=question, answer=answer)
    return _llm_score(prompt)


# ---------------------------------------------------------------------------
# Full evaluation run
# ---------------------------------------------------------------------------

def run_evaluation(
    qa_path: str | Path,
    k: int = 5,
    strategies: list[str] | None = None,
    log_path: str | Path = "eval/experiment_log.csv",
) -> list[dict[str, Any]]:
    """
    Run the full evaluation suite against a QA dataset.

    Args:
        qa_path:    Path to qa_dataset.json.
        k:          Top-k retrieval cut-off.
        strategies: List of chunking strategies to test ["fixed_size", "recursive"].
        log_path:   Where to append CSV rows.

    Returns:
        List of result dicts.
    """
    if strategies is None:
        strategies = ["fixed_size", "recursive"]

    qa_data: list[dict] = json.loads(Path(qa_path).read_text(encoding="utf-8"))
    embedder = Embedder()
    store = VectorStore(embedder)

    results = []
    log_rows = []

    for strategy in strategies:
        print(f"\n[eval] === Strategy: {strategy} ===")
        prec_scores, faith_scores, rel_scores = [], [], []

        for item in qa_data:
            question = item["question"]
            ground_truth = item["answer"]
            relevant_docs: set[str] = set(item.get("relevant_docs", []))

            # Filter by strategy
            where = {"strategy": strategy} if store.count() > 0 else None
            chunks = store.query(question, k=k, where=where)
            retrieved_filenames = [c["metadata"].get("filename", "") for c in chunks]

            # Metrics
            p_at_k = precision_at_k(retrieved_filenames, relevant_docs, k)
            result = generate_answer(question, chunks)
            faith = ragas_faithfulness(result["answer"], chunks)
            relev = ragas_relevance(question, result["answer"])

            prec_scores.append(p_at_k)
            faith_scores.append(faith)
            rel_scores.append(relev)

            results.append({
                "strategy": strategy,
                "question": question,
                "answer": result["answer"],
                "ground_truth": ground_truth,
                "precision_at_k": p_at_k,
                "faithfulness": faith,
                "relevance": relev,
                "sources": result["sources"],
            })

            print(f"  Q: {question[:60]}…  P@{k}={p_at_k:.2f}  F={faith:.2f}  R={relev:.2f}")

        avg_p = sum(prec_scores) / len(prec_scores) if prec_scores else 0
        avg_f = sum(faith_scores) / len(faith_scores) if faith_scores else 0
        avg_r = sum(rel_scores) / len(rel_scores) if rel_scores else 0

        print(f"\n[eval] {strategy} — avg P@{k}={avg_p:.3f}  faithfulness={avg_f:.3f}  relevance={avg_r:.3f}")

        log_rows.append({
            "timestamp": datetime.now().isoformat(),
            "component_changed": "chunking_strategy",
            "parameter_before": "N/A",
            "parameter_after": strategy,
            "metric_before": "N/A",
            "metric_after": f"P@{k}={avg_p:.3f}, F={avg_f:.3f}, R={avg_r:.3f}",
            "observation": f"Strategy '{strategy}' evaluated on {len(qa_data)} QA pairs.",
        })

    # Append to CSV experiment log
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["timestamp", "component_changed", "parameter_before",
                      "parameter_after", "metric_before", "metric_after", "observation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(log_rows)

    print(f"\n[eval] Results appended to {log_path}")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline.")
    parser.add_argument("--qa-file", default="eval/qa_dataset.json")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--log", default="eval/experiment_log.csv")
    args = parser.parse_args()

    run_evaluation(qa_path=args.qa_file, k=args.k, log_path=args.log)
