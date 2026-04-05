"""
Video Chat App — streamlit_app.py
A polished video analysis chat interface built with Streamlit.
"""

import streamlit as st
import os
import time
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

from modules.video_analysis_engine import VideoAnalysisEngine
from modules.sqlite_handler import SQLiteHandler
from modules.db_handler import DBHandler

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("video_chat_app")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Video Chat",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base typography ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Chrome cleanup ── */
#MainMenu, footer, header { visibility: hidden; }
.main .block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 6rem !important;
    max-width: 880px !important;
}

/* ══════════════════ SIDEBAR ══════════════════ */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.13) !important;
}
[data-testid="stSidebar"] > div {
    padding: 1.2rem 0.8rem 1rem !important;
}

/* All sidebar buttons → ghost / flat */
section[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start !important;
    text-align: left !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    padding: 0.38rem 0.65rem !important;
    border-radius: 8px !important;
    border: none !important;
    background: transparent !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    color: inherit !important;
    box-shadow: none !important;
    transition: background 0.14s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(128,128,128,0.1) !important;
}
/* Active video item */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(108,99,255,0.15) !important;
    color: #7C73FF !important;
    font-weight: 500 !important;
}

/* ── New-chat button — purple pill ── */
div.nchat-wrap .stButton > button {
    background: #6C63FF !important;
    color: #fff !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    padding: 0.52rem 1rem !important;
    justify-content: center !important;
    text-align: center !important;
    box-shadow: 0 2px 12px rgba(108,99,255,0.30) !important;
    border: none !important;
    transition: opacity 0.15s, box-shadow 0.15s !important;
}
div.nchat-wrap .stButton > button:hover {
    opacity: 0.88 !important;
    box-shadow: 0 4px 16px rgba(108,99,255,0.40) !important;
}

