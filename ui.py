"""Document Intelligence: Professional RAG interface with Claude-inspired warm editorial aesthetic.

Run:
    streamlit run ui.py
"""
import html
import os
import time
from datetime import datetime

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", API_URL).rstrip("/")
MAX_UPLOAD_MB = 25
CHAT_TIMEOUT = 120
DEFAULT_TIMEOUT = 30
GROUP_ORDER = ["Today", "Yesterday", "Previous 7 days", "Older"]
EXAMPLE_QUESTIONS = [
    "Summarize the key findings and conclusions",
    "What are the main statistics or metrics mentioned?",
    "Idare ka salana budget aur kharchat kitne hain?",
]

# Crisp, professional Lucide stroke icons
ICONS = {
    "logo": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>'
            '<path d="M6 6h10"/><path d="M6 10h10"/><path d="M6 14h6"/>'
            '</svg>',
    "file": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
            '<polyline points="14 2 14 8 20 8"/>'
            '</svg>',
    "sparkles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>'
                '</svg>',
    "link": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
            '</svg>',
    "upload": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'
              '</svg>',
}


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --terracotta: #c96442;
    --terracotta-hover: #b25335;
    --terracotta-light: #fbf2ee;
    --terracotta-border: #f2dbd1;
    --bg-main: #faf8f5;
    --bg-sidebar: #f3eee6;
    --bg-sidebar-hover: #e8e2d8;
    --bg-sidebar-active: #e2dcd0;
    --border: #e8e2d8;
    --border-light: #efebe4;
    --text-main: #201e1c;
    --text-muted: #6e685f;
    --font-serif: "Newsreader", "Georgia", "Cambria", serif;
    --font-sans: "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

html, body, [data-testid="stAppViewContainer"], .main, section.main {
    background-color: var(--bg-main) !important;
    color: var(--text-main) !important;
    font-family: var(--font-sans);
    scroll-behavior: smooth;
}

.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 7.5rem !important;
    max-width: 860px !important;
    margin: 0 auto !important;
}

header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], #MainMenu, footer { display: none !important; }

/* Keep icon font rendering properly */
[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
    color: var(--text-main);
}
[data-testid="stSidebar"] hr { border-color: var(--border) !important; }

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: .65rem;
    font-family: var(--font-serif);
    font-size: 1.3rem;
    font-weight: 500;
    color: var(--text-main);
    margin: .2rem 0 1.2rem;
}
.brand-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: var(--terracotta);
    color: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.history-label {
    font-size: .68rem;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--text-muted) !important;
    margin: 1.2rem 0 .35rem .25rem;
    font-weight: 600;
}

[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 0 !important;
    color: #383531 !important;
    justify-content: flex-start !important;
    padding: .45rem .75rem !important;
    border-radius: 10px !important;
    font-size: .88rem !important;
    box-shadow: none !important;
    transition: all .15s ease !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] p {
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: inherit !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
    background: var(--bg-sidebar-hover) !important;
    color: var(--text-main) !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: var(--terracotta) !important;
    border: 0 !important;
    color: #fff !important;
    font-weight: 500 !important;
    padding: .55rem 1rem !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    transition: all .15s ease !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
    background: var(--terracotta-hover) !important;
}

[class*="st-key-active_"] button {
    background: var(--bg-sidebar-active) !important;
    color: var(--terracotta) !important;
    font-weight: 600 !important;
    border-left: 3px solid var(--terracotta) !important;
    border-radius: 4px 10px 10px 4px !important;
}

