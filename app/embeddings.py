import os
from functools import lru_cache
import torch
from sentence_transformers import SentenceTransformer

from .config import EMBED_MODEL

# Configure PyTorch CPU threads for maximum throughput
if hasattr(os, "cpu_count") and os.cpu_count():
    torch.set_num_threads(max(1, os.cpu_count() - 1))

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    formatted = [f"passage: {t}" for t in texts]
    with torch.inference_mode():
        vecs = get_model().encode(
            formatted,
            normalize_embeddings=True,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
    return vecs.tolist()


@lru_cache(maxsize=512)
def _embed_cached(text: str) -> tuple:
    with torch.inference_mode():
        return tuple(float(x) for x in get_model().encode(
            f"query: {text}",
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        ))


def embed_query(text: str) -> list[float]:
    return list(_embed_cached(text))


def to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
