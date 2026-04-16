"""
LLM connection layer for the RAG pipeline.

Supports:
  - Anthropic (claude-haiku-4-5 by default)
  - OpenAI  (gpt-4o-mini by default)

Provider is selected via the LLM_PROVIDER environment variable.
All API keys come from environment variables — never hardcoded.
"""
from __future__ import annotations

import os
from typing import Any

from .prompts import build_prompt

_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# Model defaults per provider
_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _call_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=_MAX_TOKENS,
        temperature=_TEMPERATURE,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=_OPENAI_MODEL,
        max_tokens=_MAX_TOKENS,
        temperature=_TEMPERATURE,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_answer(
    query: str,
    chunks: list[dict[str, Any]],
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Generate a grounded, cited answer from the retrieved chunks.

    Args:
        query:    The user's question.
        chunks:   Top-k retrieved chunks from VectorStore.query().
        provider: Override LLM_PROVIDER env var ("anthropic" | "openai").

    Returns:
        {
            "answer":   str,      # LLM response
            "sources":  list,     # unique source filenames cited
            "chunks":   list,     # the chunks passed to the LLM
            "provider": str,
            "model":    str,
        }
    """
    active_provider = (provider or _PROVIDER).lower()
    system_prompt, user_message = build_prompt(query, chunks)

    if active_provider == "anthropic":
        answer = _call_anthropic(system_prompt, user_message)
        model = _ANTHROPIC_MODEL
    elif active_provider == "openai":
        answer = _call_openai(system_prompt, user_message)
        model = _OPENAI_MODEL
    else:
        raise ValueError(f"Unknown LLM provider: {active_provider!r}. Use 'anthropic' or 'openai'.")

    # Collect unique source filenames from the chunks
    sources = list(
        dict.fromkeys(
            c["metadata"].get("filename", "unknown") for c in chunks
        )
    )

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
        "provider": active_provider,
        "model": model,
    }
