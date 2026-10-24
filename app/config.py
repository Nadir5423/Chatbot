import os
from pathlib import Path
from dotenv import load_dotenv

from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing in .env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing in .env")

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing in .env")

MODELS_FILE = BASE_DIR / "models" / "models.txt"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = "intfloat/multilingual-e5-base"   # 768 dimensions
CHAT_MODEL = "openai/gpt-oss-20b"              # 20B: faster on Groq free tier
FAST_MODEL = "openai/gpt-oss-20b"               # query rewriting + fallback

CHUNK_SIZE = 1600      # characters (~400 tokens; fewer chunks = ~35% faster embedding)
CHUNK_OVERLAP = 200
TOP_K = 5
MAX_UPLOAD_MB = 25
HISTORY_MESSAGES = 8

NON_CHAT_KEYWORDS = ("whisper", "orpheus", "guard", "safeguard")


def load_models() -> list[str]:
    if not MODELS_FILE.exists():
        return []
    lines = MODELS_FILE.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


@lru_cache(maxsize=1)
def load_chat_models() -> list[str]:
    return [
        m for m in load_models()
        if not any(k in m.lower() for k in NON_CHAT_KEYWORDS)
    ]