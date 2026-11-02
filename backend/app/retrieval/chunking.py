"""
Text extraction and chunking.
Supports PDF, DOCX, TXT, and Markdown.
"""
from __future__ import annotations

from typing import TypedDict


class ChunkData(TypedDict):
    content: str
    page_number: int | None
    section_title: str | None


CHUNK_SIZE = 800   # characters
CHUNK_OVERLAP = 100


def extract_and_chunk(file_path: str, original_filename: str) -> list[ChunkData]:
    """Extract text from a file and return chunked data."""
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "txt"

    extractor_map = {
        "pdf": _extract_pdf,
        "docx": _extract_docx,
        "txt": _extract_text,
        "md": _extract_text,
    }
    extractor = extractor_map.get(ext, _extract_text)
    pages = extractor(file_path)

    chunks: list[ChunkData] = []
    for page_num, text in pages:
        page_chunks = _chunk_text(text)
        for chunk_text in page_chunks:
            if chunk_text.strip():
                chunks.append(ChunkData(
                    content=chunk_text.strip(),
                    page_number=page_num,
                    section_title=_detect_section_title(chunk_text),
                ))

    return chunks


def _extract_pdf(file_path: str) -> list[tuple[int, str]]:
    """Extract text from PDF, returning list of (page_number, text)."""
    try:
        import PyPDF2
        pages = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages.append((i, text))
        return pages
    except ImportError:
        return _extract_text(file_path)
    except Exception:
        return []


def _extract_docx(file_path: str) -> list[tuple[int, str]]:
    """Extract text from DOCX."""
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [(1, text)]
    except ImportError:
        return _extract_text(file_path)
    except Exception:
        return []


def _extract_text(file_path: str) -> list[tuple[int, str]]:
    """Read plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return [(1, f.read())]
    except Exception:
        return []


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        # Prefer splitting at paragraph boundaries
        if end < len(text):
            para_break = text.rfind("\n\n", start, end)
            sentence_break = text.rfind(". ", start, end)
            if para_break > start + CHUNK_SIZE // 2:
                end = para_break + 2
            elif sentence_break > start + CHUNK_SIZE // 2:
                end = sentence_break + 2

        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks


def _detect_section_title(text: str) -> str | None:
    """Heuristic: first line if it looks like a heading."""
    lines = text.strip().split("\n")
    if not lines:
        return None
    first_line = lines[0].strip()
    # Markdown heading
    if first_line.startswith("#"):
        return first_line.lstrip("#").strip()
    # Short capitalized line (likely a heading)
    if len(first_line) < 80 and first_line == first_line.title() and len(first_line) > 5:
        return first_line
    return None
