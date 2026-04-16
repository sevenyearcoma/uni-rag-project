# 10-Minute Live Demo Checklist

Use this script for the graded live demonstration.

---

## Pre-Demo Setup (5 min before)

- [ ] `cd backend && pip install -r requirements.txt` (if not done)
- [ ] Copy `.env.example` → `.env`, add `ANTHROPIC_API_KEY`
- [ ] `uvicorn main:app --reload` — confirm `/health` returns `{"status":"ok"}`
- [ ] `python ingest_docs.py --dir data/sample_docs --strategy fixed --clear`
- [ ] Confirm `total_vectors > 0` in response
- [ ] `cd ../ui && npm install && npm run dev` — confirm UI loads at `http://localhost:3000`

---

## Demo Script (10 minutes)

### 1. Architecture Walkthrough (2 min)

Walk through the directory structure:
- `/ingest` → loads PDF + Markdown, extracts filename/title/date
- `/retrieval` → two chunking strategies, sentence-transformers embeddings, ChromaDB
- `/generation` → system prompt with 3 hard rules, Anthropic Claude haiku
- `/ui` → Next.js chat interface with live citation rendering
- `/eval` → 30 QA pairs, precision@5, RAGAS metrics, experiment log

### 2. Positive Query 1 — Direct Factual (2 min)

**Ask:** "What is Retrieval-Augmented Generation?"

**Expected:** Grounded answer citing `rag_overview.md`, source badge visible, chunk panel expandable.

**Show:** Click "Show N chunks" → point out cosine similarity scores and chunk_index.

### 3. Positive Query 2 — Architecture (2 min)

**Ask:** "Why is BERT used for retrieval but GPT-style models are used for generation?"

**Expected:** Answer citing `architecture_study.md`, covering bidirectional vs causal attention.

### 4. Positive Query 3 — Cross-Document (1 min)

**Ask:** "What metadata is attached to each chunk and how is it stored in ChromaDB?"

**Expected:** Answer draws from both `chunking_strategies.md` and `vector_databases.md` — demonstrates cross-document retrieval.

### 5. Refusal Test — Out of Context (1 min)

**Ask:** "What is the weather like on Mars?"

**Expected:** Exact phrase: **"I cannot find this in the provided documents"**

Show the amber warning badge in the UI.

### 6. Design Decision Walkthrough (2 min)

- **ChromaDB over FAISS**: metadata filtering, zero-config persistence
- **all-MiniLM-L6-v2**: 384-dim, fast on CPU, cosine-optimised
- **Temperature = 0.0**: deterministic generation for reproducibility
- **Two chunking strategies**: fixed = deterministic, recursive = semantically coherent
- **Strict system prompt**: 3 enforced rules prevent hallucination

---

## Fallback (if API is down)

Run `python query_cli.py` for terminal-based demo without the UI.

---

## Key Numbers to Know

| Metric | Value |
|--------|-------|
| Chunk size | 100–512 tokens |
| Overlap | 10–25% |
| Top-k retrieval | 5 chunks |
| Embedding dim | 384 |
| QA dataset | 30 pairs |
| Supported file types | PDF, Markdown |
