"""
Document loader for the RAG pipeline.
Supports PDF and Markdown files.
Extracts: filename/URL, title, and date metadata.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# PDF support
try:
    import pdfplumber
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

# Markdown support
try:
    import frontmatter  # python-frontmatter
    _FM_AVAILABLE = True
except ImportError:
    _FM_AVAILABLE = False


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class Document:
    """A loaded document with raw text and metadata."""

    def __init__(self, text: str, metadata: dict[str, Any]):
        self.text = text
        self.metadata = metadata  # always contains: filename, title, date, source_type

    def __repr__(self) -> str:
        return f"Document(title={self.metadata.get('title')!r}, chars={len(self.text)})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_pdf_title(path: Path, pages: list) -> str:
    """Try to extract a title from PDF metadata or first-page text."""
    # pdfplumber exposes the underlying pypdf metadata
    with pdfplumber.open(str(path)) as pdf:
        meta = pdf.metadata or {}
        if meta.get("Title"):
            return meta["Title"].strip()

    # Fallback: first non-empty line of page 1
    if pages:
        first_line = pages[0].strip().split("\n")[0]
        if first_line:
            return first_line[:120]

    return path.stem


def _extract_pdf_date(path: Path) -> str:
    """Try to extract creation date from PDF metadata, fall back to file mtime."""
    with pdfplumber.open(str(path)) as pdf:
        meta = pdf.metadata or {}
        raw = meta.get("CreationDate", "")
        # PDF dates look like: D:20230615120000+00'00'
        if raw:
            match = re.search(r"D:(\d{8})", raw)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")
                except ValueError:
                    pass

    mtime = os.path.getmtime(str(path))
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def _extract_md_title(path: Path, post) -> str:
    """Extract title from frontmatter or first H1 heading."""
    if _FM_AVAILABLE and hasattr(post, "metadata"):
        title = post.metadata.get("title") or post.metadata.get("Title")
        if title:
            return str(title).strip()

    # Fallback: first # heading in the raw content
    content = post.content if _FM_AVAILABLE else open(path, encoding="utf-8").read()
    for line in content.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()[:120]

    return path.stem


def _extract_md_date(path: Path, post) -> str:
    """Extract date from frontmatter or file mtime."""
    if _FM_AVAILABLE and hasattr(post, "metadata"):
        date_val = post.metadata.get("date") or post.metadata.get("Date")
        if date_val:
            if isinstance(date_val, datetime):
                return date_val.strftime("%Y-%m-%d")
            return str(date_val)[:10]

    mtime = os.path.getmtime(str(path))
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_pdf(path: Path | str) -> Document:
    """Load a PDF file and return a Document."""
    if not _PDF_AVAILABLE:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    path = Path(path)
    pages_text: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n\n".join(pages_text)
    title = _extract_pdf_title(path, pages_text)
    date = _extract_pdf_date(path)

    return Document(
        text=full_text,
        metadata={
            "filename": path.name,
            "source_url": str(path.resolve()),
            "title": title,
            "date": date,
            "source_type": "pdf",
            "page_count": len(pages_text),
        },
    )


def load_markdown(path: Path | str) -> Document:
    """Load a Markdown file and return a Document."""
    path = Path(path)

    if _FM_AVAILABLE:
        post = frontmatter.load(str(path))
        content = post.content
    else:
        content = path.read_text(encoding="utf-8")
        # Strip any YAML frontmatter manually
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                content = content[end + 3:].lstrip()
        post = type("_Post", (), {"metadata": {}, "content": content})()

    title = _extract_md_title(path, post)
    date = _extract_md_date(path, post)

    return Document(
        text=content,
        metadata={
            "filename": path.name,
            "source_url": str(path.resolve()),
            "title": title,
            "date": date,
            "source_type": "markdown",
        },
    )


def load_document(path: Path | str) -> Document:
    """Auto-detect file type and load accordingly."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)
    elif suffix in {".md", ".markdown"}:
        return load_markdown(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix!r}. Supported: .pdf, .md, .markdown")


def load_directory(directory: Path | str, recursive: bool = True) -> list[Document]:
    """Load all supported documents from a directory."""
    directory = Path(directory)
    pattern = "**/*" if recursive else "*"
    supported = {".pdf", ".md", ".markdown"}

    docs: list[Document] = []
    for fpath in directory.glob(pattern):
        if fpath.suffix.lower() in supported and fpath.is_file():
            try:
                doc = load_document(fpath)
                docs.append(doc)
                print(f"  [ingest] Loaded: {fpath.name} ({doc.metadata['source_type']})")
            except Exception as exc:
                print(f"  [ingest] WARNING: could not load {fpath.name}: {exc}")

    return docs
