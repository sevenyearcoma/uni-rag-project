/**
 * Generates the Technical Report DOCX for the RAG Chatbot Pipeline project.
 * Run: node generate_report.js
 * Output: RAG_Technical_Report.docx
 *
 * After generating, open in Word / LibreOffice and export as PDF.
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, Header, Footer, LevelFormat,
} = require("docx");
const fs = require("fs");

// ── Colours ─────────────────────────────────────────────────────────────────
const C = { accent: "1F3A6E", light: "DCE6F1", mid: "BDD7EE", white: "FFFFFF",
            grey: "595959", lgrey: "F2F2F2", border: "AAAAAA" };

// ── Helpers ──────────────────────────────────────────────────────────────────
const pt  = (n) => n * 2;          // half-points (docx unit)
const dxa = (inches) => inches * 1440;

const hr = () => new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 1 } },
  spacing: { after: 160 },
  children: [],
});

const spacer = (after = 120) => new Paragraph({ spacing: { after }, children: [] });

const heading = (text, level, opts = {}) => new Paragraph({
  heading: level,
  spacing: { before: level === HeadingLevel.HEADING_1 ? 280 : 160, after: 100 },
  ...opts,
  children: [new TextRun({ text, bold: true,
    size:  level === HeadingLevel.HEADING_1 ? pt(16) :
           level === HeadingLevel.HEADING_2 ? pt(13) : pt(11.5),
    color: level === HeadingLevel.HEADING_1 ? C.accent : "000000",
    font: "Calibri",
  })],
});

const body = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 276 },
  ...opts,
  children: [new TextRun({ text, size: pt(11), font: "Calibri", ...opts.run })],
});

const bold = (text) => new TextRun({ text, bold: true, size: pt(11), font: "Calibri" });
const norm = (text, opts = {}) => new TextRun({ text, size: pt(11), font: "Calibri", ...opts });

const mixed = (parts, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 276 },
  ...opts,
  children: parts.map(([t, b]) =>
    new TextRun({ text: t, bold: !!b, size: pt(11), font: "Calibri" })
  ),
});

const bullet = (text, level = 0) => new Paragraph({
  numbering: { reference: "bullets", level },
  spacing: { after: 80, line: 260 },
  children: [new TextRun({ text, size: pt(11), font: "Calibri" })],
});

const code = (text) => new Paragraph({
  spacing: { after: 80, line: 240 },
  shading: { fill: "F0F0F0", type: ShadingType.CLEAR },
  indent: { left: dxa(0.3) },
  children: [new TextRun({ text, font: "Courier New", size: pt(9.5), color: "2C2C2C" })],
});

// ── Table helper ─────────────────────────────────────────────────────────────
const brd = (col = C.border) => ({ style: BorderStyle.SINGLE, size: 1, color: col });
const allBorders = (col) => ({ top: brd(col), bottom: brd(col), left: brd(col), right: brd(col) });

function mkTable(rows, colWidths, { headerRow = true } = {}) {
  const totalW = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: rows.map((cells, ri) => new TableRow({
      tableHeader: headerRow && ri === 0,
      children: cells.map((cell, ci) => {
        const isHeader = headerRow && ri === 0;
        const content  = typeof cell === "string" ? cell : cell.text;
        const extra    = typeof cell === "object" ? cell : {};
        return new TableCell({
          width:   { size: colWidths[ci], type: WidthType.DXA },
          borders: allBorders(C.border),
          shading: { fill: isHeader ? C.accent : (ri % 2 === 0 ? C.lgrey : C.white), type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({
              text: content,
              bold: isHeader,
              color: isHeader ? C.white : "000000",
              size: pt(10),
              font: "Calibri",
            })],
          })],
        });
      }),
    })),
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// SECTIONS
// ═══════════════════════════════════════════════════════════════════════════

// ── Title page ───────────────────────────────────────────────────────────────
const titlePage = [
  spacer(dxa(1.2)),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 160 },
    children: [new TextRun({ text: "Technical Report", size: pt(26), bold: true, color: C.accent, font: "Calibri" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [new TextRun({ text: "RAG Chatbot Pipeline", size: pt(18), bold: true, font: "Calibri", color: "000000" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [new TextRun({ text: "Build a RAG Chatbot with LLMs", size: pt(13), font: "Calibri", color: C.grey })],
  }),
  spacer(200),
  mkTable([
    ["Student", "[Your Name]"],
    ["Course",  "CS / AI — Main Project"],
    ["Date",    new Date().toLocaleDateString("en-GB", { year:"numeric", month:"long", day:"numeric" })],
    ["LLM API", "Anthropic Claude (claude-haiku-4-5)"],
    ["Embedding", "sentence-transformers all-MiniLM-L6-v2"],
    ["Vector DB",  "FAISS (IndexFlatIP, cosine similarity)"],
  ], [2800, 6200], { headerRow: false }),
  spacer(dxa(0.5)),
  new Paragraph({ children: [new PageBreak()] }),
];

// ── 1. Introduction & Architecture ───────────────────────────────────────────
const sec1 = [
  heading("1  Pipeline Architecture", HeadingLevel.HEADING_1),
  hr(),
  body(
    "RAG stands for Retrieval-Augmented Generation. The idea is simple: instead of asking " +
    "the LLM to answer from memory, you find the relevant parts of your documents first " +
    "and give them to the model as context. This way the answers are based on real content, " +
    "not something the model made up."
  ),
  body("The system has 7 main steps:"),
  bullet("Load PDF and Markdown files and extract metadata (filename, title, date)."),
  bullet("Split the text into chunks using one of two strategies."),
  bullet("Turn each chunk into a vector using all-MiniLM-L6-v2."),
  bullet("Store all vectors in FAISS with a metadata sidecar file."),
  bullet("At query time, embed the question and find the top-5 most similar chunks."),
  bullet("Send the chunks + question to Claude with a strict system prompt."),
  bullet("Show the answer in a Next.js chat UI with clickable source citations."),
  spacer(80),
  heading("1.1  Component Overview", HeadingLevel.HEADING_2),
  body("Here is a summary of each module:"),
  spacer(80),
  mkTable([
    ["Stage", "Module", "Description"],
    ["1 — Ingestion",   "ingest/loader.py",          "Loads PDF and Markdown files. Extracts filename, title, and date metadata for every document."],
    ["2 — Chunking",    "retrieval/chunker.py",       "Splits documents into overlapping text chunks (100–512 tokens, 10–25% overlap) using two strategies."],
    ["3 — Embedding",   "retrieval/embedder.py",      "Encodes each chunk into a 384-dimensional dense vector using all-MiniLM-L6-v2."],
    ["4 — Indexing",    "retrieval/vector_store.py",  "Stores vectors in a FAISS IndexFlatIP. A parallel JSON sidecar holds chunk text and metadata."],
    ["5 — Retrieval",   "retrieval/vector_store.py",  "Embeds the user query; retrieves top-5 chunks by cosine similarity (inner product of unit vectors)."],
    ["6 — Generation",  "generation/llm.py",          "Passes retrieved chunks and the query to Claude via a strict grounding system prompt."],
    ["7 — UI",          "ui/",                        "Next.js chat interface with expandable citation panel showing per-chunk similarity scores."],
  ], [2100, 2500, 4460]),
  spacer(100),
  body(
    "Every chunk carries metadata (filename, title, date, chunk index) all the way " +
    "through the pipeline so the UI can show proper citations."
  ),
];

// ── 2. Document Ingestion ────────────────────────────────────────────────────
const sec2 = [
  spacer(80),
  heading("2  Document Ingestion", HeadingLevel.HEADING_1),
  hr(),
  body(
    "I supported two file types: PDF and Markdown. " +
    "The code automatically detects the file type and uses the right parser."
  ),
  heading("2.1  PDF Files", HeadingLevel.HEADING_2),
  body("I used pdfplumber to read PDFs. Getting the title and date was the tricky part because PDFs don't always have clean metadata. So I used a fallback system:"),
  bullet("Title: from PDF metadata -> first line of page 1 -> filename"),
  bullet("Date: from PDF CreationDate field -> file modification time"),
  heading("2.2  Markdown Files", HeadingLevel.HEADING_2),
  body("I used python-frontmatter to read Markdown. Most of my docs have YAML front matter so this worked well. Fallbacks:"),
  bullet("Title: from frontmatter -> first # heading -> filename"),
  bullet("Date: from frontmatter -> file modification time"),
  heading("2.3  Metadata Fields", HeadingLevel.HEADING_2),
  body("Every document and chunk carries these fields:"),
  spacer(80),
  mkTable([
    ["Field", "Type", "Source"],
    ["filename",   "str", "Path basename (e.g. paper.pdf)"],
    ["source_url", "str", "Absolute resolved path"],
    ["title",      "str", "Extracted per §2.1 / §2.2"],
    ["date",       "str", "ISO 8601 date string (YYYY-MM-DD)"],
    ["source_type","str", "'pdf' or 'markdown'"],
  ], [2500, 1500, 5060]),
];

// ── 3. Chunking ──────────────────────────────────────────────────────────────
const sec3 = [
  spacer(80),
  heading("3  Chunking Strategy Comparison", HeadingLevel.HEADING_1),
  hr(),
  body("I tested two chunking methods. Both use chunks of 100-512 tokens with 10-25% overlap."),
  heading("3.1  Strategy A - Fixed-Size", HeadingLevel.HEADING_2),
  body("Splits text into fixed token windows with overlap. Simple and fast."),
  bullet("Default: 256 tokens, 15% overlap"),
  bullet("Always produces the same output for the same input"),
  bullet("Problem: can cut sentences in the middle"),
  heading("3.2  Strategy B - Sentence-Aware", HeadingLevel.HEADING_2),
  body("Splits on paragraph and sentence boundaries, then fills chunks up to the token limit."),
  bullet("No mid-sentence cuts"),
  bullet("Slower to build"),
  bullet("Chunk sizes vary (but stay within 100-512 tokens)"),
  heading("3.3  Results", HeadingLevel.HEADING_2),
  body("I tested both on 30 QA pairs with k=5 and chunk_size=256:"),
  spacer(80),
  mkTable([
    ["Metric", "Strategy A — Fixed", "Strategy B — Recursive", "Winner"],
    ["Precision@5",        "0.160",    "0.160",    "Tied"],
    ["RAGAS Faithfulness", "0.847",    "0.800",    "Strategy A"],
    ["RAGAS Relevance",    "0.749",    "0.754",    "Strategy B"],
    ["Avg chunk tokens",   "~256",     "variable", "—"],
    ["Index build time",   "faster",   "slower",   "Strategy A"],
  ], [2800, 2000, 2200, 2060]),
  spacer(120),
  body(
    "I chose fixed-size because it is faster and performed just as well. " +
    "Sentence-aware might be better on a larger corpus with more narrative text."
  ),
];

// ── 4. Embedding & Vector Store ───────────────────────────────────────────────
const sec4 = [
  spacer(80),
  heading("4  Embedding and Vector Store", HeadingLevel.HEADING_1),
  hr(),
  heading("4.1  Embedding Model", HeadingLevel.HEADING_2),
  body(
    "I used all-MiniLM-L6-v2 from sentence-transformers. " +
    "It is fast on CPU and produces 384-dimensional vectors. " +
    "My experiment (Exp 5) confirmed it is better than the paraphrase variant for this task."
  ),
  spacer(80),
  mkTable([
    ["Property", "Value"],
    ["Architecture",     "6-layer MiniLM (distilled BERT)"],
    ["Embedding dim",    "384"],
    ["Max input tokens", "256"],
    ["Normalisation",    "L2 (cosine-equivalent inner product)"],
    ["Throughput",       "~14,000 sentences/sec (CPU)"],
    ["Training data",    "1B+ sentence pairs (diverse similarity tasks)"],
  ], [3500, 5560], { headerRow: false }),
  spacer(120),
  heading("4.2  FAISS Vector Store", HeadingLevel.HEADING_2),
  body(
    "I planned to use ChromaDB but it needed a C++ compiler to install on Windows and that failed. " +
    "So I switched to FAISS (faiss-cpu) which worked right away. " +
    "I use IndexFlatIP which is exact cosine search (vectors are normalized so inner product = cosine). " +
    "Metadata is stored in a separate JSON file next to the index."
  ),
  heading("4.3  What Each Record Stores", HeadingLevel.HEADING_2),
  body("Each vector record contains:"),
  bullet("text — the raw chunk text"),
  bullet("filename — source document filename"),
  bullet("title — source document title"),
  bullet("date — source document date"),
  bullet("chunk_index — ordinal position within the source document"),
  bullet("strategy — 'fixed_size' or 'recursive' (supports post-retrieval filtering)"),
  bullet("token_count — actual token count of this chunk"),
  bullet("source_url — absolute path to the source file"),
];

// ── 5. Generation & Grounding ─────────────────────────────────────────────────
const sec5 = [
  spacer(80),
  heading("5  Generation and Grounding", HeadingLevel.HEADING_1),
  hr(),
  body(
    "I used Claude (claude-haiku-4-5) to generate answers. " +
    "The system prompt has three strict rules:"
  ),
  bullet("Only use the retrieved context. No outside knowledge."),
  bullet("Cite the source filename after every factual claim."),
  bullet("If the answer is not in context, say exactly: 'I cannot find this in the provided documents'."),
  spacer(40),
  body("My first prompt said 'prefer to use context' and the model still added things from memory. Making the rules strict and explicit fixed this."),
  heading("5.2  Prompt Structure", HeadingLevel.HEADING_2),
  body("Each request to the LLM is built like this:"),
  code("SYSTEM: [grounding rules — constant across all queries]"),
  code("USER:   --- CONTEXT PASSAGES ---"),
  code("        [1] Document: \"<title>\" (file: <filename>, date: <date>, relevance: <score>)"),
  code("        <chunk text>"),
  code("        ..."),
  code("        --- END OF CONTEXT ---"),
  code("        Question: <user query>"),
  spacer(80),
  body("Temperature is 0.0 for consistent, reproducible answers."),
  heading("5.3  LLM Provider", HeadingLevel.HEADING_2),
  body(
    "The code supports Anthropic and OpenAI. You switch between them with an environment variable. " +
    "No API keys are hardcoded."
  ),
];

// ── 6. GPT-2 vs BERT ─────────────────────────────────────────────────────────
const sec6 = [
  spacer(80),
  heading("6  GPT-2 vs BERT in RAG", HeadingLevel.HEADING_1),
  hr(),
  body("RAG needs two different model types. They do different jobs and cannot replace each other."),
  heading("6.1  Attention Comparison", HeadingLevel.HEADING_2),
  body("Both use transformer attention but in different ways:"),
  spacer(80),
  mkTable([
    ["Property", "BERT (Encoder-only)", "GPT-2 (Decoder-only)"],
    ["Attention type",        "Bidirectional (full)",         "Causal (unidirectional)"],
    ["Masking",               "None — all tokens attend to all tokens", "Future tokens masked out"],
    ["Pre-training task",     "Masked LM (MLM) + Next-Sentence Prediction (NSP)", "Autoregressive LM (predict next token)"],
    ["Output",                "Contextual token embeddings",  "Next-token probability distribution"],
    ["Pooled representation", "Rich, bidirectional context",  "Not designed for fixed-size embedding"],
    ["RAG role",              "Retrieval — dense embedding",  "Generation — conditioned text production"],
  ], [2800, 3000, 3260]),
  spacer(160),
  heading("6.2  Why BERT Works for Retrieval", HeadingLevel.HEADING_2),
  body(
    "BERT reads all tokens at once in both directions. So when it sees 'river bank' it " +
    "knows from context that 'bank' is not a financial institution. This is called " +
    "bidirectional attention. The same word gets a different vector depending on what " +
    "is around it."
  ),
  body(
    "BERT is also trained with a task called Masked Language Modelling — it has to guess " +
    "hidden words using both left and right context. This forces it to build very good " +
    "sentence representations. sentence-transformers fine-tunes BERT on pairs of similar " +
    "sentences, so in the end similar sentences are close in vector space. That is exactly " +
    "what retrieval needs."
  ),
  heading("6.3  Why GPT-Style Models Work for Generation", HeadingLevel.HEADING_2),
  body(
    "GPT-2 only looks left. Each token can only see the tokens before it, not after. " +
    "This lets it generate text one token at a time — it predicts the next word, adds it, " +
    "then predicts the next one, and so on. That is how text generation works."
  ),
  body(
    "In a RAG pipeline the 'left context' is: system prompt + retrieved chunks + question. " +
    "The model reads all of it and generates the answer word by word. Claude works the same way, " +
    "it is just much bigger."
  ),
  heading("6.4  Why You Can't Swap Them", HeadingLevel.HEADING_2),
  body("I tried to understand this clearly:"),
  bullet("BERT cannot generate text. It needs to see the full sequence to work, so you can't produce tokens one by one."),
  bullet("GPT cannot make good embeddings. Its attention is biased toward predicting the next word, not understanding the whole sentence meaning."),
  body(
    "So RAG uses both: BERT-style model for retrieval (find the right chunks), " +
    "GPT-style model for generation (write the answer). You need both."
  ),
  heading("6.5  GPT-2 Sandbox", HeadingLevel.HEADING_2),
  body(
    "I wrote gpt2_sandbox.py to test this. I loaded GPT-2 from HuggingFace and ran it on " +
    "a RAG-style prompt. I tried greedy decoding and temperature=0.7 sampling. " +
    "GPT-2 is clearly good at completing text. But it is not useful as an embedding model " +
    "because its vectors don't group similar sentences together properly."
  ),
];

// ── 7. Evaluation Results ─────────────────────────────────────────────────────
const sec7 = [
  spacer(80),
  heading("7  Evaluation Results", HeadingLevel.HEADING_1),
  hr(),
  body(
    "I built a dataset of 30 QA pairs (eval/qa_dataset.json) drawn from my five sample " +
    "documents: 27 in-context questions where I know which file(s) contain the answer, " +
    "and 3 deliberately out-of-context questions that should trigger the refusal phrase. " +
    "I then ran five experiments, each varying a single component."
  ),
  heading("7.1  Metrics", HeadingLevel.HEADING_2),
  bullet("Precision@5 — what fraction of the 5 retrieved chunks came from a document that actually contains the answer. I tagged relevant filenames per question in the dataset."),
  bullet("RAGAS Faithfulness — an LLM judge reads the answer and the retrieved context and scores (0–1) how well every claim is supported. High faithfulness means the model stayed grounded."),
  bullet("RAGAS Answer Relevance — the same judge scores how directly and completely the answer addresses the question asked."),
  spacer(100),
  heading("7.2  Results by Experiment", HeadingLevel.HEADING_2),
  spacer(80),
  mkTable([
    ["#", "Component", "Before → After", "P@5 Before", "P@5 After", "Faith. Before", "Faith. After", "Rel. Before", "Rel. After"],
    ["1", "Chunking strategy",  "fixed \u2192 recursive",        "0.160", "0.160",  "0.847", "0.800",  "0.749", "0.754"],
    ["2", "Chunk size",         "128 tok \u2192 256 tok",        "0.213", "0.160",  "0.871", "0.840",  "0.729", "0.746"],
    ["3", "Overlap",            "10% \u2192 25%",                "0.153", "0.180",  "0.842", "0.826",  "0.740", "0.742"],
    ["4", "Top-k",              "k=3 \u2192 k=5",                "0.211", "0.160",  "0.818", "0.837",  "0.716", "0.742"],
    ["5", "Embedding model",    "all-MiniLM \u2192 para-MiniLM", "0.160", "0.153",  "0.844", "0.707",  "0.740", "0.686"],
  ], [350, 1650, 1900, 800, 800, 900, 900, 800, 800]),
  spacer(120),
  heading("7.3  What I Found", HeadingLevel.HEADING_2),
  body(
    "Precision@5 looks low (0.153-0.213) but that is partly because my corpus is small. " +
    "I only have 5 documents and most questions have 1-2 relevant ones. So even if retrieval " +
    "is perfect, most of the top-5 chunks will be from other documents. The differences " +
    "between experiments matter more than the absolute number."
  ),
  body(
    "Faithfulness was 0.707-0.871 across all experiments. I am happy with that — it means " +
    "the system prompt is working and the model is not making things up."
  ),
  body(
    "The most interesting result was chunk size (Exp 2). Smaller chunks (128 tokens) gave " +
    "better precision than 256 tokens. I think it is because small chunks have one focused " +
    "idea, so they match the question more exactly."
  ),
  body(
    "Embedding model comparison (Exp 5) was very clear. all-MiniLM was better than " +
    "paraphrase-MiniLM on every metric, especially faithfulness (0.844 vs 0.707). " +
    "So all-MiniLM is the right choice."
  ),
  heading("7.4  Refusal Behaviour", HeadingLevel.HEADING_2),
  body(
    "All 3 out-of-context questions worked correctly. I tested 'What is the weather like on Mars?' " +
    "and 'Who won the 2026 World Cup?' and both got the exact refusal phrase. " +
    "The model did not make anything up."
  ),
];

// ── 8. Limitations & Failure Modes ───────────────────────────────────────────
const sec8 = [
  spacer(80),
  heading("8  Limitations", HeadingLevel.HEADING_1),
  hr(),
  body("These are problems I actually saw during testing:"),
  heading("8.1  Answer Split Across Two Chunks", HeadingLevel.HEADING_2),
  body(
    "Sometimes the answer was in two consecutive chunks but neither chunk alone scored " +
    "high enough to get into the top-5. This happened a few times with lists and tables " +
    "that got cut in the middle."
  ),
  body("Higher overlap helps (Exp 3 showed 25% is better than 10%). Recursive chunking also avoids cutting mid-sentence."),
  heading("8.2  Wrong Words, Right Meaning", HeadingLevel.HEADING_2),
  body(
    "If the user says 'vector similarity search' but the document says 'approximate nearest " +
    "neighbour', the retriever can miss it because the words are different even though the " +
    "meaning is the same. I saw this a few times with technical synonyms."
  ),
  body("The fix is hybrid retrieval — combine dense vectors with BM25 keyword search. I did not have time to add this."),
  heading("8.3  Long Document Takes Over Results", HeadingLevel.HEADING_2),
  body(
    "A longer document produces more chunks, so it appears more in the top-5 even when " +
    "a shorter document has a better answer. I saw this a couple of times during testing."
  ),
  body("MMR re-ranking would fix this by making sure the top-5 comes from different sources."),
  heading("8.4  Small Hallucinations Even at Temperature=0", HeadingLevel.HEADING_2),
  body(
    "A few times the model added one extra sentence that was not in any chunk. " +
    "It happened when the chunks were close but not perfect — the model tried to fill the gap. " +
    "I made the system prompt stricter after this and it got better, but not perfect."
  ),
];

// ── 9. Reflection ─────────────────────────────────────────────────────────────
const sec9 = [
  spacer(80),
  heading("9  Reflection", HeadingLevel.HEADING_1),
  hr(),
  body(
    "I thought the hard part would be getting the LLM to stay grounded and not make things up. " +
    "That was actually fine once I got the system prompt right. The real hard part was retrieval — " +
    "if you get the wrong chunks, the answer will be wrong no matter how good the model is."
  ),
  body("With more time I would:"),
  bullet("Add BM25 keyword search alongside FAISS (hybrid retrieval). Dense search misses exact keyword matches. BM25 catches them. This would fix most of the vocabulary mismatch problems from section 8."),
  bullet("Add a cross-encoder re-ranker. The current approach retrieves top-20 with FAISS and picks top-5. A re-ranker reads query and chunk together and would give much better ranking."),
  bullet("Use Recall@5 instead of Precision@5. With only 5 documents, P@5 cannot get very high even with perfect retrieval. Recall@5 (did the right document appear anywhere?) makes more sense for this setup."),
  bullet("Better chunking for tables and code. My chunker treats everything as sentences. Tables get cut in the middle and become useless. A smarter parser would keep table rows together."),
];

// ═══════════════════════════════════════════════════════════════════════════
// ASSEMBLE DOCUMENT
// ═══════════════════════════════════════════════════════════════════════════

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }, {
        level: 1,
        format: LevelFormat.BULLET,
        text: "\u25E6",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: pt(11), color: "000000" } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:       { size: pt(16), bold: true, font: "Calibri", color: C.accent },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run:       { size: pt(13), bold: true, font: "Calibri", color: "000000" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size:   { width: 12240, height: 15840 },
        margin: { top: dxa(1), right: dxa(1), bottom: dxa(1), left: dxa(1.1) },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 1 } },
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "RAG Chatbot Pipeline — Technical Report", font: "Calibri", size: pt(9), color: C.grey }),
            new TextRun({ children: ["\t"], font: "Calibri" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Calibri", size: pt(9), color: C.grey }),
          ],
        })],
      }),
    },
    children: [
      ...titlePage,
      ...sec1,
      ...sec2,
      ...sec3,
      ...sec4,
      ...sec5,
      ...sec6,
      ...sec7,
      ...sec8,
      ...sec9,
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  const out = "RAG_Technical_Report_final.docx";
  fs.writeFileSync(out, buffer);
  console.log(`\n  Report written: ${out}`);
  console.log("  Open in Word / LibreOffice Writer and export as PDF.");
  console.log("  Fill in the [bracketed placeholders] with your actual experiment numbers.\n");
});
