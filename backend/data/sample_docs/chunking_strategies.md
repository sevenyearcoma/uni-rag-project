---
title: "Chunking Strategies for RAG"
date: "2024-03-10"
---

# Chunking Strategies for RAG

Chunking is the process of splitting documents into smaller segments before embedding and indexing. Chunk quality directly impacts retrieval quality: chunks that are too large dilute relevance; chunks that are too small lose context.

This pipeline implements two strategies.

## Constraints (Applied to Both Strategies)

- **Token size**: 100 to 512 tokens per chunk
- **Overlap**: 10% to 25% of chunk size (repeated between consecutive chunks)
- **Metadata per chunk**: filename, title, date, chunk_index, strategy name, token_count, source_url

## Strategy A: Fixed-Size Overlap Chunking

The simplest and most predictable strategy. The document is tokenised using the `cl100k_base` tokeniser (tiktoken) and split into windows of a fixed token count with a fixed stride.

### Algorithm

```
stride = chunk_size - overlap_tokens
start = 0
while start < len(tokens):
    end = start + chunk_size
    yield tokens[start:end]
    start += stride
```

With `chunk_size=256` and `overlap=0.15`, each chunk is 256 tokens and consecutive chunks share 38 tokens.

### Strengths
- Deterministic: same document always produces the same chunks
- Fast: O(N) in document length
- Predictable embedding distribution

### Weaknesses
- Ignores sentence and paragraph boundaries — a sentence may be split mid-way
- The same sentence can appear in two consecutive chunks with slightly different surrounding context, potentially confusing the retriever

## Strategy B: Recursive Sentence-Aware Chunking

This strategy respects linguistic structure. It first splits the document on paragraph and sentence boundaries, then merges or further splits to meet the token-size constraint.

### Algorithm

1. Split document into paragraphs (on `\n\n`).
2. Split each paragraph into sentences (on `.`, `!`, `?` followed by whitespace).
3. Greedily accumulate sentences into a buffer until `chunk_size` tokens is reached.
4. When the buffer is full, flush it as a chunk.
5. Carry forward the last `overlap_tokens` worth of sentences as the start of the next chunk.
6. If a single sentence exceeds `chunk_size`, split it word-by-word.

### Strengths
- Chunks align with semantic units — sentences are not broken mid-way
- The retriever is more likely to fetch a complete, self-contained thought
- Better RAGAS faithfulness scores in practice

### Weaknesses
- Chunk sizes are variable (within the 100–512 constraint)
- Slower than fixed-size due to sentence tokenisation

## Overlap Rationale

Overlap ensures that context spanning a chunk boundary is represented in both chunks. Without overlap, a sentence split across chunk boundary would be partially retrieved regardless of which chunk is fetched. A 15% overlap (the default) strikes the balance between redundancy and completeness.

## Metadata Attachment

Every chunk carries full document-level metadata plus:
- `chunk_index`: position of the chunk within the document (0-based)
- `strategy`: `"fixed_size"` or `"recursive"` (allows filtering at retrieval time)
- `token_count`: the actual token count of the chunk text

This metadata is stored alongside the vector in ChromaDB and returned with every retrieval result, enabling the UI to display precise source citations.
