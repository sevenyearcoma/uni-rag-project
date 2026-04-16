"""
GPT-2 Sandbox Script
====================
Loads GPT-2 from HuggingFace Transformers and demonstrates its generation
behaviour — as required by the project specification.

This script illustrates:
  1. Why GPT-2 (decoder-only, causal self-attention) is a natural fit for the
     *generative* component of RAG.
  2. How autoregressive generation works step-by-step.
  3. The contrast with BERT-style encoders used for retrieval.

Run::
    pip install transformers torch
    python gpt2_sandbox.py
"""
from __future__ import annotations

import textwrap
import time

print("=" * 60)
print("  GPT-2 Sandbox — Generation Behaviour Demo")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. Load GPT-2 from HuggingFace
# ---------------------------------------------------------------------------
print("\n[1/5] Loading GPT-2 tokeniser and model from HuggingFace…")
t0 = time.time()

from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
model.eval()

print(f"      Model loaded in {time.time() - t0:.1f}s")
print(f"      Parameters: {sum(p.numel() for p in model.parameters()):,}")
print(f"      Architecture: {model.config.model_type.upper()} — decoder-only Transformer")
print(f"      Layers: {model.config.n_layer} | Heads: {model.config.n_head} | d_model: {model.config.n_embd}")

# ---------------------------------------------------------------------------
# 2. Demonstrate causal (unidirectional) self-attention
# ---------------------------------------------------------------------------
print("\n[2/5] Inspecting causal self-attention mask…")
prompt = "Retrieval-Augmented Generation works by"
inputs = tokenizer(prompt, return_tensors="pt")
n_tokens = inputs["input_ids"].shape[1]
print(f"      Prompt: '{prompt}'")
print(f"      Tokens: {n_tokens}")
print(f"      Each token attends ONLY to itself and prior tokens (causal mask).")
print(f"      This prevents future-token look-ahead — the core of autoregression.")

# ---------------------------------------------------------------------------
# 3. Greedy decoding — one token at a time
# ---------------------------------------------------------------------------
print("\n[3/5] Running greedy decoding (temperature=1.0, deterministic)…")
with torch.no_grad():
    greedy_ids = model.generate(
        inputs["input_ids"],
        max_new_tokens=40,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
greedy_text = tokenizer.decode(greedy_ids[0], skip_special_tokens=True)
print(f"      Output:\n{textwrap.fill(greedy_text, width=72, initial_indent='      ')}")

# ---------------------------------------------------------------------------
# 4. Temperature sampling — stochastic generation
# ---------------------------------------------------------------------------
print("\n[4/5] Running temperature sampling (temperature=0.7)…")
with torch.no_grad():
    sample_ids = model.generate(
        inputs["input_ids"],
        max_new_tokens=40,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id,
    )
sample_text = tokenizer.decode(sample_ids[0], skip_special_tokens=True)
print(f"      Output:\n{textwrap.fill(sample_text, width=72, initial_indent='      ')}")

# ---------------------------------------------------------------------------
# 5. Architecture contrast summary
# ---------------------------------------------------------------------------
print("\n[5/5] Architecture Summary — GPT-2 vs BERT for RAG")
print("-" * 60)
summary = """\
GPT-2 (Decoder-only, Causal Self-Attention):
  • Pre-trained on autoregressive language modelling (predict next token).
  • Each token attends only to PAST tokens — no bidirectional context.
  • Natural fit for GENERATION: produces fluent continuations given a prompt.
  • In RAG: takes "context chunks + query" as a prompt and generates an answer.

BERT / sentence-transformers (Encoder-only, Bidirectional Self-Attention):
  • Pre-trained on Masked Language Modelling (MLM) and Next-Sentence Prediction.
  • Every token attends to ALL other tokens — full bidirectional context.
  • Produces rich contextual embeddings where similar meanings cluster together.
  • Natural fit for RETRIEVAL: embed query and documents, compare with cosine similarity.
  • In RAG: sentence-transformer derivatives (all-MiniLM-L6-v2) generate the dense
    vectors stored in ChromaDB and used to find top-k relevant chunks.

Conclusion:
  GPT-2-style decoders generate; BERT-style encoders understand and retrieve.
  RAG exploits this complementarity: retrieve with BERT → generate with GPT.
"""
for line in summary.strip().split("\n"):
    print(f"  {line}")

print("\n" + "=" * 60)
print("  Sandbox complete.")
print("=" * 60)