/* ── Sidebar popover trigger ── */
section[data-testid="stSidebar"] [data-testid="stPopover"] > button {
    padding: 0.18rem 0.44rem !important;
    font-size: 1.05rem !important;
    background: transparent !important;
    border: none !important;
    opacity: 0.3 !important;
    box-shadow: none !important;
    transition: opacity 0.14s !important;
}
section[data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
    opacity: 0.8 !important;
    background: rgba(128,128,128,0.1) !important;
}
[data-baseweb="popover"] .stButton > button { color: #e53e3e !important; }

/* ── Section label ── */
p.slabel {
    font-size: 0.66rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    opacity: 0.36 !important;
    margin: 0.75rem 0 0.3rem 0.45rem !important;
    line-height: 1 !important;
}

/* ══════════════════ FEATURE CARDS ══════════════════ */
div.fcard {
    background: rgba(128,128,128,0.05);
    border: 1px solid rgba(128,128,128,0.12);
    border-radius: 14px;
    padding: 1.35rem 1rem 1.15rem;
    text-align: center;
    height: 100%;
    transition: border-color 0.2s ease, background 0.2s ease;
}
div.fcard:hover {
    border-color: rgba(108,99,255,0.30);
    background: rgba(108,99,255,0.045);
}
div.fcard .fi  { font-size: 1.65rem; display: block; margin-bottom: 0.6rem; line-height: 1; }
div.fcard .ft  { font-size: 0.875rem; font-weight: 600; display: block; margin-bottom: 0.3rem; }
div.fcard .fd  { font-size: 0.75rem; opacity: 0.50; line-height: 1.55; margin: 0; }

/* ══════════════════ SUGGESTION CHIPS ══════════════════ */
div.chips .stButton > button {
    background: rgba(128,128,128,0.07) !important;
    border: 1px solid rgba(128,128,128,0.17) !important;
    border-radius: 100px !important;
    font-size: 0.8rem !important;
    font-weight: 400 !important;
    padding: 0.32rem 1rem !important;
    color: inherit !important;
    text-align: center !important;
    justify-content: center !important;
    box-shadow: none !important;
    transition: border-color 0.14s, background 0.14s !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div.chips .stButton > button:hover {
    border-color: rgba(108,99,255,0.42) !important;
    background: rgba(108,99,255,0.07) !important;
}

/* ══════════════════ MAIN AREA BUTTONS ══════════════════ */
.main .stButton > button[kind="primary"] {
    background: #6C63FF !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 10px rgba(108,99,255,0.28) !important;
    transition: opacity 0.15s !important;
}
.main .stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }
.main .stButton > button[kind="secondary"]     { border-radius: 10px !important; }

/* ══════════════════ CHAT ══════════════════ */
[data-testid="stChatMessage"] { padding: 0.45rem 0 !important; }
[data-testid="stChatMessage"] p { font-size: 0.91rem !important; line-height: 1.68 !important; }
[data-testid="stChatInput"] > div { border-radius: 14px !important; }

/* ══════════════════ MISC ══════════════════ */
[data-testid="stProgressBar"] > div { border-radius: 100px !important; overflow: hidden; }
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #6C63FF, #a78bfa) !important;
    border-radius: 100px !important;
}
[data-testid="stStatus"]              { border-radius: 12px !important; }
[data-testid="stFileUploaderDropzone"]{ border-radius: 14px !important; }
.stTextInput input                    { border-radius: 10px !important; }
hr                                    { margin: 0.55rem 0 !important; opacity: 0.1 !important; }
[data-testid="stAlert"]               { border-radius: 10px !important; }
[data-testid="stExpander"]            { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ── Cached resources ──────────────────────────────────────────────────────────
@st.cache_resource
def get_sqlite():
    return SQLiteHandler()

@st.cache_resource
def get_db():
    return DBHandler(
        host=os.getenv("CHROMADB_HOST", "localhost"),
        port=int(os.getenv("CHROMADB_PORT", 8000)),
    )

@st.cache_resource(show_spinner=False)
def get_engine():
    logger.info("Loading VideoAnalysisEngine…")
    return VideoAnalysisEngine()

sqlite_handler = get_sqlite()
db_handler     = get_db()

# ── Session state ─────────────────────────────────────────────────────────────
_defaults = dict(
    messages=[],
    selected_video=None,
    selected_video_name="",
    view="home",
)
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go_home():
    st.session_state.update(
        selected_video=None,
        selected_video_name="",
        messages=[],
        view="home",
    )


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Brand header
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.65rem;
                padding:0 0.3rem 0.15rem;margin-bottom:0.25rem">
        <span style="font-size:1.45rem;line-height:1">🎬</span>
        <div>
            <div style="font-size:0.98rem;font-weight:700;
                        letter-spacing:-0.3px;line-height:1.25">Video Chat</div>
            <div style="font-size:0.68rem;opacity:0.42;font-weight:400">
                Powered by Groq AI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.55rem'></div>", unsafe_allow_html=True)

    # New Chat — purple pill
    st.markdown("<div class='nchat-wrap'>", unsafe_allow_html=True)
    if st.button("New Chat", icon=":material/add:", use_container_width=True):
        go_home()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Library heading + count
    all_videos = sqlite_handler.get_videos()
    col_lbl, col_cnt = st.columns([0.75, 0.25])
    with col_lbl:
        st.markdown("<p class='slabel'>Library</p>", unsafe_allow_html=True)
    with col_cnt:
        st.markdown(
            f"<div style='margin-top:0.78rem;text-align:right;"
            f"font-size:0.68rem;opacity:0.38;font-weight:600'>{len(all_videos)}</div>",
            unsafe_allow_html=True,
        )

    if not all_videos:
        st.markdown(
            "<div style='font-size:0.77rem;opacity:0.38;padding:0.3rem 0.5rem'>"
            "No videos yet. Upload one below.</div>",
            unsafe_allow_html=True,
        )
    else:
        query = st.text_input(
            "search",
            placeholder="Search library…",
            label_visibility="collapsed",
        )
        videos = (
            [v for v in all_videos if query.lower() in v["smart_title"].lower()]
            if query else all_videos
        )

        for video in videos:
            is_sel = st.session_state.selected_video == video["uuid"]

            # 3 columns: left color strip, main button, tiny delete icon
            col_strip, col_btn, col_del = st.columns([0.04, 0.80, 0.16], gap="small")

            # Left accent strip when selected
            with col_strip:
                if is_sel:
                    st.markdown(
                        "<div style='width:3px;height:30px;border-radius:999px;"
                        "background:#6C63FF;'></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.write("")

            # Main video button
            with col_btn:
                if st.button(
                    video["smart_title"],
                    key=f"v_{video['uuid']}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                    icon=":material/play_arrow:" if is_sel else ":material/movie:",
                ):
                    st.session_state.update(
                        selected_video=video["uuid"],
                        selected_video_name=video["smart_title"],
                        messages=[],
                        view="chat",
                    )
                    logger.info("Selected: %s", video["smart_title"])
                    st.rerun()

            # Minimal trash icon (no popover, just click‑to‑delete)
            with col_del:
                # Tiny icon‑style button using markdown + on_click style
                delete_clicked = st.button(
                    "🗑",
                    key=f"d_{video['uuid']}",
                    help="Delete video",
                )
                if delete_clicked:
                    try:
                        sqlite_handler.delete_video(video["uuid"])
                        db_handler.delete_video(video["uuid"])
                        if st.session_state.selected_video == video["uuid"]:
                            go_home()
                        logger.info("Deleted: %s", video["uuid"])
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


            # with col_pop:
            #     with st.popover("⋯"):
            #         st.caption(video["smart_title"])
            #         if st.button(
            #             "Delete",
            #             icon=":material/delete:",
            #             key=f"d_{video['uuid']}",
            #             use_container_width=True,
            #         ):
            #             try:
            #                 sqlite_handler.delete_video(video["uuid"])
            #                 db_handler.delete_video(video["uuid"])
            #                 if st.session_state.selected_video == video["uuid"]:
            #                     go_home()
            #                 logger.info("Deleted: %s", video["uuid"])
            #                 st.rerun()
            #             except Exception as exc:
            #                 st.error(str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# HOME / UPLOAD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "home":

    # Hero
    st.markdown("""
    <div style="text-align:center;padding:2.8rem 1rem 1.8rem">
        <div style="font-size:2.6rem;line-height:1;margin-bottom:0.9rem">🎬</div>
        <h1 style="font-size:1.95rem;font-weight:700;letter-spacing:-0.5px;margin:0 0 0.5rem">
            Video Chat
        </h1>
        <p style="font-size:0.95rem;opacity:0.52;margin:0;max-width:420px;
                  margin-inline:auto;line-height:1.6">
            Upload a video. Ask anything about it in plain English.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # File uploader
    uploaded_file = st.file_uploader(
        "Drop a video here, or click to browse",
        type=["mp4", "mov", "avi", "mkv", "webm"],
    )

    if uploaded_file:
        with st.container(border=True):
            col_info, col_btn = st.columns(
                [0.72, 0.28], gap="medium", vertical_alignment="center"
            )
            with col_info:
                size_mb = uploaded_file.size / 1_048_576
                st.markdown(
                    f"**{uploaded_file.name}**&nbsp;&nbsp;"
                    f"<span style='font-size:0.78rem;opacity:0.50'>"
                    f"{size_mb:.1f} MB &nbsp;·&nbsp; Ready</span>",
                    unsafe_allow_html=True,
                )
            with col_btn:
                process = st.button(
                    "Process",
                    icon=":material/play_arrow:",
                    type="primary",
                    use_container_width=True,
                )

        if process:
            temp_dir  = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as fh:
                fh.write(uploaded_file.getbuffer())

            try:
                prog = st.progress(0, text="Starting…")

                try:
                    engine = get_engine()
                    prog.progress(10, text="AI engine loaded.")
                except Exception as eng_exc:
                    st.error(f"Failed to load AI engine: {eng_exc}")
                    logger.error("Engine load error: %s", eng_exc, exc_info=True)
                    st.stop()

                logger.info("Processing: %s", uploaded_file.name)
                with st.status("Analysing video frames…", expanded=True) as status:
                    st.write(f"Running AI analysis on **{uploaded_file.name}**…")
                    try:
                        result = engine.process_video_sync(file_path)
                    except Exception as proc_exc:
                        status.update(label="Processing failed", state="error", expanded=True)
                        st.error(f"Video processing error: {proc_exc}")
                        logger.error("Processing error: %s", proc_exc, exc_info=True)
                        raise

                    prog.progress(90, text="Storing results…")
                    title  = result.get("smart_title", uploaded_file.name)
                    alerts = result.get("alerts", [])
                    status.update(label=f"✅  Done — {title}", state="complete", expanded=False)
                    logger.info("Done: '%s'. Alerts: %d", title, len(alerts))

                prog.progress(100, text="Complete!")
                time.sleep(0.4)
                prog.empty()

                if alerts:
                    st.warning(f"⚠️  {len(alerts)} alert(s) detected during analysis.")

                latest = sqlite_handler.get_videos()
                if latest:
                    st.session_state.update(
                        selected_video=latest[0]["uuid"],
                        selected_video_name=latest[0]["smart_title"],
                        messages=[],
                        view="chat",
                    )
                st.rerun()

            except Exception as exc:
                if "proc_exc" not in dir():
                    st.error(f"Unexpected error: {exc}")
                    logger.error("Unexpected processing error: %s", exc, exc_info=True)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

    else:
        # Feature cards
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="medium")
        cards = [
            ("🔍", "Frame Analysis",
             "AI vision model scans every frame and extracts detailed descriptions."),
            ("💬", "Natural Language",
             "Ask questions in plain English — get context-aware answers instantly."),
            ("⚡", "Groq Speed",
             "LLaMA-4 Scout on Groq's LPU — responses at ~400 tokens / sec."),
        ]
        for col, (icon, title, desc) in zip([c1, c2, c3], cards):
            with col:
                st.markdown(
                    f"<div class='fcard'>"
                    f"<span class='fi'>{icon}</span>"
                    f"<span class='ft'>{title}</span>"
                    f"<p class='fd'>{desc}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

        with st.expander("How it works", icon=":material/info:"):
            st.markdown("""
1. **Upload** any MP4, MOV, AVI, MKV, or WebM video (up to ~2 GB).
2. The app samples frames, describes them with an AI vision model, and stores results in ChromaDB.
3. **Select** the video from the sidebar library.
4. **Chat** — ask anything about the video. Questions are answered using semantic search over frame descriptions.
            """)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.view == "chat":

    name   = st.session_state.selected_video_name
    vid_id = st.session_state.selected_video

    # Chat header
    col_title, col_clear = st.columns([0.80, 0.20], gap="small", vertical_alignment="center")
    with col_title:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:0.55rem;padding:0.2rem 0">
                <span style="font-size:1rem">🎬</span>
                <span style="font-size:0.97rem;font-weight:600;letter-spacing:-0.2px;
                             white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                             max-width:500px;display:inline-block">{name}</span>
                <span style="display:inline-flex;align-items:center;gap:3px;
                             font-size:0.65rem;font-weight:500;padding:0.16rem 0.5rem;
                             border-radius:100px;background:rgba(34,197,94,0.10);
                             color:#22c55e;border:1px solid rgba(34,197,94,0.22);
                             white-space:nowrap;flex-shrink:0">● Active</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_clear:
        if st.button(
            "Clear",
            icon=":material/refresh:",
            use_container_width=True,
            key="clear_chat",
        ):
            st.session_state.messages = []
            st.rerun()

    st.divider()

    # Empty state — suggestion chips
    if not st.session_state.messages:
        st.markdown(
            "<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.07em;"
            "text-transform:uppercase;opacity:0.38;margin-bottom:0.55rem'>"
            "Suggested questions</p>",
            unsafe_allow_html=True,
        )
        suggestions = [
            "How many people appear in the video?",
            "What activities are happening?",
            "Is there any suspicious behaviour?",
            "Describe the environment and setting.",
        ]
        st.markdown("<div class='chips'>", unsafe_allow_html=True)
        for i in range(0, len(suggestions), 2):
            cc = st.columns(2, gap="small")
            for j, col in enumerate(cc):
                idx = i + j
                if idx < len(suggestions):
                    with col:
                        if st.button(
                            suggestions[idx],
                            use_container_width=True,
                            key=f"chip_{idx}",
                        ):
                            st.session_state.messages.append(
                                {"role": "user", "content": suggestions[idx]}
                            )
                            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Conversation history
    for msg in st.session_state.messages:
        avatar = ":material/person:" if msg["role"] == "user" else ":material/smart_toy:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Generate assistant reply
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_q = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            with st.status("Searching video memory…", expanded=False) as status:
                try:
                    engine  = get_engine()
                    t0      = time.time()
                    logger.info("Query → %s", last_q)
                    answer  = engine.query_video_sync(vid_id, last_q)
                    elapsed = time.time() - t0
                    logger.info("Response in %.2fs", elapsed)
                    status.update(
                        label=f"Done in {elapsed:.1f}s",
                        state="complete",
                        expanded=False,
                    )
                except Exception as exc:
                    err_detail = str(exc)
                    answer = f"❌ Query failed: {err_detail}"
                    status.update(label="Error", state="error", expanded=True)
                    st.error(f"Query error: {err_detail}")
                    logger.error("Query error: %s", exc, exc_info=True)
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # Chat input (pinned to viewport bottom by Streamlit)
    if prompt := st.chat_input(f'Ask about "{name}"…'):
        st.session_state.messages.append({"role": "user", "content": prompt})
        logger.info("User → %s", prompt)
        st.rerun()
