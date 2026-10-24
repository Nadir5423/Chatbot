import hashlib
import logging
import threading
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .agent import answer, cited_pages, rewrite_query, wants_references
from .auth import (create_file_token, create_token, current_user, hash_password,
                   verify_file_token, verify_password)
from .config import (CHAT_MODEL, HISTORY_MESSAGES, MAX_UPLOAD_MB, UPLOAD_DIR,
                     load_chat_models)
from .db import pool
from .embeddings import get_model
from .ingestion import ingest_pdf
from .retrieval import hybrid_search

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    # Load the embedding model in the background so the first upload is fast
    threading.Thread(target=get_model, daemon=True).start()
    yield
    pool.close()


app = FastAPI(title="RAG Chatbot API", lifespan=lifespan)


class ThreadCreate(BaseModel):
    title: str | None = None


class ThreadRename(BaseModel):
    title: str


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=4000)
    model: str | None = None


class AuthBody(BaseModel):
    email: str
    password: str


def _require_thread(conn, thread_id: UUID, user_id: str):
    """404 unless the thread exists AND belongs to this user."""
    if not conn.execute(
        "SELECT 1 FROM threads WHERE id = %s AND user_id = %s", (thread_id, user_id)
    ).fetchone():
        raise HTTPException(404, "Thread not found")


def _file_path(document_id):
    return UPLOAD_DIR / f"{document_id}.pdf"


def _build_sources(chunks: list[dict], reply: str) -> list[dict]:
    """One entry per (document, page). If the answer cites pages, keep only those."""
    cited = cited_pages(reply)
    picked = [c for c in chunks if c["page"] in cited] or chunks
    seen, out = set(), []
    for c in picked:
        key = (str(c["document_id"]), c["page"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "document_id": str(c["document_id"]),
            "filename": c["filename"],
            "page": c["page"],
            "snippet": c["content"][:200],
        })
    return sorted(out, key=lambda s: (s["filename"], s["page"]))


def _link_sources(sources, user_id: str) -> list[dict]:
    """Adds a short-lived link to each source whose PDF is still on disk."""
    out = []
    for s in sources or []:
        s = dict(s)
        doc_id = s.get("document_id")
        if doc_id and _file_path(doc_id).exists():
            s["url"] = f"/files/{doc_id}?token={create_file_token(user_id, doc_id)}"
        out.append(s)
    return out


# ---------- Public endpoints ----------

@app.get("/")
def root():
    return {"message": "RAG Chatbot API. See /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "db": "connected"}


@app.get("/models")
def models():
    return {"models": load_chat_models(), "default": CHAT_MODEL}


@app.post("/auth/register")
def register(body: AuthBody):
    email = body.email.strip().lower()
    if "@" not in email or len(body.password) < 8:
        raise HTTPException(400, "Enter a valid email and a password of 8+ characters")
    try:
        with pool.connection() as conn:
            if conn.execute("SELECT 1 FROM users WHERE email = %s", (email,)).fetchone():
                raise HTTPException(409, "This email is already registered")
            row = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, hash_password(body.password)),
            ).fetchone()
    except UniqueViolation:
        raise HTTPException(409, "This email is already registered")
    return {"token": create_token(row["id"]), "email": email}


@app.post("/auth/login")
def login(body: AuthBody):
    email = body.email.strip().lower()
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = %s", (email,)
        ).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(row["id"]), "email": email}


# ---------- Threads (login required) ----------

@app.post("/threads")
def create_thread(body: ThreadCreate, user_id: str = Depends(current_user)):
    with pool.connection() as conn:
        return conn.execute(
            "INSERT INTO threads (title, user_id) VALUES (%s, %s) "
            "RETURNING id, title, created_at",
            (body.title or "New chat", user_id),
        ).fetchone()


