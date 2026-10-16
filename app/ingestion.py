import logging
import re

import pymupdf

from .config import CHUNK_OVERLAP, CHUNK_SIZE
from .db import pool
from .embeddings import embed_passages, to_pgvector

log = logging.getLogger("ingestion")


def is_non_english(text: str) -> bool:
    """True when most letters are Arabic-script (Urdu pages are skipped for now)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    arabic = sum(
        1 for c in letters
        if 0x0600 <= ord(c) <= 0x06FF or 0xFB50 <= ord(c) <= 0xFEFF
    )
    return arabic / len(letters) > 0.3


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = max(text.rfind(". ", start, end),
                      text.rfind("? ", start, end),
                      text.rfind("! ", start, end))
            if cut > start + size * 0.5:
                end = cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if len(c) > 30]


def ingest_pdf(document_id: str, thread_id: str, path: str) -> None:
    """Runs in the background: parse, chunk, embed, store."""
    try:
        doc = pymupdf.open(path)
        page_count = len(doc)
        rows, skipped = [], []

        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            if not text.strip():
                skipped.append(i)
                continue
            if is_non_english(text):
                skipped.append(i)
                continue
            for c in chunk_text(text):
                rows.append((i, c))

        if not rows:
            raise ValueError(
                "No readable English text found (scanned or non-English PDF; OCR is not enabled yet)."
            )

        texts = [c for _, c in rows]
        vectors = embed_passages(texts)

        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO chunks (document_id, thread_id, page, chunk_index, content, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s::vector)",
                    [
                        (document_id, thread_id, page, idx, content, to_pgvector(vec))
                        for idx, ((page, content), vec) in enumerate(zip(rows, vectors))
                    ],
                )
                note = f"Skipped pages (empty or non-English): {skipped}" if skipped else None
                cur.execute(
                    "UPDATE documents SET status='ready', page_count=%s, error=%s WHERE id=%s",
                    (page_count, note, document_id),
                )
        log.info("Ingested %s: %d chunks", document_id, len(rows))

    except Exception as e:
        log.exception("Ingestion failed")
        with pool.connection() as conn:
            conn.execute(
                "UPDATE documents SET status='failed', error=%s WHERE id=%s",
                (str(e)[:500], document_id),
            )