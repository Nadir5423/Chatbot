"""Document Chat: Streamlit frontend for the FastAPI RAG backend.

Run (backend must already be running in another terminal):
    streamlit run ui.py
"""
import html
import time
from datetime import datetime

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
MAX_UPLOAD_MB = 25
CHAT_TIMEOUT = 120
DEFAULT_TIMEOUT = 30
POLL_SECONDS = 3
GROUP_ORDER = ["Today", "Yesterday", "Previous 7 days", "Older"]
EXAMPLE_QUESTIONS = [
    "Summarize this document",
    "What are the key figures mentioned?",
    "Idare ka salana budget kitna hai?",
]

USER_AVATAR = ":material/person:"
BOT_AVATAR = ":material/description:"

# Vector icons (Feather icon set, MIT licence) drawn inline, so no emoji are used.
ICONS = {
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
            '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
            '<line x1="16" y1="17" x2="8" y2="17"/>',
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
}


def svg(name, size=16):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:-3px;flex-shrink:0">{ICONS[name]}</svg>'
    )


CSS = """
<style>
:root { --green:#0f7b5a; --navy:#1f2d3d; --navy-2:#2b3b4e; --line:#e3e8ee; }
.block-container { padding-top: 4rem; padding-bottom: 7rem; max-width: 1400px; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], #MainMenu, footer { display: none !important; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: var(--navy); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] small,
[data-testid="stSidebar"] div { color: #e6edf3; }
[data-testid="stSidebar"] hr { border-color: #34475c; }
.brand { display: flex; align-items: center; gap: .6rem; font-size: 1.1rem; font-weight: 700;
    color: #fff; margin: .2rem 0 1rem; }
.logo-mark { width: 30px; height: 30px; border-radius: 8px; background: var(--green); color: #fff;
    display: inline-flex; align-items: center; justify-content: center; }
.grp { font-size: .68rem; letter-spacing: .08em; text-transform: uppercase;
    color: #8fa3b8 !important; margin: 1rem 0 .25rem .25rem; }
[data-testid="stSidebar"] button { box-shadow: none; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent; border: 0; color: #cfd8e3; justify-content: flex-start; padding: .4rem .6rem; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p { text-align: left;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: inherit; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover { background: var(--navy-2); color: #fff; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: var(--green); border: 0; color: #fff; font-weight: 600; padding: .55rem; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p { color: #fff; }
[class*="st-key-active_"] button { background: var(--navy-2) !important; color: #4ade80 !important; }
[class*="st-key-del_"] button { color: #8fa3b8 !important; justify-content: center !important; padding: .4rem 0 !important; }
[class*="st-key-del_"] button:hover { color: #f87171 !important; background: transparent !important; }
.status { font-size: .8rem; display: flex; align-items: center; gap: .45rem; color: #e6edf3; }
.status .ms { margin-left: auto; color: #8fa3b8; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.ok { background: #22c55e; } .dot.bad { background: #ef4444; }

/* ---------- Header and profile ---------- */
.thread-title { font-size: 1.35rem; font-weight: 700; color: #1b2733; line-height: 1.2; }
.thread-sub { color: #6b7a89; font-size: .82rem; margin-top: .1rem; }
.st-key-profile button { width: 2.4rem; height: 2.4rem; min-height: 2.4rem; padding: 0; border-radius: 50%;
    background: var(--green); border: 0; color: #fff; font-weight: 700; }
.st-key-profile button p { color: #fff; }
.st-key-profile button [data-testid="stIconMaterial"] { display: none; }
.p-email { font-weight: 600; color: #1b2733; word-break: break-all; }
.p-sub { color: #6b7a89; font-size: .78rem; margin-bottom: .6rem; }

/* ---------- Message box (model picker lives inside it) ---------- */
.st-key-composer_box [data-testid="stForm"] { border: 1px solid #d6dde5; border-radius: 18px; background: #fff;
    padding: .35rem .5rem; box-shadow: 0 2px 10px rgba(20,40,60,.06); }
.st-key-composer_box [data-testid="stForm"]:focus-within { border-color: var(--green); }
.st-key-composer_box div[data-baseweb="input"], .st-key-composer_box div[data-baseweb="base-input"] {
    background: transparent !important; border: 0 !important; }
.st-key-composer_box input { background: transparent !important; box-shadow: none !important; }
.st-key-composer_box div[data-baseweb="select"] > div { background: #eef3f7; border: 0; border-radius: 999px;
    min-height: 2.2rem; font-size: .8rem; }
.st-key-composer_box button { width: 2.4rem; height: 2.4rem; min-height: 2.4rem; padding: 0; border-radius: 50%;
    background: var(--green); border: 0; color: #fff; }
.st-key-composer_box button:disabled { background: #cfd8e0; }

/* ---------- Source cards ---------- */
.src-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .6rem; margin: .3rem 0; }
.src { background: #f4f8fb; border: 1px solid var(--line); border-radius: 12px; padding: .65rem .75rem; }
.src-top { display: flex; align-items: center; gap: .5rem; margin-bottom: .4rem; }
.pg { background: var(--green); color: #fff; font-size: .7rem; font-weight: 600; padding: .1rem .5rem; border-radius: 6px; }
.fn { color: #6b7a89; font-size: .72rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.snip { background: #fff; border-radius: 8px; padding: .45rem .55rem; font-size: .78rem; color: #3a4754;
    max-height: 7.5rem; overflow: hidden; }

/* ---------- Documents vault ---------- */
.vault-head { display: flex; align-items: center; gap: .5rem; font-weight: 700; font-size: 1.05rem; margin-bottom: .6rem; }
.label { font-size: .68rem; letter-spacing: .08em; text-transform: uppercase; color: #6b7a89; margin: 1rem 0 .4rem; }
.doc { background: #f4f8fb; border: 1px solid var(--line); border-radius: 12px; padding: .75rem .85rem; margin-bottom: .6rem; }
.doc-top { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
.doc-name { display: flex; align-items: center; gap: .45rem; font-weight: 600; font-size: .9rem; min-width: 0; }
.doc-name span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-meta { color: #6b7a89; font-size: .76rem; margin-top: .15rem; }
.badge { font-size: .68rem; font-weight: 700; padding: .12rem .55rem; border-radius: 999px; white-space: nowrap; }
.b-ready { background: #d9f3e6; color: #0b7a4b; }
.b-proc  { background: #fff3cd; color: #8a6100; }
.b-fail  { background: #fde2e2; color: #b42318; }
.note { font-size: .76rem; color: #5b6b7a; margin-top: .45rem; }
.note.warn { background: #eaf2fb; border-radius: 8px; padding: .4rem .55rem; }
.note.warn span { color: #7b8996; font-size: .72rem; }
.note.err { background: #fdecec; color: #b42318; border-radius: 8px; padding: .4rem .55rem; }
.bar { height: 6px; background: #dbe5ee; border-radius: 999px; overflow: hidden; margin-top: .55rem; }
.bar-in { height: 100%; width: 35%; background: var(--green); border-radius: 999px; animation: slide 1.3s ease-in-out infinite; }
@keyframes slide { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }

/* ---------- Login and empty states ---------- */
.login-logo { width: 54px; height: 54px; border-radius: 14px; background: var(--green); color: #fff;
    display: flex; align-items: center; justify-content: center; margin: 3rem 0 .8rem; }
.empty { text-align: center; color: #5b6b7a; padding: 3rem 1rem; }
.empty h2 { color: #1b2733; margin-bottom: .3rem; }
</style>
"""


