---
title: "GPT-2 vs BERT: Architecture Study for RAG"
date: "2024-03-05"
---

# GPT-2 vs BERT: Architecture Study for RAG

Understanding why different Transformer architectures serve different roles in a RAG pipeline is fundamental to designing an effective system. This document explains the architectural differences between GPT-2 and BERT, and maps them to their respective roles in retrieval and generation.

## Transformer Primer

Both GPT-2 and BERT are Transformer-based models, but they differ in which sub-components they use and how attention is structured.

A standard Transformer has an encoder (processes input bidirectionally) and a decoder (generates output left-to-right, attending causally). GPT-2 uses only the decoder stack. BERT uses only the encoder stack.

## GPT-2 (Decoder-Only, Causal Self-Attention)

GPT-2 is a decoder-only model with 12 to 48 Transformer layers (depending on the variant). Its defining feature is **causal (unidirectional) self-attention**: when processing token at position `t`, the model can only attend to tokens at positions `0` to `t`. Future tokens are masked out.

### Pre-Training Objective: Autoregressive Language Modelling

GPT-2 is pre-trained to predict the next token in a sequence:

```
P(x_t | x_1, x_2, ..., x_{t-1})
```

This objective is computed autoregressively over the entire training corpus. No masking of input tokens is needed — the causal mask naturally prevents look-ahead.

### Why GPT-2 is Natural for RAG Generation

Because GPT-2 was trained to continue a sequence, it excels at *generating* text conditioned on a prefix. In RAG, the prefix is: `[system prompt] + [retrieved context chunks] + [user query]`. GPT-2's causal attention ensures the generated answer attends to all retrieved context while producing tokens left-to-right — exactly the generation pattern RAG requires.

A GPT-style model used in production RAG (e.g., Claude, GPT-4) applies the same causal generation principle at much greater scale.

## BERT (Encoder-Only, Bidirectional Self-Attention)

BERT (Bidirectional Encoder Representations from Transformers) uses only the encoder stack. Its self-attention is **fully bidirectional**: every token can attend to every other token in the sequence simultaneously.

### Pre-Training Objectives

BERT is pre-trained on two tasks:

1. **Masked Language Modelling (MLM)**: 15% of input tokens are randomly replaced with a `[MASK]` token. The model must predict the original token using both left and right context. This forces the model to develop rich, context-sensitive representations.

2. **Next-Sentence Prediction (NSP)**: The model is given pairs of sentences and must predict whether the second sentence follows the first in the original document. This trains inter-sentence coherence understanding.

### Why BERT is Natural for Retrieval Embeddings

Because every token attends to every other token, BERT produces embeddings that capture the full bidirectional context of a sentence. Fine-tuning on semantic similarity tasks (as done in `sentence-transformers`) yields embeddings where semantically similar sentences cluster together in vector space.

The `all-MiniLM-L6-v2` model is a distilled, fine-tuned BERT derivative that produces 384-dimensional sentence embeddings optimised for cosine similarity — 6x faster than full BERT with comparable quality.

### The Complementarity Principle

| Property            | BERT (Encoder)         | GPT-2 (Decoder)        |
|---------------------|------------------------|------------------------|
| Attention           | Bidirectional          | Causal (left-to-right) |
| Pre-training        | MLM + NSP              | Autoregressive LM      |
| Output              | Fixed-size embeddings  | Variable-length text   |
| RAG Role            | **Retrieval**          | **Generation**         |
| Why ideal           | Semantically rich vecs | Conditioned text gen   |

RAG exploits this complementarity: the encoder **understands** and **retrieves**; the decoder **generates** a grounded answer.

## all-MiniLM-L6-v2

This is the default embedding model in this pipeline. Key properties:
- Architecture: 6-layer MiniLM distilled from a larger BERT model
- Embedding dimension: 384
- Max sequence length: 256 tokens
- Training: fine-tuned on 1 billion sentence pairs for semantic similarity
- Speed: ~14,000 sentences/second on CPU

It balances speed and quality, making it suitable for real-time retrieval in a RAG system.
