# RAG Chatbot Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline built from scratch. The system ingests documents, chunks them with two strategies, embeds them into a FAISS vector store, retrieves top-5 contexts, and generates strictly grounded, cited answers via an LLM API.

---

## Architecture

```
Documents (PDF / Markdown)
        │
        ▼
  ┌─────────────┐
  │   /ingest   │  Loads files, extracts filename · title · date
  └──────┬──────┘
         │ Document objects
         ▼
  ┌─────────────┐
  │ /retrieval  │  Strategy A: fixed-size overlap
  │  chunker    │  Strategy B: recursive sentence-aware
  └──────┬──────┘
         │ Chunks (text + metadata + chunk_index)
         ▼
  ┌─────────────┐
  │  embedder   │  all-MiniLM-L6-v2  →  384-dim L2-normalised vectors
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ FAISS index │  IndexFlatIP (inner-product = cosine for unit vecs)
  └──────┬──────┘
         │  top-5 chunks (cosine similarity)
         ▼
  ┌──────────────┐
  │ /generation  │  System prompt: cite sources · context-only · refusal
  │   LLM API   │  Provider: Anthropic (claude-haiku) or OpenAI
  └──────┬───────┘
         │  Grounded, cited answer
         ▼
  ┌──────┐
  │  /ui │  Next.js chat interface with expandable citation panel
  └──────┘
```

---

## Directory Structure

```
├── backend/
│   ├── ingest/
│   │   └── loader.py          # PDF + Markdown parser, metadata extraction
│   ├── retrieval/
│   │   ├── chunker.py         # Strategy A (fixed) + Strategy B (recursive)
│   │   ├── embedder.py        # sentence-transformers wrapper
│   │   └── vector_store.py    # FAISS index + JSON metadata sidecar
│   ├── generation/
│   │   ├── prompts.py         # Grounding system prompt + context formatter
│   │   └── llm.py             # Anthropic / OpenAI provider switch
│   ├── eval/
│   │   ├── evaluator.py       # precision@5, RAGAS faithfulness & relevance
│   │   ├── qa_dataset.json    # 30 ground-truth QA pairs
│   │   └── experiment_log.csv # Experiment results table
│   ├── data/
│   │   └── sample_docs/       # Sample PDF / Markdown knowledge base
│   ├── gpt2_sandbox.py        # HuggingFace GPT-2 generation behaviour demo
│   ├── main.py                # FastAPI server (POST /ingest, POST /query …)
│   ├── ingest_docs.py         # CLI helper: ingest a directory
│   ├── query_cli.py           # Terminal-based query interface
│   ├── run_experiments.py     # Automated 5-experiment evaluation suite
│   └── requirements.txt
└── ui/
    ├── app/
    │   ├── page.tsx            # Chat page
    │   └── api/chat/route.ts   # Server-side proxy to Python backend
    ├── components/
    │   ├── ChatInterface.tsx   # Input bar + message list
    │   ├── ChatBubble.tsx      # Message rendering + refusal badge
    │   └── Citations.tsx       # Expandable source citation panel
    └── lib/
        ├── api.ts              # Typed fetch wrappers
        └── types.ts            # Shared TypeScript interfaces
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | If using Anthropic | — | `sk-ant-...` |
| `OPENAI_API_KEY` | If using OpenAI | — | `sk-...` |
| `LLM_PROVIDER` | No | `anthropic` | `anthropic` or `openai` |
| `ANTHROPIC_MODEL` | No | `claude-haiku-4-5-20251001` | Claude model ID |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model ID |
| `LLM_MAX_TOKENS` | No | `1024` | Max tokens in response |
| `LLM_TEMPERATURE` | No | `0.0` | 0 = deterministic |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | sentence-transformers model |
| `FAISS_PERSIST_DIR` | No | `./faiss_db` | Where vectors are stored |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed UI origins |

Copy `ui/.env.local.example` to `ui/.env.local`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | Python backend (server-side) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Python backend (browser) |

---

## Setup & Running

### 1. Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

### 2. Start the API server

```bash
cd backend
uvicorn main:app --reload
# API docs at http://localhost:8000/docs
```

### 3. Ingest documents

```bash
# Ingest sample docs with fixed-size chunking (Strategy A)
python ingest_docs.py --dir data/sample_docs --strategy fixed --clear

