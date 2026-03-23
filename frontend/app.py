"""
AI ChatBot — Streamlit Frontend
A ChatGPT-style chat interface that communicates with the FastAPI backend.
"""

import os
import uuid

import httpx
import streamlit as st

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="AI ChatBot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS for ChatGPT-style UI
# ──────────────────────────────────────────────

st.markdown("""
<style>
    /* Dark theme enhancements */
    .stApp {
        background-color: #0e1117;
    }

    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1c23;
        border-right: 1px solid #2d3139;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }

    .main-header h1 {
        font-size: 1.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }

    .main-header p {
        color: #8b949e;
        font-size: 0.9rem;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .status-online {
        background-color: #1a3a2a;
        color: #3fb950;
    }

    .status-offline {
        background-color: #3a1a1a;
        color: #f85149;
    }

    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #1a1c2e 0%, #1e2030 100%);
        border: 1px solid #2d3139;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }

    .welcome-card h3 {
        color: #e6edf3;
        margin-bottom: 0.5rem;
    }

    .welcome-card p {
        color: #8b949e;
        font-size: 0.9rem;
    }

    .feature-list {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }

    .feature-item {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session State Initialization
# ──────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = True


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def check_backend_health() -> dict | None:
    """Check if the backend is healthy."""
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def send_chat_message(message: str) -> dict | None:
    """Send a chat message to the backend and return the response."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "use_web_search": st.session_state.web_search_enabled,
            },
            timeout=60.0,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend error: {response.status_code} — {response.text}")
    except httpx.ConnectError:
        st.error("❌ Cannot connect to backend. Make sure it's running on " + BACKEND_URL)
    except httpx.TimeoutException:
        st.error("⏰ Request timed out. The model may be taking too long to respond.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
    return None


def clear_chat():
    """Clear chat history both locally and on the backend."""
    try:
        httpx.delete(
            f"{BACKEND_URL}/history/{st.session_state.session_id}",
            timeout=5.0,
        )
    except Exception:
        pass
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # Health check
    health = check_backend_health()
    if health:
        status_html = '<span class="status-badge status-online">● Online</span>'
        st.markdown(f"**Backend:** {status_html}", unsafe_allow_html=True)
        st.caption(f"Provider: `{health.get('llm_provider', 'unknown')}`")
        if health.get("web_search_available"):
            st.caption("🌐 Web search: available")
        else:
            st.caption("🌐 Web search: not configured")
    else:
        status_html = '<span class="status-badge status-offline">● Offline</span>'
        st.markdown(f"**Backend:** {status_html}", unsafe_allow_html=True)

    st.divider()

    # Web search toggle
    st.session_state.web_search_enabled = st.toggle(
        "🔍 Web Search",
        value=st.session_state.web_search_enabled,
        help="Augment responses with real-time web search results",
    )

    st.divider()

    # Clear chat
    if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
        clear_chat()
        st.rerun()

    # New session
    if st.button("✨ New Session", use_container_width=True, type="primary"):
        clear_chat()
        st.rerun()

    st.divider()

    # Session info
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    st.caption(f"Messages: {len(st.session_state.messages)}")


# ──────────────────────────────────────────────
# Main Chat Area
# ──────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>🤖 AI ChatBot</h1>
    <p>Context-aware conversations powered by LangChain & Groq</p>
</div>
""", unsafe_allow_html=True)

# Welcome message when no messages
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>👋 Welcome!</h3>
        <p>I'm your AI assistant with real-time web search capabilities.</p>
        <div class="feature-list">
            <div class="feature-item">💬 Multi-turn Memory</div>
            <div class="feature-item">🌐 Web Search</div>
            <div class="feature-item">⚡ Fast Inference</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if msg.get("web_search_used"):
            st.caption("🌐 Enhanced with web search")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            result = send_chat_message(prompt)

        if result:
            response_text = result["response"]
            st.markdown(response_text)
            if result.get("web_search_used"):
                st.caption("🌐 Enhanced with web search")

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "web_search_used": result.get("web_search_used", False),
            })
        else:
            error_msg = "Sorry, I couldn't generate a response. Please check the backend connection."
            st.markdown(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
            })
