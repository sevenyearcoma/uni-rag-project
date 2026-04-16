"""
Creates a sample PDF document for testing the RAG ingestion pipeline.

Topic: Transformer Scaling Laws and Attention Variants
This covers content not in any of the existing Markdown sample docs,
so it gives distinct, cross-document-testable questions.

Run once:
    python create_sample_pdf.py
"""

from fpdf import FPDF
from pathlib import Path

OUT_PATH = Path("data/sample_docs/transformer_scaling.pdf")


def s(text: str) -> str:
    """Sanitise text to Latin-1 so Helvetica doesn't choke."""
    return (text
        .replace("\u2014", " - ")   # em dash
        .replace("\u2013", "-")     # en dash
        .replace("\u2019", "'")     # right single quote
        .replace("\u2018", "'")     # left single quote
        .replace("\u201c", '"')     # left double quote
        .replace("\u201d", '"')     # right double quote
        .replace("\u2022", "-")     # bullet
        .replace("\u2500", "-")     # box drawing
        .encode("latin-1", errors="replace").decode("latin-1")
    )


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Transformer Scaling Laws and Attention Variants - Technical Overview", align="L")
        self.ln(2)
        self.set_draw_color(30, 60, 120)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")

    def section_title(self, text):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 60, 120)
        self.cell(0, 8, s(text), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 60, 120)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.l_margin + 60, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def subsection_title(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, s(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 6, s(text), align="J")
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.cell(5, 6, "-")
        self.multi_cell(0, 6, s(text), align="J")

    def key_value_table(self, rows):
        """Simple two-column table."""
        self.set_font("Helvetica", "B", 10)
        col_w = [65, 115]
        self.set_fill_color(30, 60, 120)
        self.set_text_color(255, 255, 255)
        self.cell(col_w[0], 7, "Property", border=1, fill=True)
        self.cell(col_w[1], 7, "Value", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        for i, (k, v) in enumerate(rows):
            self.set_fill_color(240, 245, 252) if i % 2 == 0 else self.set_fill_color(255, 255, 255)
            self.set_text_color(0, 0, 0)
            self.cell(col_w[0], 6.5, s(k), border=1, fill=True)
            self.cell(col_w[1], 6.5, s(v), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


# ── Build the document ───────────────────────────────────────────────────────

pdf = PDF()
from datetime import datetime
pdf.set_creator("RAG Pipeline Sample Document Generator")
pdf.set_title("Transformer Scaling Laws and Attention Variants")
pdf.set_author("CS AI Project — Sample Document")
pdf.set_creation_date(datetime(2024, 4, 1))

pdf.set_margins(left=18, top=22, right=18)
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()

# ── Title block ──────────────────────────────────────────────────────────────
pdf.set_font("Helvetica", "B", 18)
pdf.set_text_color(30, 60, 120)
pdf.cell(0, 10, s("Transformer Scaling Laws and Attention Variants"), new_x="LMARGIN", new_y="NEXT", align="C")
pdf.set_font("Helvetica", "I", 11)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 7, s("A Technical Overview for the RAG Architecture Study"), new_x="LMARGIN", new_y="NEXT", align="C")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 6, s("Date: 2024-04-01  |  Type: Technical Reference  |  Topic: LLM Foundations"), new_x="LMARGIN", new_y="NEXT", align="C")
pdf.set_text_color(0, 0, 0)
pdf.ln(6)

# ── 1. Scaling Laws ──────────────────────────────────────────────────────────
pdf.section_title("1  Scaling Laws in Large Language Models")

pdf.body_text(
    "Scaling laws describe the predictable relationship between a model's performance and "
    "three key factors: the number of parameters (N), the size of the training dataset (D), "
    "and the amount of compute used (C). The landmark 2020 paper by Kaplan et al. at OpenAI "
    "established that test loss decreases as a smooth power law when any of these factors is "
    "increased, holding the others fixed."
)

pdf.body_text(
    "The key finding was that model performance scales more efficiently with parameter count "
    "than with dataset size when compute is held constant. This led to the early practice of "
    "training very large models on relatively small datasets — for example, GPT-3 (175 billion "
    "parameters) was trained on approximately 300 billion tokens."
)

pdf.subsection_title("1.1  Chinchilla Scaling Laws")

pdf.body_text(
    "In 2022, Hoffmann et al. at DeepMind published the Chinchilla paper, which revised the "
    "earlier scaling law estimates significantly. Their finding: for a given compute budget, "
    "the optimal strategy is to train a smaller model on more data, not a larger model on "
    "less data. Specifically, the number of training tokens should be approximately 20 times "
    "the number of model parameters."
)

pdf.body_text(
    "Under Chinchilla-optimal training, a 70 billion parameter model should be trained on "
    "roughly 1.4 trillion tokens. This is the principle behind models like Llama 2 70B and "
    "Mistral 7B, which punch above their weight relative to earlier models of similar size "
    "because they were trained on far more tokens than the pre-Chinchilla guidance suggested."
)

pdf.key_value_table([
    ("Kaplan et al. (2020)", "Larger models are more compute-efficient"),
    ("Chinchilla ratio", "~20 tokens per parameter is optimal"),
    ("GPT-3 (175B params)", "Trained on ~300B tokens — under-trained by Chinchilla standard"),
    ("Llama 2 70B",         "Trained on 2T tokens — Chinchilla-optimal"),
    ("Key implication",     "Smaller, well-trained models can outperform larger, under-trained ones"),
])

# ── 2. Attention Variants ────────────────────────────────────────────────────
pdf.section_title("2  Attention Variants")

pdf.body_text(
    "Standard multi-head attention (MHA) has quadratic complexity in sequence length — "
    "processing a sequence of length L requires O(L^2) operations and O(L^2) memory. "
    "For long documents this becomes a bottleneck. Several variants have been proposed "
    "to address this."
)

pdf.subsection_title("2.1  Multi-Query Attention (MQA)")

pdf.body_text(
    "Multi-Query Attention (Shazeer, 2019) reduces memory bandwidth at inference time by "
    "sharing a single set of key and value heads across all query heads. This significantly "
    "reduces the size of the key-value (KV) cache, which is a major bottleneck for inference "
    "throughput on long sequences. MQA is used in PaLM and Falcon."
)

pdf.subsection_title("2.2  Grouped Query Attention (GQA)")

pdf.body_text(
    "Grouped Query Attention (Ainslie et al., 2023) is a middle ground between standard MHA "
    "and MQA. Instead of one shared KV head, it uses G groups of KV heads, where G is between "
    "1 (MQA) and the number of query heads (MHA). This retains most of MQA's inference speed "
    "advantage while recovering some of the quality lost from sharing a single head. GQA is "
    "used in Llama 2 70B, Llama 3, and Mistral 7B."
)

pdf.subsection_title("2.3  Flash Attention")

pdf.body_text(
    "Flash Attention (Dao et al., 2022) is an IO-aware exact attention algorithm that "
    "reorders the attention computation to minimise reads and writes to GPU HBM (high-bandwidth "
    "memory). It achieves the same result as standard attention mathematically, but runs 2-4x "
    "faster and uses up to 10-20x less memory, enabling training on much longer sequences. "
    "Flash Attention 2 (2023) extended these improvements with better parallelism across "
    "sequence length."
)

pdf.key_value_table([
    ("MHA (standard)",          "H query, H key, H value heads — full KV cache"),
    ("MQA",                     "H query heads, 1 shared KV head — minimal KV cache"),
    ("GQA",                     "H query heads, G shared KV groups — balanced"),
    ("Flash Attention",         "Exact attention, 2-4x faster, up to 20x less memory"),
    ("Used in Llama 3",         "GQA with 8 KV heads for 70B model"),
])

# ── 3. Context Length ────────────────────────────────────────────────────────
pdf.section_title("3  Context Length and Long-Context Models")

pdf.body_text(
    "The context window defines how many tokens a model can process in a single forward pass. "
    "Early transformer models were limited to 512 tokens (BERT) or 1024 tokens (GPT-2). "
    "Modern LLMs have extended this dramatically: GPT-4 supports 128K tokens, Claude 3 "
    "supports 200K tokens, and Gemini 1.5 Pro demonstrated experimental support for up to "
    "1 million tokens."
)

pdf.body_text(
    "Longer context windows are valuable for RAG systems because they allow more retrieved "
    "chunks to be included in the prompt, reducing the chance that a key passage is excluded. "
    "However, several studies have shown the 'lost in the middle' problem: models with very "
    "long contexts tend to under-utilise information positioned in the middle of the context "
    "window, performing better on information near the beginning or end. This means that "
    "simply increasing context length does not linearly improve RAG quality."
)

pdf.subsection_title("3.1  Positional Encoding Methods")

pdf.body_text(
    "Original transformers used fixed sinusoidal positional encodings. Modern models use "
    "Rotary Positional Embeddings (RoPE, Su et al., 2021), which encode position information "
    "directly into the query-key dot product. RoPE is used in Llama, Mistral, and most modern "
    "open-source models. It supports context length extension via techniques like YaRN and "
    "Dynamic NTK scaling, which interpolate or extrapolate the position frequencies."
)

# ── 4. Instruction Tuning and RLHF ──────────────────────────────────────────
pdf.section_title("4  Instruction Tuning and Alignment")

pdf.body_text(
    "Pre-trained language models predict the next token but do not naturally follow instructions. "
    "Instruction tuning fine-tunes a pre-trained model on a dataset of (instruction, response) "
    "pairs, teaching the model to be helpful and follow directions."
)

pdf.subsection_title("4.1  Reinforcement Learning from Human Feedback (RLHF)")

pdf.body_text(
    "RLHF (Ouyang et al., 2022 — InstructGPT) is the technique used to align models like "
    "GPT-4 and Claude. It has three stages: (1) supervised fine-tuning on demonstration data, "
    "(2) training a reward model on human preference labels, and (3) using PPO reinforcement "
    "learning to optimise the language model against the reward model. The reward model learns "
    "to predict which of two model outputs a human would prefer."
)

pdf.subsection_title("4.2  Direct Preference Optimisation (DPO)")

pdf.body_text(
    "Direct Preference Optimisation (Rafailov et al., 2023) is a simpler alternative to RLHF "
    "that skips the reward model entirely. DPO reformulates the RLHF objective as a classification "
    "problem on preference pairs, making training more stable and computationally cheaper. "
    "Several recent open-source models (Zephyr, Tulu 2) use DPO rather than PPO-based RLHF."
)

pdf.key_value_table([
    ("Instruction tuning",  "Fine-tune on (instruction, response) pairs — teaches helpfulness"),
    ("RLHF",               "Human preference labels + reward model + PPO — aligns to human values"),
    ("DPO",                "Preference classification without a separate reward model — simpler"),
    ("Used in",            "GPT-4, Claude (RLHF); Zephyr, Tulu 2 (DPO)"),
])

# ── 5. Relevance to RAG ──────────────────────────────────────────────────────
pdf.section_title("5  Relevance to RAG Systems")

pdf.body_text(
    "The architectural choices described in this document directly affect RAG system design. "
    "The Chinchilla scaling laws suggest that a well-trained smaller model (e.g. Llama 3 8B, "
    "trained on 15 trillion tokens) can outperform a larger but under-trained model as a RAG "
    "generator, while being much cheaper to run."
)

pdf.body_text(
    "GQA and Flash Attention reduce inference latency and memory consumption, which is "
    "important for RAG because the context passed to the generator can be very long — "
    "the system prompt plus five retrieved chunks of 256 tokens each is already over 1,500 "
    "tokens before the question is added."
)

pdf.body_text(
    "The 'lost in the middle' problem has a direct implication for chunk ordering in RAG: "
    "the most relevant retrieved chunks should be placed at the beginning and end of the "
    "context block, not in the middle, to maximise the probability that the model attends "
    "to them during generation."
)

pdf.body_text(
    "Finally, instruction tuning and alignment (RLHF or DPO) are what make modern LLM APIs "
    "follow grounding instructions in system prompts. A base pre-trained model would largely "
    "ignore the 'only use the provided context' instruction; an instruction-tuned model treats "
    "it as a hard constraint."
)

# ── Save ─────────────────────────────────────────────────────────────────────
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
pdf.output(str(OUT_PATH))
print(f"PDF written: {OUT_PATH}  ({OUT_PATH.stat().st_size // 1024} KB)")
