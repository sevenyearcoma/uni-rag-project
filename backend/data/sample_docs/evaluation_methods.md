---
title: "Evaluation Methods for RAG Pipelines"
date: "2024-03-15"
---

# Evaluation Methods for RAG Pipelines

Evaluating a RAG system requires metrics that probe both the retrieval component and the generation component independently, as well as their interaction.

## Retrieval Metric: Precision@k

Precision@k measures the fraction of the top-k retrieved chunks that are genuinely relevant to the query.

```
Precision@k = |{relevant chunks in top-k}| / k
```

For this pipeline, k=5. A score of 1.0 means all 5 retrieved chunks are relevant; 0.6 means 3 of 5 are relevant.

Ground-truth relevance is defined per query in `qa_dataset.json` as the set of filenames expected to contain the answer.

### Interpreting Precision@5

| Score | Interpretation |
|-------|---------------|
| 1.0   | Perfect retrieval |
| 0.8   | 4/5 relevant — good |
| 0.6   | 3/5 relevant — acceptable |
| < 0.4 | Poor retrieval — inspect embeddings or chunk quality |

## Generation Metric: RAGAS Faithfulness

Faithfulness measures whether every claim in the generated answer is supported by the retrieved context. It is computed by an LLM-as-judge approach: the evaluator LLM is given the context and the answer, and must score support from 0.0 to 1.0.

A faithfulness score of 1.0 means the answer is entirely grounded in the retrieved passages. A score below 0.7 suggests the model is hallucinating or mixing in parametric knowledge.

## Generation Metric: RAGAS Answer Relevance

Answer relevance measures how well the generated answer addresses the question. It penalises answers that:
- Are factually correct but do not answer the specific question asked
- Are redundant or overly verbose
- Omit key information

An LLM-as-judge scores the answer from 0.0 to 1.0 relative to the question.

## Experiment Log

All evaluation runs are logged to `experiment_log.csv` with the following columns:

| Column | Description |
|--------|-------------|
| `timestamp` | ISO 8601 timestamp of the run |
| `component_changed` | Which pipeline component was modified |
| `parameter_before` | Parameter value before the change |
| `parameter_after` | Parameter value after the change |
| `metric_before` | Metric values before the change |
| `metric_after` | Metric values after the change |
| `observation` | Human-readable notes |

This log supports the "Limitations and Failure Modes" section of the technical report by providing empirical evidence of how parameter choices affect pipeline performance.

## QA Dataset

`qa_dataset.json` contains 30 ground-truth question-answer pairs:
- 27 in-context questions with known relevant documents
- 3 out-of-context questions that should trigger the refusal phrase

Each entry specifies the expected answer and the filenames of relevant documents. The evaluator uses the relevant document list to compute Precision@5.

## Running the Evaluation

```bash
cd backend
python -m eval.evaluator --qa-file eval/qa_dataset.json --k 5 --log eval/experiment_log.csv
```

The script runs both chunking strategies against the 30 QA pairs and appends results to the experiment log.
