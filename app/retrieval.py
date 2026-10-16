import re

from .config import TOP_K
from .db import pool
from .embeddings import embed_query, to_pgvector

RRF_K = 60


def hybrid_search(thread_id: str, query: str, top_k: int = TOP_K) -> list[dict]:
    qvec = to_pgvector(embed_query(query))
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
    ts_query = " | ".join(words)

    with pool.connection() as conn:
        vec_rows = conn.execute(
            "SELECT c.id, c.page, c.content, d.filename "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE c.thread_id = %s ORDER BY c.embedding <=> %s::vector LIMIT 20",
            (thread_id, qvec),
        ).fetchall()

        fts_rows = []
        if ts_query:
            fts_rows = conn.execute(
                "SELECT c.id, c.page, c.content, d.filename "
                "FROM chunks c JOIN documents d ON d.id = c.document_id "
                "WHERE c.thread_id = %s AND c.tsv @@ to_tsquery('simple', %s) "
                "ORDER BY ts_rank_cd(c.tsv, to_tsquery('simple', %s)) DESC LIMIT 20",
                (thread_id, ts_query, ts_query),
            ).fetchall()

    # Reciprocal Rank Fusion
    scores, by_id = {}, {}
    for rows in (vec_rows, fts_rows):
        for rank, r in enumerate(rows):
            scores[r["id"]] = scores.get(r["id"], 0) + 1 / (RRF_K + rank + 1)
            by_id[r["id"]] = r

    best = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [by_id[i] for i in best]