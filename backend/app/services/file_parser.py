"""
Bunny - File Parser Service
Extracts text from .docx, .md, .pdf, .txt files and computes SHA-256 hash.
"""

import hashlib
import io
from pathlib import Path
from app.config import settings


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")

    if ext in (".docx", ".doc"):
        text = _from_docx(file_bytes)
    elif ext == ".pdf":
        text = _from_pdf(file_bytes)
    elif ext == ".md":
        text = file_bytes.decode("utf-8", errors="replace")
    else:  # .txt
        text = file_bytes.decode("utf-8", errors="replace")

    text = text.strip()
    if not text:
        raise ValueError("No text content could be extracted from the file.")
    return text


def _from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _from_pdf(file_bytes: bytes) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n\n".join(parts)


def compute_hash(text: str) -> str:
    """SHA-256 hex digest — the fingerprint stored on-chain."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_hash_bytes(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()


def get_text_stats(text: str) -> dict:
    words = text.split()
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    return {
        "word_count": len(words),
        "char_count": len(text),
        "sentence_count": len(sentences),
        "paragraph_count": text.count("\n\n") + 1,
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 2),
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 2),
    }