@app.get("/threads")
def list_threads(user_id: str = Depends(current_user)):
    with pool.connection() as conn:
        return conn.execute(
            "SELECT id, title, created_at FROM threads "
            "WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()


@app.patch("/threads/{thread_id}")
def rename_thread(thread_id: UUID, body: ThreadRename, user_id: str = Depends(current_user)):
    title = body.title.strip()[:60] or "New chat"
    with pool.connection() as conn:
        _require_thread(conn, thread_id, user_id)
        conn.execute("UPDATE threads SET title = %s WHERE id = %s", (title, thread_id))
    return {"id": str(thread_id), "title": title}


@app.delete("/threads/{thread_id}")
def delete_thread(thread_id: UUID, user_id: str = Depends(current_user)):
    with pool.connection() as conn:
        conn.execute(
            "DELETE FROM threads WHERE id = %s AND user_id = %s", (thread_id, user_id)
        )
    return {"deleted": str(thread_id)}


@app.get("/threads/{thread_id}/messages")
def get_messages(thread_id: UUID, user_id: str = Depends(current_user)):
    with pool.connection() as conn:
        _require_thread(conn, thread_id, user_id)
        rows = conn.execute(
            "SELECT id, role, content, sources, model, created_at "
            "FROM messages WHERE thread_id = %s ORDER BY created_at, id",
            (thread_id,),
        ).fetchall()
    for r in rows:
        r["sources"] = _link_sources(r.get("sources"), user_id)
    return rows


# ---------- Documents ----------

@app.get("/threads/{thread_id}/documents")
def list_documents(thread_id: UUID, user_id: str = Depends(current_user)):
    with pool.connection() as conn:
        _require_thread(conn, thread_id, user_id)
        return conn.execute(
            "SELECT id, filename, status, page_count, error, created_at "
            "FROM documents WHERE thread_id = %s ORDER BY created_at",
            (thread_id,),
        ).fetchall()


@app.post("/threads/{thread_id}/documents")
async def upload_document(
    thread_id: UUID,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(current_user),
):
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD_MB} MB)")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "This does not look like a PDF file")

    file_hash = hashlib.sha256(data).hexdigest()
    with pool.connection() as conn:
        _require_thread(conn, thread_id, user_id)
        dup = conn.execute(
            "SELECT id FROM documents WHERE thread_id = %s AND file_hash = %s AND status != 'failed'",
            (thread_id, file_hash),
        ).fetchone()
        if dup:
            return {"document_id": str(dup["id"]), "status": "duplicate"}
        row = conn.execute(
            "INSERT INTO documents (thread_id, filename, file_hash) "
            "VALUES (%s, %s, %s) RETURNING id",
            (thread_id, file.filename, file_hash),
        ).fetchone()

    doc_id = str(row["id"])
    path = _file_path(doc_id)          # named after the document id so links can find it
    path.write_bytes(data)
    background.add_task(ingest_pdf, doc_id, str(thread_id), str(path))
    return {"document_id": doc_id, "status": "processing"}


@app.get("/files/{document_id}")
def open_document(document_id: UUID, token: str):
    """Opens the original PDF. Used by reference links, so it checks a short-lived file token."""
    user_id = verify_file_token(token, document_id)
    with pool.connection() as conn:
        row = conn.execute(
            "SELECT d.filename FROM documents d JOIN threads t ON t.id = d.thread_id "
            "WHERE d.id = %s AND t.user_id = %s",
            (document_id, user_id),
        ).fetchone()
    path = _file_path(document_id)
    if not row or not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=row["filename"] or "document.pdf",
        content_disposition_type="inline",
    )


# ---------- Chat ----------

@app.post("/threads/{thread_id}/chat")
def chat(thread_id: UUID, body: ChatRequest, user_id: str = Depends(current_user)):
    question = body.message.strip()
    if not question:
        raise HTTPException(400, "Empty message")
    if body.model and body.model not in load_chat_models():
        raise HTTPException(400, "Unknown model")

    with pool.connection() as conn:
        _require_thread(conn, thread_id, user_id)
        history = list(reversed(conn.execute(
            "SELECT role, content FROM messages WHERE thread_id = %s "
            "ORDER BY created_at DESC, id DESC LIMIT %s",
            (thread_id, HISTORY_MESSAGES),
        ).fetchall()))
        has_docs = conn.execute(
            "SELECT 1 FROM documents WHERE thread_id = %s AND status = 'ready' LIMIT 1",
            (thread_id,),
        ).fetchone()
        # Save the user message before calling the LLM
        conn.execute(
            "INSERT INTO messages (thread_id, role, content) VALUES (%s, 'user', %s)",
            (thread_id, question),
        )

    wants_refs = wants_references(question)
    sources, used_model = [], None
    if not has_docs:
        reply = "Please upload a PDF to this thread first (and wait until it shows as ready)."
    else:
        search_query = rewrite_query(question, history)
        chunks = hybrid_search(str(thread_id), search_query)
        try:
            reply, used_model, found = answer(question, chunks, history, body.model, wants_refs)
        except Exception as e:
            logging.exception("LLM generation failed: %s", e)
            raise HTTPException(
                503,
                "The AI model service is currently unavailable or rate limited. Please try again in a few moments."
            )
        # References only when the user asked for them AND the answer came from the document
        if wants_refs and found:
            sources = _build_sources(chunks, reply)

    with pool.connection() as conn:
        conn.execute(
            "INSERT INTO messages (thread_id, role, content, sources, model) "
            "VALUES (%s, 'assistant', %s, %s, %s)",
            (thread_id, reply, Jsonb(sources), used_model),
        )
    return {"answer": reply, "sources": _link_sources(sources, user_id), "model": used_model}