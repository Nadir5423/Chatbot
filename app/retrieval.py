import logging
import re

from .config import TOP_K
from .db import pool
from .embeddings import embed_query, to_pgvector

log = logging.getLogger("retrieval")
RRF_K = 60


def hybrid_search(thread_id: str, query: str, top_k: int = TOP_K) -> list[dict]:
    qvec = to_pgvector(embed_query(query))
    clean_query = query.strip()

    with pool.connection() as conn:
        vec_rows = conn.execute(
            "SELECT c.id, c.document_id, c.page, c.content, d.filename, (c.embedding <=> %s::vector) as dist "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE c.thread_id = %s AND (c.embedding <=> %s::vector) < 0.45 "
            "ORDER BY dist ASC LIMIT 20",
            (qvec, thread_id, qvec),
        ).fetchall()

        fts_rows = []
        if clean_query:
            try:
                fts_rows = conn.execute(
                    "SELECT c.id, c.document_id, c.page, c.content, d.filename "
                    "FROM chunks c JOIN documents d ON d.id = c.document_id "
                    "WHERE c.thread_id = %s AND c.tsv @@ plainto_tsquery('simple', %s) "
                    "ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('simple', %s)) DESC LIMIT 20",
                    (thread_id, clean_query, clean_query),
                ).fetchall()
            except Exception as e:
                log.warning("FTS search failed: %s; falling back to vector results only", e)
                fts_rows = []

    # Reciprocal Rank Fusion
    scores, by_id = {}, {}
    for rows in (vec_rows, fts_rows):
        for rank, r in enumerate(rows):
            scores[r["id"]] = scores.get(r["id"], 0) + 1 / (RRF_K + rank + 1)
            by_id[r["id"]] = r

    best = sorted(scores, key=scores.get, reverse=True)[:top_k]
    log.info("Hybrid search for thread %s: %d vector candidates, %d FTS candidates -> top %d returned",
             thread_id, len(vec_rows), len(fts_rows), len(best))
    return [by_id[i] for i in best]