.system-status {
    font-size: .78rem;
    display: flex;
    align-items: center;
    gap: .45rem;
    color: var(--text-muted);
}
.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
}
.status-dot.ok { background: #16a34a; }
.status-dot.bad { background: #dc2626; }

/* ---------- Header ---------- */
.chat-header-bar {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-light);
}
.chat-title {
    font-family: var(--font-serif);
    font-size: 1.7rem;
    font-weight: 500;
    color: var(--text-main);
    line-height: 1.25;
}
.chat-subtitle {
    color: var(--text-muted);
    font-size: .84rem;
    margin-top: .2rem;
}

/* ---------- Floating Message Composer ---------- */
.st-key-composer_box {
    max-width: 860px;
    margin: 0 auto;
}
.st-key-composer_box [data-testid="stForm"] {
    border: 1px solid var(--border) !important;
    border-radius: 22px !important;
    background: #ffffff !important;
    padding: .35rem .65rem !important;
    box-shadow: 0 4px 20px rgba(40,30,15,.05) !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.st-key-composer_box [data-testid="stForm"]:focus-within {
    border-color: var(--terracotta) !important;
    box-shadow: 0 4px 26px rgba(201,100,66,.12) !important;
}
.st-key-composer_box div[data-baseweb="input"], .st-key-composer_box div[data-baseweb="base-input"] {
    background: transparent !important;
    border: 0 !important;
    font-size: .95rem !important;
}
.st-key-composer_box input {
    background: transparent !important;
    box-shadow: none !important;
    color: var(--text-main) !important;
}
.st-key-composer_box div[data-baseweb="select"] > div {
    background: #f7f4ee !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 999px !important;
    min-height: 2.1rem !important;
    font-size: .78rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
}
.st-key-composer_box button {
    width: 2.3rem !important;
    height: 2.3rem !important;
    min-height: 2.3rem !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: var(--terracotta) !important;
    border: 0 !important;
    color: #fff !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    transition: background .15s ease !important;
}
.st-key-composer_box button:hover { background: var(--terracotta-hover) !important; }
.st-key-composer_box button:disabled { background: #e5e0d7 !important; color: #9c968b !important; }

/* ---------- References & Citations ---------- */
.citation-container { margin: .85rem 0 .3rem; font-size: .86rem; }
.citation-title {
    font-size: .72rem;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: .45rem;
    font-weight: 600;
}
.citation-chips { display: flex; flex-wrap: wrap; gap: .45rem; }
.citation-chip {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-size: .8rem;
    font-weight: 500;
    padding: .25rem .65rem;
    border-radius: 8px;
    background: var(--terracotta-light);
    border: 1px solid var(--terracotta-border);
    color: var(--terracotta);
    text-decoration: none;
    transition: all .15s ease;
}
.citation-chip:hover {
    background: #f7e4dc;
    color: var(--terracotta-hover);
    border-color: #ecc9bd;
}

/* ---------- Welcome & Empty States ---------- */
.welcome-hero {
    text-align: center;
    padding: 3.5rem 1rem 2rem;
    max-width: 650px;
    margin: 0 auto;
}
.welcome-badge {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: var(--terracotta-light);
    color: var(--terracotta);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.2rem;
}
.welcome-hero h2 {
    font-family: var(--font-serif);
    font-size: 2.2rem;
    font-weight: 400;
    color: var(--text-main);
    margin-bottom: .45rem;
}
.welcome-hero p {
    color: var(--text-muted);
    font-size: 1rem;
    line-height: 1.5;
    margin-bottom: 2rem;
}

/* Suggestion Buttons */
.suggestion-card button {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text-main) !important;
    padding: .9rem 1.1rem !important;
    text-align: left !important;
    font-size: .88rem !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 4px rgba(40,30,15,.03) !important;
    transition: all .15s ease !important;
}
.suggestion-card button:hover {
    border-color: var(--terracotta) !important;
    background: #fffdfc !important;
    box-shadow: 0 3px 12px rgba(201,100,66,.08) !important;
}

/* Document drawer items */
.document-item {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: .75rem .9rem;
    margin-bottom: .5rem;
}
.document-row { display: flex; align-items: center; justify-content: space-between; }
.badge { font-size: .68rem; font-weight: 600; padding: .15rem .55rem; border-radius: 999px; }
.badge-ready { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.badge-proc  { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.badge-fail  { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

/* User popover */
.profile-email { font-weight: 600; color: var(--text-main); word-break: break-all; }
.profile-sub { color: var(--text-muted); font-size: .78rem; margin-bottom: .6rem; }
</style>
"""


# ======================================================================
# Application State and API Client
# ======================================================================
def init_state():
    defaults = {
        "token": None, "email": None, "auth_error": None,
        "thread_id": None, "messages": [], "messages_for": None,
        "docs": [], "uploader_n": 0, "prev_processing": False,
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
    st.session_state.auth_error = message


def api(method, path, *, json=None, files=None, timeout=DEFAULT_TIMEOUT, auth=True):
    """Executes HTTP calls to the backend API."""
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.request(method, API_URL + path, json=json, files=files,
                             headers=headers, timeout=timeout)
    except requests.exceptions.ConnectionError:
        return None, "Unable to reach the backend service. Please check that FastAPI is running."
    except requests.exceptions.Timeout:
        return None, "The request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"

    if r.status_code == 401 and auth:
        logout("Session expired. Please log in again.")
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
        return None, "Unexpected server response."


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
# Authentication Screen
# ======================================================================
def _authenticate(path, email, password):
    email = (email or "").strip()
    if not email or not password:
        st.error("Please enter both email and password.")
        return
    with st.spinner("Authenticating..."):
        data, err = api("POST", path, json={"email": email, "password": password}, auth=False)
    if err:
        st.error(err)
        return
    st.session_state.token = data["token"]
    st.session_state.email = data["email"]
    st.session_state.auth_error = None
    st.rerun()


def login_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(
            f'<div class="welcome-badge" style="margin-top: 3.5rem;">{ICONS["logo"]}</div>'
            '<h1 style="font-family: var(--font-serif); font-size: 2.2rem; font-weight: 400; margin-bottom: .2rem;">Document Intelligence</h1>'
            '<p style="color: var(--text-muted); font-size: .95rem; margin-bottom: 1.8rem;">'
            'Analyze reports, query facts, and synthesize citations from your PDFs in English or Roman Urdu.</p>',
            unsafe_allow_html=True,
        )
        if st.session_state.auth_error:
            st.warning(st.session_state.auth_error)
        tab_in, tab_up = st.tabs(["Sign In", "Create Account"])
        with tab_in:
            with st.form("login_form"):
                email = st.text_input("Email", key="li_email")
                password = st.text_input("Password", type="password", key="li_pw")
                go = st.form_submit_button("Continue with Email", type="primary", use_container_width=True)
            if go:
                _authenticate("/auth/login", email, password)
        with tab_up:
            with st.form("register_form"):
                email = st.text_input("Email", key="su_email")
                password = st.text_input("Password (8+ characters)", type="password", key="su_pw")
                go = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            if go:
                _authenticate("/auth/register", email, password)


# ======================================================================
# Sidebar Navigation
# ======================================================================
def render_sidebar(threads):
    with st.sidebar:
        st.markdown(
            f'<div class="sidebar-brand"><span class="brand-icon">{ICONS["logo"]}</span>DocuMind AI</div>',
            unsafe_allow_html=True,
        )

        if st.button("+ New Conversation", type="primary", use_container_width=True, key="new_chat"):
            data, err = api("POST", "/threads", json={"title": "New chat"})
            if not err:
                select_thread(data["id"])
                st.rerun()

        groups = {}
        for t in threads:
            groups.setdefault(group_label(parse_dt(t.get("created_at"))), []).append(t)

        for label in GROUP_ORDER:
            if label not in groups:
                continue
            st.markdown(f'<div class="history-label">{label}</div>', unsafe_allow_html=True)
            for t in groups[label]:
                active = t["id"] == st.session_state.thread_id
                title = t.get("title") or "New chat"
                short = title if len(title) <= 26 else title[:25] + "…"
                key = f"{'active_' if active else 'thr_'}{t['id']}"
                if st.button(short, key=key, use_container_width=True):
                    select_thread(t["id"])
                    st.rerun()

        st.divider()
        t0 = time.time()
        _, health_err = api("GET", "/health", auth=False, timeout=5)
        ms = int((time.time() - t0) * 1000)
        ok = health_err is None
        st.markdown(
            f'<div class="system-status"><span class="status-dot {"ok" if ok else "bad"}"></span>'
            f'{"System ready" if ok else "Backend offline"}'
            f'<span style="margin-left: auto;">{ms}ms</span></div>',
            unsafe_allow_html=True,
        )


# ======================================================================
# Header & Document Management
# ======================================================================
def fetch_docs():
    data, err = api("GET", f"/threads/{st.session_state.thread_id}/documents")
    if err:
        return [], err
    st.session_state.docs = data or []
    return st.session_state.docs, None


def render_header(title, docs):
    h_left, h_right = st.columns([5.5, 3.5], vertical_alignment="center")
    ready_n = sum(1 for d in docs if d.get("status") == "ready")
    proc_n = sum(1 for d in docs if d.get("status") == "processing")

    with h_left:
        sub_text = (
            f"📄 {ready_n} document indexed" if ready_n == 1
            else f"📄 {ready_n} documents indexed" if ready_n > 1
            else "Processing document..." if proc_n > 0
            else "No document attached"
        )
        st.markdown(
            f'<div style="margin-bottom: 1.2rem;">'
            f'<div class="chat-title">{html.escape(title)}</div>'
            f'<div class="chat-subtitle">{sub_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with h_right:
        c_docs, c_del, c_prof = st.columns([2.4, 0.9, 0.9], vertical_alignment="center")
        with c_docs:
            with st.popover(f"📄 Documents ({len(docs)})", use_container_width=True):
                st.markdown("#### Document Vault")
                up = st.file_uploader(
                    "Upload PDF", type=["pdf"], label_visibility="collapsed",
                    key=f"header_up_{st.session_state.uploader_n}",
                )
                if up is not None:
                    if up.size > MAX_UPLOAD_MB * 1024 * 1024:
                        st.error(f"Limit is {MAX_UPLOAD_MB} MB.")
                    elif st.button("Upload Document", type="primary", use_container_width=True):
                        with st.spinner("Processing..."):
                            data, err = api(
                                "POST", f"/threads/{st.session_state.thread_id}/documents",
                                files={"file": (up.name, up.getvalue(), "application/pdf")},
                                timeout=120,
                            )
                        if not err:
                            st.session_state.uploader_n += 1
                            st.rerun()

                st.markdown("---")
                if not docs:
                    st.caption("No PDFs attached yet.")
                for d in docs:
                    status = d.get("status")
                    name = html.escape(d.get("filename") or "document.pdf")
                    badge_cls = "badge-ready" if status == "ready" else "badge-proc" if status == "processing" else "badge-fail"
                    st.markdown(
                        f'<div class="document-item">'
                        f'<div class="document-row"><span>{name}</span>'
                        f'<span class="badge {badge_cls}">{status.capitalize()}</span></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        with c_del:
            if st.button("🗑️", help="Delete conversation"):
                api("DELETE", f"/threads/{st.session_state.thread_id}")
                st.session_state.thread_id = None
                st.session_state.messages_for = None
                st.rerun()
        with c_prof:
            email = st.session_state.email or "User"
            initial = (email[:1] or "U").upper()
            with st.popover(initial, help="Account"):
                st.markdown(f'<div class="profile-email">{html.escape(email)}</div><div class="profile-sub">Active Session</div>', unsafe_allow_html=True)
                if st.button("Sign Out", key="logout_btn", use_container_width=True):
                    logout()
                    st.rerun()


# ======================================================================
# Floating Message Composer
# ======================================================================
def composer(ready, placeholder):
    host = getattr(st, "bottom", None) or getattr(st, "_bottom", None)
    with (host if host is not None else st.container()):
        with st.container(key="composer_box"):
            with st.form("composer", clear_on_submit=True, border=False):
                c_text, c_model, c_send = st.columns([7.2, 2.8, 0.7], vertical_alignment="center")
                text = c_text.text_input(
                    "Message", placeholder=placeholder, key="composer_text",
                    label_visibility="collapsed", disabled=not ready,
                )
                models = st.session_state.models
                if models:
                    current = st.session_state.model
                    idx = models.index(current) if current in models else 0
                    st.session_state.model = c_model.selectbox(
                        "Model", models, index=idx, label_visibility="collapsed",
                        disabled=not ready, help="Select Inference Model",
                    )
                sent = c_send.form_submit_button("↑", key="send_btn", type="primary", disabled=not ready)
    if sent and text and text.strip():
        return text.strip()
    return None


# ======================================================================
# Citations & Message Feed
# ======================================================================
def render_sources(sources):
    """Renders sleek reference chips with link icons."""
    if not sources:
        return
    seen, chips = set(), []
    for src in sources:
        key = (src.get("filename"), src.get("page"))
        if key in seen:
            continue
        seen.add(key)
        page_str = f'p. {src.get("page", "?")}'
        fname = src.get("filename") or "Document"
        if len(fname) > 24:
            fname = fname[:23] + "…"
        label = html.escape(f'{fname} · {page_str}')
        url = src.get("url")
        if url:
            href = html.escape(f'{PUBLIC_API_URL}{url}#page={src.get("page") or 1}', quote=True)
            chips.append(f'<a href="{href}" target="_blank" rel="noopener" class="citation-chip">{ICONS["file"]} {label} {ICONS["link"]}</a>')
        else:
            chips.append(f'<span class="citation-chip">{ICONS["file"]} {label}</span>')
    st.markdown(
        '<div class="citation-container"><div class="citation-title">Verified Sources</div><div class="citation-chips">' + "".join(chips) + "</div></div>",
        unsafe_allow_html=True,
    )


def render_message(m):
    avatar = "👤" if m["role"] == "user" else "✨"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            render_sources(m.get("sources"))
            if m.get("model"):
                st.caption(f"Synthesized by {m['model']}")


def scroll_to_bottom():
    """Scrolls smoothly to the bottom of the conversation feed."""
    js = """
    <div id="end-of-chat-anchor" style="height: 1px; width: 100%; margin: 0; padding: 0;"></div>
    <script>
    (function() {
        function scrollToBottom() {
            var el = document.getElementById("end-of-chat-anchor");
            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "end", inline: "nearest" });
            }
            var containers = [
                document.querySelector('[data-testid="stAppViewContainer"]'),
                document.querySelector('[data-testid="stMain"]'),
                document.querySelector('section.main'),
                document.documentElement,
                document.body
            ];
            containers.forEach(function(c) {
                if (c && c.scrollHeight > c.clientHeight) {
                    c.scrollTo({ top: c.scrollHeight, behavior: "smooth" });
                }
            });
            window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }
        scrollToBottom();
        setTimeout(scrollToBottom, 50);
        setTimeout(scrollToBottom, 180);
        setTimeout(scrollToBottom, 450);
    })();
    </script>
    """
    try:
        st.html(js, unsafe_allow_javascript=True)
    except Exception:
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
            (function() {
                var doc = window.parent.document;
                var el = doc.getElementById("end-of-chat-anchor");
                if (el) el.scrollIntoView({ behavior: "smooth", block: "end" });
                var c = doc.querySelector('[data-testid="stAppViewContainer"]') || doc.querySelector('section.main');
                if (c) c.scrollTop = c.scrollHeight;
                window.parent.scrollTo({ top: doc.body.scrollHeight, behavior: "smooth" });
            })();
            </script>
            """,
            height=0,
            width=0,
        )


def send_question(thread, question):
    tid = thread["id"]
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)
    scroll_to_bottom()

    payload = {"message": question}
    if st.session_state.models_valid and st.session_state.model:
        payload["model"] = st.session_state.model

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Retrieving document context..."):
            t0 = time.time()
            data, err = api("POST", f"/threads/{tid}/chat", json=payload, timeout=CHAT_TIMEOUT)
            latency = int((time.time() - t0) * 1000)
        if err:
            st.error(err)
            st.caption("Unable to complete request. Please verify the backend logs.")
            st.session_state.messages_for = None
            scroll_to_bottom()
            return
        answer = data["answer"]
        st.markdown(answer)
        render_sources(data.get("sources"))
        st.caption(f"Generated by {data.get('model', 'assistant')} in {latency / 1000:.1f}s")

    scroll_to_bottom()

    is_first = not st.session_state.messages
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer, "sources": data.get("sources") or [],
         "model": data.get("model"), "latency_ms": latency},
    ]
    if is_first and (thread.get("title") or "New chat") == "New chat":
        title = " ".join(question.split())[:36]
        renamed, _ = api("PATCH", f"/threads/{tid}", json={"title": title})
        if renamed:
            st.rerun()


