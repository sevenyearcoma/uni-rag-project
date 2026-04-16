---
title: "Retrieval-Augmented Generation: An Overview"
date: "2024-03-01"
---

# Retrieval-Augmented Generation: An Overview

Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with language model generation to produce grounded, verifiable answers. Instead of relying solely on a model's parametric memory, RAG retrieves relevant passages from a document corpus at inference time and feeds them as context to the generator.

## Why RAG?

Large language models (LLMs) are prone to hallucination — generating plausible-sounding but factually incorrect text. RAG mitigates this by anchoring the generator to a retrieved context window. Every claim in the output can be traced back to a specific source chunk.

A secondary benefit is freshness: the knowledge base can be updated without retraining the model. New documents are ingested, chunked, embedded, and stored, immediately becoming retrievable.

## Pipeline Overview

The RAG pipeline has four main stages:

1. **Ingestion** — Raw documents (PDF, Markdown, HTML) are loaded. Metadata is extracted: filename/URL, title, and date. Documents are stored for downstream chunking.

2. **Chunking & Embedding** — Each document is split into overlapping text chunks (100–512 tokens, 10–25% overlap). Each chunk is encoded into a dense vector using a sentence-transformer model (e.g., `all-MiniLM-L6-v2`).

3. **Retrieval** — At query time, the user's question is embedded using the same encoder. The top-5 most similar chunks are retrieved from the vector database using cosine similarity or approximate nearest neighbour (ANN) search.

4. **Generation** — The retrieved chunks, together with the query, are passed to an LLM. A strict system prompt enforces grounding: the model must cite the source document by filename for every factual claim and must refuse with the exact phrase "I cannot find this in the provided documents" when the answer is absent from context.

## Cross-Document Retrieval

Because all chunks from all documents share the same embedding space, retrieval is naturally cross-document. A single query can surface relevant passages from a PDF, a Markdown file, and a web-scraped article simultaneously. Each retrieved chunk carries its originating document's metadata (filename, title, date, chunk_index), enabling precise citation.

## Grounding and Citation

The generation system prompt enforces three hard rules:
1. Answer only using the provided context passages.
2. Cite the source document name (filename) after every factual claim: `(Source: filename.pdf)`.
3. If the answer cannot be found, respond with exactly: "I cannot find this in the provided documents".

This makes the system's knowledge boundaries transparent and auditable.

## Temperature and Determinism

The LLM is called with temperature = 0.0 for grounded QA tasks. This maximises determinism: given the same query and retrieved context, the model always produces the same answer — crucial for reproducibility in evaluation.
