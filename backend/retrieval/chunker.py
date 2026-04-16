"""
Two chunking strategies.

I thought chunking would be the boring part of this project. It's not.
The strategy you pick has a real effect on retrieval quality — chunks that
cut across sentence boundaries make it harder for the embedder to capture
the meaning, and then the retriever surfaces the wrong stuff.

Strategy A — Fixed-size overlap:
  Tokenise with tiktoken, slide a fixed window, repeat. Fast and deterministic.
  The downside is that sentences can get cut mid-way, which is annoying.

Strategy B — Recursive sentence-aware:
  Split on paragraph breaks first, then sentences, then accumulate greedily
  until the token limit. Carries a few sentences of overlap into the next chunk.
  Slower but produces more coherent chunks. My experiments showed similar
  precision@5 to fixed-size on this corpus, but I think it would win more
  clearly on a larger, more narrative dataset.

Both enforce: 100–512 tokens, 10–25% overlap, metadata + chunk_index on every chunk.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

# We use tiktoken for fast token counting (works without an OpenAI API call)
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def _token_len(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    # Rough fallback: 1 token ≈ 4 characters
    def _token_len(text: str) -> int:  # type: ignore[misc]
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class ChunkStrategy(str, Enum):
    FIXED = "fixed_size"
    RECURSIVE = "recursive"


class Chunk:
    """A single text chunk with metadata."""

    def __init__(self, text: str, metadata: dict[str, Any], chunk_index: int, strategy: ChunkStrategy):
        self.text = text.strip()
        self.metadata = {
            **metadata,
            "chunk_index": chunk_index,
            "strategy": strategy.value,
            "token_count": _token_len(text),
        }

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "metadata": self.metadata}

    def __repr__(self) -> str:
        return (
            f"Chunk(idx={self.metadata['chunk_index']}, "
            f"tokens={self.metadata['token_count']}, "
            f"strategy={self.metadata['strategy']!r})"
        )


# ---------------------------------------------------------------------------
# Strategy A — Fixed-size overlap
# ---------------------------------------------------------------------------

def fixed_size_chunk(
    text: str,
    metadata: dict[str, Any],
    chunk_size: int = 256,
    overlap: float = 0.15,
) -> list[Chunk]:
    """
    Split *text* into token windows of *chunk_size* with *overlap* (fraction).

    Args:
        text:        Raw document text.
        metadata:    Document-level metadata dict (filename, title, date …).
        chunk_size:  Target tokens per chunk (clamped to 100–512).
        overlap:     Fraction of chunk_size to repeat between consecutive chunks.
    """
    chunk_size = max(100, min(512, chunk_size))
    overlap_tokens = max(1, int(chunk_size * max(0.10, min(0.25, overlap))))

    try:
        tokens = _enc.encode(text)
        use_tokens = True
    except Exception:
        tokens = text.split()
        use_tokens = False

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    stride = chunk_size - overlap_tokens

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        window = tokens[start:end]

        if use_tokens:
            chunk_text = _enc.decode(window)
        else:
            chunk_text = " ".join(window)

        if _token_len(chunk_text) >= 10:  # skip near-empty tails
            chunks.append(Chunk(chunk_text, metadata, idx, ChunkStrategy.FIXED))
            idx += 1

        if end == len(tokens):
            break
        start += stride

    return chunks


# ---------------------------------------------------------------------------
# Strategy B — Recursive / sentence-aware
# ---------------------------------------------------------------------------

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_PARA_RE = re.compile(r"\n{2,}")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving paragraph boundaries."""
    paragraphs = _PARA_RE.split(text)
    sentences: list[str] = []
    for para in paragraphs:
        for sent in _SENTENCE_RE.split(para.strip()):
            s = sent.strip()
            if s:
                sentences.append(s)
        sentences.append("")  # paragraph boundary sentinel
    return [s for s in sentences if s]  # remove sentinels but keep flow


def recursive_chunk(
    text: str,
    metadata: dict[str, Any],
    chunk_size: int = 256,
    overlap: float = 0.15,
) -> list[Chunk]:
    """
    Split *text* into semantically coherent chunks by first splitting on
    paragraph / sentence boundaries, then merging/splitting to fit the
    token-size constraint.

    Overlap is applied by re-appending the last *overlap_tokens* worth of
    sentences to the beginning of the next chunk.

    Args:
        text:        Raw document text.
        metadata:    Document-level metadata dict.
        chunk_size:  Target tokens per chunk (100–512).
        overlap:     Fraction of overlap (0.10–0.25).
    """
    chunk_size = max(100, min(512, chunk_size))
    overlap_tokens = max(1, int(chunk_size * max(0.10, min(0.25, overlap))))

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0
    overlap_buffer: list[str] = []
    idx = 0

    def _flush(sents: list[str]) -> None:
        nonlocal idx
        joined = " ".join(sents)
        if _token_len(joined) >= 10:
            chunks.append(Chunk(joined, metadata, idx, ChunkStrategy.RECURSIVE))
            idx += 1

    for sent in sentences:
        sent_tokens = _token_len(sent)

        # If a single sentence exceeds chunk_size, split it word by word
        if sent_tokens > chunk_size:
            if current:
                _flush(current)
                # Build overlap from tail of current
                overlap_buffer = _build_overlap(current, overlap_tokens)
                current = list(overlap_buffer)
                current_tokens = sum(_token_len(s) for s in current)

            # Now chunk the long sentence itself
            words = sent.split()
            sub: list[str] = []
            sub_tokens = 0
            for word in words:
                w_tokens = _token_len(word)
                if sub_tokens + w_tokens > chunk_size and sub:
                    _flush([" ".join(sub)])
                    overlap_buffer = _build_overlap([" ".join(sub)], overlap_tokens)
                    sub = list(overlap_buffer)
                    sub_tokens = sum(_token_len(w) for w in sub)
                sub.append(word)
                sub_tokens += w_tokens
            if sub:
                current = sub
                current_tokens = sub_tokens
            continue

        if current_tokens + sent_tokens > chunk_size and current:
            _flush(current)
            overlap_buffer = _build_overlap(current, overlap_tokens)
            current = list(overlap_buffer)
            current_tokens = sum(_token_len(s) for s in current)

        current.append(sent)
        current_tokens += sent_tokens

    if current:
        _flush(current)

    return chunks


def _build_overlap(sentences: list[str], target_tokens: int) -> list[str]:
    """Pick sentences from the *end* of a list to fill *target_tokens*."""
    buffer: list[str] = []
    accumulated = 0
    for sent in reversed(sentences):
        t = _token_len(sent)
        if accumulated + t > target_tokens:
            break
        buffer.insert(0, sent)
        accumulated += t
    return buffer