# ======================================================================
# State and API helpers
# ======================================================================
def init_state():
    defaults = {
        "token": None, "email": None, "auth_error": None,
        "thread_id": None, "messages": [], "messages_for": None,
        "docs": [], "show_docs": False, "confirm_delete": None,
        "uploader_n": 0, "flash": None, "prev_processing": False,
        "models": [], "models_valid": False, "model": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def logout(message=None):
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.thread_id = None
    st.session_state.messages = []
    st.session_state.messages_for = None
    st.session_state.docs = []
    st.session_state.confirm_delete = None
    st.session_state.auth_error = message


def api(method, path, *, json=None, files=None, timeout=DEFAULT_TIMEOUT, auth=True):
    """Returns (data, error_message). Never raises for network or HTTP errors."""
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.request(method, API_URL + path, json=json, files=files,
                             headers=headers, timeout=timeout)
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Start it with: uvicorn app.main:app --reload"
    except requests.exceptions.Timeout:
        return None, "The request took too long. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"

    if r.status_code == 401 and auth:
        logout("Your session expired. Please log in again.")
        st.rerun()
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = None
        if isinstance(detail, list):
            detail = "; ".join(str(d.get("msg", d)) for d in detail)
        return None, detail or f"Server error ({r.status_code})"
    try:
        return r.json(), None
    except ValueError:
        return None, "The server sent an unexpected response."


def parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone()
    except (ValueError, TypeError):
        return None


def group_label(dt):
    if dt is None:
        return "Older"
    days = (datetime.now().astimezone().date() - dt.date()).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days <= 7:
        return "Previous 7 days"
    return "Older"


def select_thread(thread_id):
    st.session_state.thread_id = thread_id
    st.session_state.messages_for = None
    st.session_state.show_docs = False
    st.session_state.uploader_n += 1


def ensure_models():
    if st.session_state.models:
        return
    data, err = api("GET", "/models", auth=False)
    if err or not data:
        return
    allowed = data.get("models") or []
    default = data.get("default")
    st.session_state.models_valid = bool(allowed)
    st.session_state.models = allowed or ([default] if default else [])
    if st.session_state.model not in st.session_state.models and st.session_state.models:
        st.session_state.model = default if default in st.session_state.models else st.session_state.models[0]


# ======================================================================
# Login screen
# ======================================================================
def _authenticate(path, email, password):
    email = (email or "").strip()
    if not email or not password:
        st.error("Enter your email and password.")
        return
    with st.spinner("Please wait..."):
        data, err = api("POST", path, json={"email": email, "password": password}, auth=False)
    if err:
        st.error(err)
        return
    st.session_state.token = data["token"]
    st.session_state.email = data["email"]
    st.session_state.auth_error = None
    st.rerun()


def login_page():
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(f'<div class="login-logo">{svg("file", 28)}</div>', unsafe_allow_html=True)
        st.title("Document Chat")
        st.caption("Upload PDFs and ask questions in English or Roman Urdu. Answers come with page references.")
        if st.session_state.auth_error:
            st.warning(st.session_state.auth_error)
        tab_in, tab_up = st.tabs(["Log in", "Create account"])
        with tab_in:
            with st.form("login_form"):
                email = st.text_input("Email", key="li_email")
                password = st.text_input("Password", type="password", key="li_pw")
                go = st.form_submit_button("Log in", type="primary", use_container_width=True)
            if go:
                _authenticate("/auth/login", email, password)
        with tab_up:
            with st.form("register_form"):
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password (8+ characters)", type="password", key="su_pw")
                go = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if go:
                _authenticate("/auth/register", email, password)


# ======================================================================
# Sidebar
# ======================================================================
def render_sidebar(threads):
    with st.sidebar:
        st.markdown(
            f'<div class="brand"><span class="logo-mark">{svg("file", 17)}</span>Document Chat</div>',
            unsafe_allow_html=True,
        )

        if st.button("New chat", icon=":material/add:", type="primary",
                     use_container_width=True, key="new_chat"):
            data, err = api("POST", "/threads", json={"title": "New chat"})
            if err:
                st.error(err)
            else:
                select_thread(data["id"])
                st.rerun()

        pending = st.session_state.confirm_delete
        if pending and any(t["id"] == pending for t in threads):
            st.warning("Delete this chat and its documents?")
            c1, c2 = st.columns(2)
            if c1.button("Delete", key="confirm_yes", type="primary", use_container_width=True):
                _, err = api("DELETE", f"/threads/{pending}")
                if err:
                    st.error(err)
                else:
                    if st.session_state.thread_id == pending:
                        st.session_state.thread_id = None
                        st.session_state.messages_for = None
                    st.session_state.confirm_delete = None
                    st.rerun()
            if c2.button("Cancel", key="confirm_no", use_container_width=True):
                st.session_state.confirm_delete = None
                st.rerun()

        groups = {}
        for t in threads:
            groups.setdefault(group_label(parse_dt(t.get("created_at"))), []).append(t)

        for label in GROUP_ORDER:
            if label not in groups:
                continue
            st.markdown(f'<div class="grp">{label}</div>', unsafe_allow_html=True)
            for t in groups[label]:
                active = t["id"] == st.session_state.thread_id
                title = t.get("title") or "New chat"
                short = title if len(title) <= 24 else title[:23] + "…"
                c1, c2 = st.columns([6, 1], vertical_alignment="center")
                key = f"{'active_' if active else 'thr_'}{t['id']}"
                if c1.button(short, icon=":material/chat_bubble_outline:", key=key, use_container_width=True):
                    select_thread(t["id"])
                    st.rerun()
                if c2.button("", icon=":material/delete_outline:", key=f"del_{t['id']}", help="Delete this chat"):
                    st.session_state.confirm_delete = t["id"]
                    st.rerun()

        st.divider()
        t0 = time.time()
        _, health_err = api("GET", "/health", auth=False, timeout=5)
        ms = int((time.time() - t0) * 1000)
        ok = health_err is None
        st.markdown(
            f'<div class="status"><span class="dot {"ok" if ok else "bad"}"></span>'
            f'{"Backend connected" if ok else "Backend offline"}'
            f'<span class="ms">{ms}ms</span></div>',
            unsafe_allow_html=True,
        )


# ======================================================================
# Header with profile menu
# ======================================================================
def profile_menu():
    email = st.session_state.email or ""
    initial = (email[:1] or "U").upper()
    with st.container(key="profile"):
        with st.popover(initial, help="Account"):
            st.markdown(f'<div class="p-email">{html.escape(email)}</div><div class="p-sub">Signed in</div>',
                        unsafe_allow_html=True)
            if st.button("Log out", icon=":material/logout:", key="logout_btn", use_container_width=True):
                logout()
                st.rerun()


def render_header(title, sub, n_docs, can_toggle):
    h1, h2, h3 = st.columns([6, 1.7, 0.6], vertical_alignment="center")
    with h1:
        st.markdown(
            f'<div class="thread-title">{html.escape(title)}</div><div class="thread-sub">{html.escape(sub)}</div>',
            unsafe_allow_html=True,
        )
    with h2:
        if st.button(f"Documents ({n_docs})", icon=":material/folder_open:", use_container_width=True,
                     key="toggle_docs", disabled=not can_toggle):
            st.session_state.show_docs = not st.session_state.show_docs
            st.rerun()
    with h3:
        profile_menu()


# ======================================================================
# Message box: text field, model picker and send button in one pill
# ======================================================================
def composer(ready, placeholder):
    host = getattr(st, "bottom", None) or getattr(st, "_bottom", None)
    with (host if host is not None else st.container()):
        with st.container(key="composer_box"):
            with st.form("composer", clear_on_submit=True, border=False):
                c_text, c_model, c_send = st.columns([7, 2.6, 0.7], vertical_alignment="center")
                text = c_text.text_input("Message", placeholder=placeholder, key="composer_text",
                                         label_visibility="collapsed", disabled=not ready)
                models = st.session_state.models
                if models:
                    current = st.session_state.model
                    idx = models.index(current) if current in models else 0
                    st.session_state.model = c_model.selectbox(
                        "Model", models, index=idx, label_visibility="collapsed",
                        disabled=not ready, help="Model used to answer",
                    )
                sent = c_send.form_submit_button("", icon=":material/arrow_upward:", key="send_btn",
                                                 type="primary", disabled=not ready)
    if sent and text and text.strip():
        return text.strip()
    return None


# ======================================================================
# Documents vault
# ======================================================================
def fetch_docs():
    data, err = api("GET", f"/threads/{st.session_state.thread_id}/documents")
    if err:
        return None, err
    st.session_state.docs = data
    return data, None


def doc_card_html(d):
    status = d.get("status")
    name = html.escape(d.get("filename") or "document.pdf")
    pages = d.get("page_count")
    meta = f"{pages} pages" if pages else "Reading..."
    if status == "ready":
        badge = '<span class="badge b-ready">Ready</span>'
    elif status == "failed":
        badge = '<span class="badge b-fail">Failed</span>'
    else:
        badge = '<span class="badge b-proc">Processing</span>'

    extra = ""
    if status == "processing":
        extra = ('<div class="bar"><div class="bar-in"></div></div>'
                 '<div class="note">Reading your document. This can take a minute.</div>')
    elif status == "failed":
        extra = f'<div class="note err">{html.escape(d.get("error") or "Processing failed.")}</div>'
    elif d.get("error"):
        extra = ('<div class="note warn">Some pages were skipped (empty or non-English).'
                 f'<br><span>{html.escape(d["error"])}</span></div>')
    return (f'<div class="doc"><div class="doc-top"><div class="doc-name">{svg("file", 16)}<span>{name}</span></div>'
            f'{badge}</div><div class="doc-meta">{meta}</div>{extra}</div>')


def docs_panel():
    """Runs as a fragment: polls every few seconds while a document is processing."""
    docs, err = fetch_docs()
    if err:
        st.error(err)
        docs = st.session_state.docs
    processing = any(d["status"] == "processing" for d in docs)
    if st.session_state.prev_processing and not processing:
        st.session_state.prev_processing = False
        st.rerun()  # full rerun so the message box unlocks
    st.session_state.prev_processing = processing

    ready_n = sum(1 for d in docs if d["status"] == "ready")
    st.markdown(
        f'<div class="vault-head">{svg("folder", 18)} Documents Vault '
        f'<span class="badge b-ready">{ready_n} ready</span></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None

    up = st.file_uploader(
        "Upload a PDF", type=["pdf"], label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_n}",
    )
    st.caption(f"Drop your PDF here or click to browse. Max {MAX_UPLOAD_MB} MB per document.")
    if up is not None:
        if up.size > MAX_UPLOAD_MB * 1024 * 1024:
            st.error(f"This file is {up.size / 1048576:.1f} MB. The limit is {MAX_UPLOAD_MB} MB.")
        elif st.button("Upload and index", icon=":material/upload:", type="primary",
                       use_container_width=True, key="do_upload"):
            with st.spinner("Uploading..."):
                data, err = api(
                    "POST", f"/threads/{st.session_state.thread_id}/documents",
                    files={"file": (up.name, up.getvalue(), "application/pdf")},
                    timeout=120,
                )
            if err:
                st.error(err)
            else:
                st.session_state.flash = (
                    "This file was already uploaded to this chat."
                    if data.get("status") == "duplicate"
                    else "Upload received. Reading your document now."
                )
                st.session_state.uploader_n += 1
                st.rerun()

    st.markdown('<div class="label">Uploaded sources</div>', unsafe_allow_html=True)
    if not docs:
        st.caption("No documents yet.")
    for d in docs:
        st.markdown(doc_card_html(d), unsafe_allow_html=True)


# ======================================================================
# Chat
# ======================================================================
def render_sources(sources, expanded=False):
    if not sources:
        return
    cards = "".join(
        f'<div class="src"><div class="src-top"><span class="pg">Page {html.escape(str(s.get("page", "?")))}</span>'
        f'<span class="fn">{html.escape(str(s.get("filename", "")))}</span></div>'
        f'<div class="snip">{html.escape(str(s.get("snippet", "")))}…</div></div>'
        for s in sources
    )
    with st.expander(f"Sources ({len(sources)})", expanded=expanded):
        st.markdown(f'<div class="src-grid">{cards}</div>', unsafe_allow_html=True)


def render_footer(model, latency_ms):
    parts = []
    if model:
        parts.append(f"Answered by {model}")
    if latency_ms:
        parts.append(f"{latency_ms / 1000:.1f}s")
    if parts:
        st.caption(" · ".join(parts))


def render_message(m, expanded=False):
    avatar = USER_AVATAR if m["role"] == "user" else BOT_AVATAR
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            render_sources(m.get("sources"), expanded)
            render_footer(m.get("model"), m.get("latency_ms"))


def typing(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.012)


def send_question(thread, question):
    tid = thread["id"]
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)
    payload = {"message": question}
    if st.session_state.models_valid and st.session_state.model:
        payload["model"] = st.session_state.model

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Searching the document..."):
            t0 = time.time()
            data, err = api("POST", f"/threads/{tid}/chat", json=payload, timeout=CHAT_TIMEOUT)
            latency = int((time.time() - t0) * 1000)
        if err:
            st.error(err)
            st.caption("This question was not answered. Check the message above and send it again.")
            st.session_state.messages_for = None  # reload history next time
            return
        answer = data["answer"]
        st.write_stream(typing(answer))
        render_sources(data.get("sources"), expanded=True)
        render_footer(data.get("model"), latency)

    is_first = not st.session_state.messages
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer, "sources": data.get("sources") or [],
         "model": data.get("model"), "latency_ms": latency},
    ]
    # Name the chat after the first question (needs the optional PATCH endpoint; ignored if missing)
    if is_first and (thread.get("title") or "New chat") == "New chat":
        title = " ".join(question.split())[:40]
        renamed, _ = api("PATCH", f"/threads/{tid}", json={"title": title})
        if renamed:
            st.rerun()