# ======================================================================
# Main Layout
# ======================================================================
def chat_page():
    threads, err = api("GET", "/threads")
    if err:
        render_sidebar([])
        st.error(err)
        st.stop()

    ids = [t["id"] for t in threads]
    if st.session_state.thread_id not in ids:
        st.session_state.thread_id = ids[0] if ids else None
        st.session_state.messages_for = None
    render_sidebar(threads)

    tid = st.session_state.thread_id
    if tid is None:
        st.markdown(
            f'<div class="welcome-hero">'
            f'<div class="welcome-badge">{ICONS["logo"]}</div>'
            f'<h2>Document Intelligence</h2>'
            f'<p>Create a conversation or upload a PDF to analyze facts, extract insights, and cite verified sources.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        _, mid, _ = st.columns([1, 1.2, 1])
        if mid.button("+ Start Conversation", type="primary", use_container_width=True):
            data, err = api("POST", "/threads", json={"title": "New chat"})
            if not err:
                select_thread(data["id"])
                st.rerun()
        return

    thread = next(t for t in threads if t["id"] == tid)
    docs, _ = fetch_docs()
    ready = any(d["status"] == "ready" for d in docs)
    processing = any(d["status"] == "processing" for d in docs)
    st.session_state.prev_processing = processing

    if st.session_state.messages_for != tid:
        msgs, err = api("GET", f"/threads/{tid}/messages")
        st.session_state.messages_for = tid
        st.session_state.messages = msgs or []

    render_header(thread.get("title") or "New chat", docs)

    if processing:
        st.info("Indexing your document in the background... Ready to query in a few moments.")
        time.sleep(1.5)
        st.rerun()

    placeholder = (
        "Ask a question about your document..." if ready
        else "Document is currently being indexed..." if processing
        else "Attach a PDF to this conversation to begin..."
    )
    prompt = composer(ready, placeholder)
    if not prompt:
        prompt = st.session_state.pop("pending_prompt", None)

    for m in st.session_state.messages:
        render_message(m)

    if not st.session_state.messages and not prompt:
        if not docs:
            st.markdown(
                f'<div class="welcome-hero">'
                f'<div class="welcome-badge">{ICONS["upload"]}</div>'
                f'<h2>Attach your first document</h2>'
                f'<p>Upload any PDF report, study, or document to extract insights and ask questions in English or Roman Urdu.</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            with st.container():
                up_inline = st.file_uploader(
                    "Upload PDF to begin", type=["pdf"], key=f"inline_{st.session_state.uploader_n}",
                )
                if up_inline is not None:
                    if st.button("Index Document", type="primary", use_container_width=True):
                        with st.spinner("Uploading and indexing..."):
                            data, err = api(
                                "POST", f"/threads/{tid}/documents",
                                files={"file": (up_inline.name, up_inline.getvalue(), "application/pdf")},
                                timeout=120,
                            )
                        if not err:
                            st.session_state.uploader_n += 1
                            st.rerun()
        elif ready:
            st.markdown(
                f'<div class="welcome-hero">'
                f'<div class="welcome-badge">{ICONS["sparkles"]}</div>'
                f'<h2>What would you like to explore?</h2>'
                f'<p>Your document is indexed and ready. Select a suggested prompt or write your own below:</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            sc1, sc2, sc3 = st.columns(3)
            cols = [sc1, sc2, sc3]
            for n, q in enumerate(EXAMPLE_QUESTIONS):
                with cols[n % 3]:
                    st.markdown('<div class="suggestion-card">', unsafe_allow_html=True)
                    if st.button(q, key=f"chip_{n}", use_container_width=True):
                        st.session_state.pending_prompt = q
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        elif processing:
            st.info("Analyzing document structure and generating embeddings. Ready to answer in a few moments.")
            time.sleep(1.2)
            st.rerun()

    if prompt:
        send_question(thread, prompt.strip())
    elif st.session_state.messages:
        scroll_to_bottom()


def main():
    st.set_page_config(page_title="Document Intelligence", page_icon="📄", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    if not st.session_state.token:
        login_page()
        return
    ensure_models()
    chat_page()


if __name__ == "__main__":
    main()