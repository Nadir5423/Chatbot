from sentence_transformers import SentenceTransformer

from .config import EMBED_MODEL

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    vecs = get_model().encode(
        [f"passage: {t}" for t in texts],
        normalize_embeddings=True,
        batch_size=16,
    )
    return vecs.tolist()


def embed_query(text: str) -> list[float]:
    return get_model().encode(f"query: {text}", normalize_embeddings=True).tolist()


def to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"