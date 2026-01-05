import streamlit as st
import io
import os
import time
import logging
import sys
import shutil
from PIL import Image

from modules.video_analysis_engine import VideoAnalysisEngine      
from modules.sqlite_handler import SQLiteHandler
from modules.db_handler import DBHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

st.set_page_config(
    page_title="Drone Security Agent - Powered by Groq",
    layout="wide",
    page_icon="🚁",
    initial_sidebar_state="expanded"
)

# Modern CSS Framework
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* App Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
    }
    
    /* Sidebar Modern Design */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }
    [data-testid="stSidebar"] .stMarkdown h1 {
        color: #f1f5f9 !important;
        font-weight: 700;
        font-size: 1.5rem;
        margin-bottom: 0.25rem;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f1f5f9 !important;
        font-weight: 600;
    }
    
    /* Main Content Container */
    .main .block-container {
        max-width: 1200px;
        padding: 2rem 3rem;
    }
    
    /* Modern Card Design */
    .modern-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 1.5rem;
    }
    
    /* Chat Container */
    [data-testid="stVerticalBlock"] > div:has(.chat-message) {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* Chat Messages - Modern Bubbles */
    .chat-message {
        padding: 1rem 1.25rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    }
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .chat-message.user {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        margin-left: auto;
        max-width: 85%;
    }
    .chat-message.bot {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        margin-right: auto;
        max-width: 85%;
    }
    .chat-message * {
        color: #ffffff !important;
        line-height: 1.6;
    }
    
    /* Avatar */
    .avatar {
        width: 2.25rem;
        height: 2.25rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    .avatar.user {
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
    }
    .avatar.bot {
        background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.6);
        transition: all 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        border-color: #3b82f6;
    }
    .feature-card h3 {
        color: #1e293b !important;
        font-size: 1.25rem;
        font-weight: 600;
        margin: 1rem 0 0.75rem 0;
    }
    .feature-card p {
        color: #64748b !important;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0;
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Buttons Override */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
    }
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #64748b 0%, #475569 100%);
        box-shadow: 0 2px 8px rgba(100, 116, 139, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    /* Info/Success/Warning boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        backdrop-filter: blur(10px);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: white;
    }
    
    /* Dividers */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: rgba(148, 163, 184, 0.2);
    }
    
    /* Welcome Screen */
    .welcome-container {
        text-align: center;
        padding: 3rem 2rem;
    }
    .welcome-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .welcome-subtitle {
        font-size: 1.25rem;
        color: #64748b;
        font-weight: 400;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Lightweight Handlers (Instant Load)
@st.cache_resource
def get_sqlite_handler():
    return SQLiteHandler()

@st.cache_resource
def get_db_handler():
    return DBHandler(host=os.getenv("CHROMADB_HOST", "localhost"), port=int(os.getenv("CHROMADB_PORT", 8000)))

sqlite_handler = get_sqlite_handler()
db_handler = get_db_handler()

# Initialize Heavy Engine (Lazy Load)
@st.cache_resource(show_spinner=False)
def get_engine():
    print("DEBUG: Initializing VideoAnalysisEngine (Heavy Load)...")
    return VideoAnalysisEngine()

# Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None
if 'selected_video_name' not in st.session_state:
    st.session_state.selected_video_name = ""

# Sidebar
with st.sidebar:
    st.title("🚁 Drone Security")
    st.caption("Powered by Groq AI")
    
    # Stats Section
    videos = sqlite_handler.get_videos()
    st.metric("Total Videos", len(videos))
    
    st.divider()
    
    # Upload
    st.subheader("📤 Upload Video")
    uploaded_file = st.file_uploader(
        "Select a video file",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        help="Upload drone footage for AI analysis"
    )
    if uploaded_file is not None:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
        if st.button("🚀 Process Video", use_container_width=True, type="primary"):
            # Load engine only when needed
            with st.spinner("Initializing AI Engine..."):
                engine = get_engine()
                
            with st.spinner("Processing video... This may take a while."):
                print(f"DEBUG: Starting processing for {uploaded_file.name}")
                
                # Save to temp file
                temp_dir = "temp_uploads"
                os.makedirs(temp_dir, exist_ok=True)
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    result = engine.process_video(file_path)
                    st.success("Processing complete!")
                    print(f"DEBUG: Finished processing {uploaded_file.name}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing video: {e}")
                    print(f"DEBUG: Error processing video: {e}")
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

    st.divider()
    
    # Video List from SQLite (Fast)
    st.subheader("📚 Video Library")
    videos = sqlite_handler.get_videos()
    
    if not videos:
        st.info("📭 No videos yet. Upload one to get started!")
    else:
        # Search/filter
        search = st.text_input("🔍 Search videos", placeholder="Search by title...")
        filtered_videos = [v for v in videos if search.lower() in v['smart_title'].lower()] if search else videos
        
        st.caption(f"Showing {len(filtered_videos)} of {len(videos)} videos")
        
        for video in filtered_videos:
            with st.container():
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    is_selected = st.session_state.selected_video == video['uuid']
                    button_type = "primary" if is_selected else "secondary"
                    if st.button(
                        f"{'▶️' if is_selected else '🎬'} {video['smart_title']}",
                        key=video['uuid'],
                        use_container_width=True,
                        type=button_type
                    ):
                        st.session_state.selected_video = video['uuid']
                        st.session_state.selected_video_name = video['smart_title']
                        st.session_state.messages = []
                        logging.info(f"Selected video: {video['smart_title']}")
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{video['uuid']}", help="Delete video"):
                        logging.info(f"Deleting video: {video['uuid']}")
                        try:
                            sqlite_handler.delete_video(video['uuid'])
                            db_handler.delete_video(video['uuid'])
                            
                            if st.session_state.selected_video == video['uuid']:
                                st.session_state.selected_video = None
                                st.session_state.messages = []
                            st.success("Video deleted!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            logging.error(f"Delete error: {e}")

# Main Chat Interface
if st.session_state.selected_video:
    # Modern Header
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h1 style="margin: 0; font-size: 1.75rem; color: #1e293b;">🎬 {st.session_state.selected_video_name}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748b; font-size: 0.875rem;">Video ID: {st.session_state.selected_video}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Clear", help="Start new conversation", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()
    
    # Chat Container with Modern Design
    chat_container = st.container(height=500)
    
    with chat_container:
        if not st.session_state.messages:
            # Welcome message in chat
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                <h3 style="color: #475569; font-weight: 600;">Start a Conversation</h3>
                <p style="color: #64748b; margin-bottom: 2rem;">Ask questions about the video content, people, activities, or suspicious behavior</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Modern Suggested Questions
            st.markdown('<p style="color: #475569; font-weight: 600; margin-bottom: 1rem;">💡 Try asking:</p>', unsafe_allow_html=True)
            suggestions = [
                ("👥", "How many people are in the video?"),
                ("🏃", "What activities are taking place?"),
                ("⚠️", "Is there any suspicious behavior?"),
                ("🏞️", "Describe the environment and setting.")
            ]
            cols = st.columns(2, gap="medium")
            for idx, (icon, suggestion) in enumerate(suggestions):
                with cols[idx % 2]:
                    if st.button(f"{icon} {suggestion}", key=f"sug_{idx}", use_container_width=True):
                        st.session_state.messages.append({"role": "user", "content": suggestion})
                        st.rerun()
            
        for idx, msg in enumerate(st.session_state.messages):
            role_class = "user" if msg["role"] == "user" else "bot"
            avatar_char = "👤" if msg["role"] == "user" else "🤖"
            role_name = "You" if msg["role"] == "user" else "Groq AI"
            
            st.markdown(f"""
            <div class="chat-message {role_class}">
                <div class="avatar {role_class}">{avatar_char}</div>
                <div style="flex: 1;">
                    <div style="font-weight: bold; margin-bottom: 0.5rem; font-size: 0.9rem;">
                        {role_name}
                    </div>
                    <div style="line-height: 1.6;">
                        {msg['content']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Input area (using st.chat_input for better UI)
    if prompt := st.chat_input("💭 Ask anything about this video...", key="chat_input"):
        logging.info(f"User query: {prompt}")
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Handle response generation after rerun to update UI first
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_user_msg = st.session_state.messages[-1]["content"]
        
        # Load engine only when needed
        with st.spinner("🔄 Initializing Groq AI Engine..."):
            engine = get_engine()
            
        with st.spinner("🤔 Analyzing with Groq AI..."):
            try:
                start_time = time.time()
                answer = engine.query_video(st.session_state.selected_video, last_user_msg)
                elapsed = time.time() - start_time
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"{answer}\n\n*Response time: {elapsed:.2f}s*"
                })
                logging.info(f"AI response generated in {elapsed:.2f}s")
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}\n\nPlease try again or rephrase your question."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                logging.error(f"Query error: {e}")
        st.rerun()

else:
    # Modern Welcome Screen
    st.markdown("""
    <div class="welcome-container">
        <div style="font-size: 5rem; margin-bottom: 1rem;">🚁</div>
        <h1 class="welcome-title">Drone Security Agent</h1>
        <p class="welcome-subtitle">AI-Powered Video Analysis with Groq</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3>Smart Analysis</h3>
            <p>Advanced AI analyzes video frames to detect people, activities, and suspicious behavior in real-time.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <h3>Interactive Chat</h3>
            <p>Ask natural language questions about your videos and get instant AI-powered answers.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>Powered by Groq</h3>
            <p>Lightning-fast inference using Groq's LPU technology for real-time analysis.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Getting Started Section
    st.markdown("""
    <div class="modern-card">
        <h2 style="color: #1e293b; margin-bottom: 1rem;">🚀 Getting Started</h2>
        <div style="color: #475569; line-height: 1.8;">
            <p style="margin-bottom: 0.75rem;"><strong>1. Upload a video</strong> using the sidebar uploader</p>
            <p style="margin-bottom: 0.75rem;"><strong>2. Wait for processing</strong> - AI will analyze all frames</p>
            <p style="margin-bottom: 0.75rem;"><strong>3. Select the video</strong> from the library</p>
            <p style="margin-bottom: 0;"><strong>4. Ask questions</strong> about the content, people, or activities</p>
        </div>
        <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 1.5rem; margin-bottom: 0;">
            💡 Video processing time depends on video length and quality
        </p>
    </div>
    """, unsafe_allow_html=True)