# Or with recursive chunking (Strategy B)
python ingest_docs.py --dir data/sample_docs --strategy recursive --clear
```

### 4. Frontend

```bash
cd ui
npm install
cp .env.local.example .env.local
npm run dev
# UI at http://localhost:3000
```

### 5. Terminal query (no browser needed)

```bash
cd backend
python query_cli.py
```

---

## Evaluation

### Run full evaluation suite (both strategies, all 30 QA pairs)

```bash
cd backend
python -m eval.evaluator --qa-file eval/qa_dataset.json --k 5
```

### Run automated 5-experiment comparison

```bash
python run_experiments.py
```

Results are appended to `eval/experiment_log.csv`.

---

## Sample Documents

The corpus lives in `backend/data/sample_docs/` and contains **6 documents** across both supported file types:

| File | Type | Topic |
|------|------|-------|
| `rag_overview.md` | Markdown | RAG pipeline concepts, grounding, cross-document retrieval |
| `architecture_study.md` | Markdown | GPT-2 vs BERT, all-MiniLM-L6-v2, attention types |
| `chunking_strategies.md` | Markdown | Fixed-size and recursive chunking, overlap rationale |
| `vector_databases.md` | Markdown | ChromaDB vs FAISS, cosine similarity, ANN indexing |
| `evaluation_methods.md` | Markdown | Precision@k, RAGAS metrics, experiment log format |
| `transformer_scaling.pdf` | **PDF** | Scaling laws, Chinchilla, GQA, Flash Attention, RLHF, DPO |

---

## Test Questions

Use these after ingesting the sample docs (`python ingest_docs.py --dir data/sample_docs`).

### Questions answered from the Markdown docs

```
What is Retrieval-Augmented Generation?
Why is BERT used for retrieval but not generation?
What are the two chunking strategies and how do they differ?
What metadata is attached to every chunk?
What is the exact refusal phrase when a question is out of context?
What does precision@5 measure?
Why was FAISS chosen over ChromaDB?
```

### Questions answered from the PDF (transformer_scaling.pdf)

```
What is the Chinchilla scaling law?
What is the optimal ratio of training tokens to model parameters according to Chinchilla?
What is Grouped Query Attention and which models use it?
How does Flash Attention reduce memory usage?
What is the difference between RLHF and DPO?
What is the "lost in the middle" problem in long-context models?
How many parameters does GPT-3 have and how many tokens was it trained on?
What positional encoding method do Llama and Mistral use?
```

### Cross-document questions (should pull from both PDF and Markdown)

```
How do the attention mechanisms used in BERT and in GQA compare?
What does instruction tuning have to do with RAG grounding?
Why does context window length matter for RAG, and what is the lost-in-the-middle problem?
```

### Refusal trigger (should return exact refusal phrase)

```
What is the weather like on Mars?
Who won the 2026 FIFA World Cup?
What is the capital of Australia?
```

---

## GPT-2 Sandbox

```bash
cd backend
pip install transformers torch   # if not already installed
python gpt2_sandbox.py
```

Demonstrates causal vs bidirectional self-attention, greedy decoding, and temperature sampling.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + vector count |
| `GET` | `/stats` | Embedding model, vector count, persist dir |
| `POST` | `/ingest` | Load + chunk + index documents |
| `POST` | `/query` | Query the pipeline, returns answer + citations |
| `DELETE` | `/index` | Clear the vector store |

### POST /ingest

```json
{
  "directory": "./data/sample_docs",
  "strategy": "fixed",
  "chunk_size": 256,
  "overlap": 0.15,
  "clear_first": false
}
```

### POST /query

```json
{
  "query": "What is Retrieval-Augmented Generation?",
  "k": 5
}
```

Response includes `answer`, `sources` (list of filenames), `chunks` (with metadata + scores), `provider`, and `model`.