def empty_no_thread():
    st.markdown(
        '<div class="empty"><h2>Chat with your documents</h2>'
        'Create a chat, upload a PDF, then ask questions in English or Roman Urdu.</div>',
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1, 1])
    if mid.button("Start new chat", icon=":material/add:", type="primary",
                  use_container_width=True, key="start_chat"):
        data, err = api("POST", "/threads", json={"title": "New chat"})
        if err:
            st.error(err)
        else:
            select_thread(data["id"])
            st.rerun()


def chat_page():
    threads, err = api("GET", "/threads")
    if err:
        render_sidebar([])
        render_header("Document Chat", "", 0, False)
        st.error(err)
        st.stop()

    ids = [t["id"] for t in threads]
    if st.session_state.thread_id not in ids:
        st.session_state.thread_id = ids[0] if ids else None
        st.session_state.messages_for = None
    render_sidebar(threads)

    tid = st.session_state.thread_id
    if tid is None:
        render_header("Document Chat", "Create a chat to get started", 0, False)
        empty_no_thread()
        return
    thread = next(t for t in threads if t["id"] == tid)

    docs, err = fetch_docs()
    if err:
        st.error(err)
        docs = []
    ready = any(d["status"] == "ready" for d in docs)
    processing = any(d["status"] == "processing" for d in docs)
    st.session_state.prev_processing = processing

    if st.session_state.messages_for != tid:
        msgs, err = api("GET", f"/threads/{tid}/messages")
        if err:
            st.error(err)
            msgs = []
        else:
            st.session_state.messages_for = tid
        st.session_state.messages = msgs

    sub = f"{len(docs)} document(s) in this chat" if docs else "No documents yet"
    render_header(thread.get("title") or "New chat", sub, len(docs), bool(docs))

    if ready:
        placeholder = "Ask a question about your document (English or Roman Urdu)..."
    elif processing:
        placeholder = "Your document is still being processed..."
    else:
        placeholder = "Upload a PDF first, then ask a question"
    prompt = composer(ready, placeholder)
    if not prompt:
        prompt = st.session_state.pop("pending_prompt", None)

    show_panel = st.session_state.show_docs or not docs
    if show_panel:
        chat_col, doc_col = st.columns([2.3, 1], gap="large")
    else:
        chat_col, doc_col = st.container(), None

    with chat_col:
        for i, m in enumerate(st.session_state.messages):
            last = i == len(st.session_state.messages) - 1
            render_message(m, expanded=last and m["role"] == "assistant")

        if not st.session_state.messages and not prompt:
            if ready:
                st.markdown(
                    '<div class="empty"><h2>Ask your first question</h2>'
                    'Your document is ready. Try one of these:</div>',
                    unsafe_allow_html=True,
                )
                for n, q in enumerate(EXAMPLE_QUESTIONS):
                    st.button(q, key=f"chip_{n}", use_container_width=True,
                              on_click=lambda q=q: st.session_state.update(pending_prompt=q))
            elif processing:
                st.info("Reading your document. You can ask questions as soon as it shows as Ready.")
            else:
                st.info("Upload a PDF using the panel on the right to begin.")

        if prompt:
            send_question(thread, prompt.strip())

    if doc_col is not None:
        with doc_col:
            st.fragment(docs_panel, run_every=POLL_SECONDS if processing else None)()


def main():
    st.set_page_config(page_title="Document Chat", page_icon=":material/description:", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    if not st.session_state.token:
        login_page()
        return
    ensure_models()
    chat_page()


main()