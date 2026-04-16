"""
System prompt and context formatter for the RAG generator.

Took a few iterations to get this right. My first version said something like
"prefer to use the provided context" and the model would still casually mix in
things it knew from training. Had to be much more explicit.

The three rules below are non-negotiable — the model must follow all of them
regardless of what the user asks. Rule 3 (exact refusal phrase) matters a lot
for evaluation: the evaluator checks for that exact string, so the wording
can't change.
"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """\
You are a precise, citation-driven research assistant. Your job is to answer \
the user's question using ONLY the context passages provided below.

STRICT RULES — violating any rule is unacceptable:
1. BASE EVERY CLAIM on the provided context. Do not use prior knowledge.
2. CITE THE SOURCE by including the document name in parentheses after each \
   factual claim, like this: (Source: <filename>).
3. If the question cannot be answered from the context, respond with EXACTLY \
   this phrase and nothing else:
   "I cannot find this in the provided documents"
4. Do not speculate, infer beyond the text, or combine context with external \
   knowledge.
5. Keep your answer concise and structured.
"""


def format_context(chunks: list[dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a numbered context block for the prompt.

    Each block includes the document name, date, and chunk text.
    """
    lines: list[str] = ["--- CONTEXT PASSAGES ---"]
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        title = meta.get("title") or meta.get("filename", "Unknown")
        filename = meta.get("filename", "unknown")
        date = meta.get("date", "n/a")
        score = chunk.get("score", 0.0)
        lines.append(
            f"\n[{i}] Document: \"{title}\" (file: {filename}, date: {date}, relevance: {score:.2f})\n"
            f"{chunk['text']}"
        )
    lines.append("\n--- END OF CONTEXT ---")
    return "\n".join(lines)


def build_prompt(query: str, chunks: list[dict[str, Any]]) -> tuple[str, str]:
    """
    Build the system prompt and user message for the LLM.

    Returns:
        (system_prompt, user_message)
    """
    context_block = format_context(chunks)
    user_message = f"{context_block}\n\nQuestion: {query}"
    return SYSTEM_PROMPT, user_message
