"""
app.py — Streamlit AI Data Analysis Assistant.

Interactive chat interface for analyzing the CareerViet job dataset.
Uses OpenAI Assistants API for code generation and local execution for results.
Follows all requirements from AI_detail.md:
  - AI generates code + explanation (displayed, not auto-executed)
  - Human reviews, edits, and approves code before execution
  - Code runs locally only
  - All interactions are logged
"""

import os
import json
import base64
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from ai_agent import AIAgent
from code_executor import execute_code, JOBS_CSV, INDUSTRIES_CSV
from log_store import save_log, update_log, get_logs, get_logs_by_thread

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareerViet AI Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# Custom CSS for a polished chat UI
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---- Global ---- */
.block-container { padding-top: 1rem; }

/* ---- Chat bubbles ---- */
.user-msg {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}
.ai-msg {
    background: #f0f2f6;
    color: #1a1a2e;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    max-width: 90%;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* ---- Status badges ---- */
.status-pending {
    background: #fff3cd; color: #856404;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-executed {
    background: #d4edda; color: #155724;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-failed {
    background: #f8d7da; color: #721c24;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-rejected {
    background: #e2e3e5; color: #383d41;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}

/* ---- Code area ---- */
.code-container {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    margin: 8px 0;
}
.code-container.pending { border-color: #ffc107; }
.code-container.executed { border-color: #28a745; }
.code-container.failed { border-color: #dc3545; }

/* ---- Suggestion chips ---- */
.suggestion-chip {
    display: inline-block;
    padding: 6px 14px;
    margin: 4px;
    border-radius: 20px;
    background: linear-gradient(135deg, #667eea22, #764ba222);
    border: 1px solid #667eea44;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
}
.suggestion-chip:hover {
    background: linear-gradient(135deg, #667eea44, #764ba244);
    transform: translateY(-1px);
}

/* ---- Sidebar ---- */
.sidebar-section {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialization & auto-connect
# ---------------------------------------------------------------------------
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "agent": None,            # AIAgent instance
        "conversation_id": None,  # Current OpenAI conversation ID
        "messages": [],           # Chat history: list of dicts
        "is_connected": False,
        "connection_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def auto_connect():
    """Auto-connect to OpenAI using .env credentials on first load."""
    if st.session_state.is_connected:
        return  # Already connected

    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    base_url = os.getenv("OPENAI_BASE_URL", None)

    if not api_key:
        st.session_state.connection_error = (
            "OPENAI_API_KEY chưa được cấu hình trong file .env"
        )
        return

    try:
        agent = AIAgent(api_key=api_key, model=model, base_url=base_url)
        st.session_state.agent = agent
        st.session_state.is_connected = True
        st.session_state.connection_error = None
    except Exception as e:
        st.session_state.connection_error = str(e)


init_session_state()
auto_connect()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    """Render the sidebar with connection status, dataset info, and log history."""
    with st.sidebar:
        st.markdown("## 🤖 CareerViet AI Analyst")
        st.markdown("---")

        # ---- Connection status ----
        if st.session_state.is_connected:
            st.success("✅ Đã kết nối OpenAI (Responses API)")
            agent = st.session_state.agent
            if agent:
                st.markdown(f"**Model:** `{agent.model}`")
        elif st.session_state.connection_error:
            st.error(f"❌ {st.session_state.connection_error}")
            if st.button("🔄 Thử kết nối lại", use_container_width=True, type="primary"):
                st.session_state.is_connected = False
                st.session_state.connection_error = None
                st.rerun()
        else:
            st.warning("⏳ Đang kết nối...")

        st.markdown("---")

        # ---- New conversation ----
        if st.button("🔄 Cuộc hội thoại mới", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")

        # ---- Dataset info ----
        st.markdown("### 📊 Bộ dữ liệu")
        with st.expander("Xem thông tin dataset", expanded=False):
            try:
                df_preview = pd.read_csv(JOBS_CSV, nrows=5, encoding="utf-8-sig")
                st.markdown(f"**careerviet_all_jobs.csv**")
                df_full = pd.read_csv(JOBS_CSV, usecols=["job_id"], encoding="utf-8-sig")
                st.markdown(f"- Số dòng: `{len(df_full):,}`")
                st.markdown(f"- Số cột: `{len(df_preview.columns)}`")
                st.markdown(f"**Các cột:**")
                st.code(", ".join(df_preview.columns.tolist()), language=None)
            except Exception as e:
                st.error(f"Lỗi đọc dataset: {e}")

        st.markdown("---")

        # ---- Log history ----
        st.markdown("### 📜 Lịch sử")
        logs = get_logs(limit=10)
        if logs:
            for log in logs:
                status_emoji = {
                    "pending": "⏳", "executed": "✅",
                    "failed": "❌", "rejected": "🚫", "fixed": "🔧",
                }.get(log["status"], "❓")
                request_preview = (log["user_request"] or "")[:40]
                st.markdown(
                    f"{status_emoji} `{log['timestamp'][:16]}` — {request_preview}..."
                )
        else:
            st.markdown("_Chưa có lịch sử_")


# ---------------------------------------------------------------------------
# Message rendering
# ---------------------------------------------------------------------------
def render_message(msg: dict, msg_index: int):
    """Render a single chat message with code, approval buttons, and results."""
    role = msg["role"]

    if role == "user":
        st.markdown(
            f'<div class="user-msg">🧑 {msg["content"]}</div>',
            unsafe_allow_html=True,
        )
        return

    # ---- AI message ----
    st.markdown(
        f'<div class="ai-msg">🤖 <strong>AI Analyst</strong></div>',
        unsafe_allow_html=True,
    )

    # Explanation
    if msg.get("explanation"):
        st.markdown(msg["explanation"])

    # Code block (if present)
    code = msg.get("code")
    if code is not None:
        status = msg.get("status", "pending")
        status_labels = {
            "pending": ("⏳ Chờ duyệt", "status-pending"),
            "approved": ("✅ Đã duyệt", "status-executed"),
            "executed": ("✅ Đã thực thi", "status-executed"),
            "failed": ("❌ Lỗi", "status-failed"),
            "rejected": ("🚫 Đã từ chối", "status-rejected"),
            "fixed": ("🔧 Đã sửa", "status-executed"),
        }
        label, css_class = status_labels.get(status, ("❓", "status-pending"))
        st.markdown(f'<span class="{css_class}">{label}</span>', unsafe_allow_html=True)

        # Editable code area (only editable if pending)
        if status == "pending":
            edited_code = st.text_area(
                "📝 Code (có thể chỉnh sửa trước khi duyệt):",
                value=code,
                height=300,
                key=f"code_editor_{msg_index}",
                label_visibility="visible",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "✅ Duyệt & Chạy",
                    key=f"approve_{msg_index}",
                    type="primary",
                    use_container_width=True,
                ):
                    _execute_approved_code(msg_index, edited_code)

            with col2:
                if st.button(
                    "❌ Từ chối",
                    key=f"reject_{msg_index}",
                    use_container_width=True,
                ):
                    st.session_state.messages[msg_index]["status"] = "rejected"
                    if msg.get("log_id"):
                        update_log(msg["log_id"], status="rejected")
                    st.rerun()
        else:
            # Non-editable display for already-processed code
            st.code(code, language="python")

    # ---- Execution results ----
    exec_result = msg.get("exec_result")
    if exec_result:
        if exec_result["success"]:
            # Stdout
            if exec_result.get("stdout"):
                with st.expander("📋 Output", expanded=True):
                    st.code(exec_result["stdout"], language=None)

            # Matplotlib figures
            for i, fig_b64 in enumerate(exec_result.get("figures", [])):
                st.image(
                    base64.b64decode(fig_b64),
                    caption=f"Biểu đồ {i + 1}",
                    use_container_width=True,
                )

            # Plotly figures
            for fig in exec_result.get("plotly_figures", []):
                st.plotly_chart(fig, use_container_width=True)

            # Tables
            for table_info in exec_result.get("tables", []):
                st.markdown(f"**📊 {table_info['name']}** ({table_info['total_rows']:,} dòng"
                          + (" — hiển thị 500 dòng đầu" if table_info.get("truncated") else "")
                          + ")")
                st.dataframe(table_info["data"], use_container_width=True)

        else:
            # Error display
            st.error("❌ Code thực thi bị lỗi!")
            with st.expander("🔍 Chi tiết lỗi", expanded=True):
                st.code(exec_result.get("error_traceback", "Unknown error"), language=None)

            # Fix buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "🔧 Sửa lỗi với AI",
                    key=f"fix_{msg_index}",
                    type="primary",
                    use_container_width=True,
                ):
                    _request_ai_fix(msg_index)
            with col2:
                if st.button(
                    "✏️ Sửa thủ công",
                    key=f"manual_fix_{msg_index}",
                    use_container_width=True,
                ):
                    # Reset to pending so user can edit
                    st.session_state.messages[msg_index]["status"] = "pending"
                    if msg.get("log_id"):
                        update_log(msg["log_id"], status="pending")
                    st.rerun()


def _execute_approved_code(msg_index: int, code: str):
    """Execute approved code and update the message with results."""
    msg = st.session_state.messages[msg_index]
    msg["code"] = code  # Save potentially edited code
    msg["status"] = "approved"

    with st.spinner("⚙️ Đang thực thi code..."):
        result = execute_code(code)

    msg["exec_result"] = result

    if result["success"]:
        msg["status"] = "executed"
        if msg.get("log_id"):
            update_log(
                msg["log_id"],
                edited_code=code,
                execution_result=json.dumps({
                    "stdout": result["stdout"],
                    "figures_count": len(result.get("figures", [])),
                    "tables_count": len(result.get("tables", [])),
                }, ensure_ascii=False),
                status="executed",
            )
    else:
        msg["status"] = "failed"
        if msg.get("log_id"):
            update_log(
                msg["log_id"],
                edited_code=code,
                error_traceback=result.get("error_traceback", ""),
                status="failed",
            )

    st.rerun()


def _request_ai_fix(msg_index: int):
    """Send the error back to AI for a fix."""
    msg = st.session_state.messages[msg_index]
    agent = st.session_state.agent
    conversation_id = st.session_state.conversation_id

    if not agent or not conversation_id:
        st.error("Chưa kết nối với AI!")
        return

    code = msg.get("code", "")
    error_tb = msg.get("exec_result", {}).get("error_traceback", "Unknown error")

    with st.spinner("🔧 AI đang phân tích lỗi và sửa code..."):
        response = agent.request_fix(conversation_id, code, error_tb)

    # Mark old message as failed
    msg["status"] = "failed"

    # Add the fix as a new AI message
    fix_msg = {
        "role": "assistant",
        "content": response["raw_response"],
        "explanation": "🔧 **Sửa lỗi:**\n\n" + response["explanation"],
        "code": response["code"],
        "status": "pending" if response["code"] else "executed",
        "exec_result": None,
    }

    # Save to logs
    log_id = save_log(
        thread_id=conversation_id,
        user_request=f"[Auto-fix] Sửa lỗi code",
        ai_explanation=response["explanation"],
        generated_code=response["code"] or "",
        status="pending" if response["code"] else "executed",
    )
    fix_msg["log_id"] = log_id

    st.session_state.messages.append(fix_msg)
    st.rerun()


# ---------------------------------------------------------------------------
# Main chat input handler
# ---------------------------------------------------------------------------
def handle_user_input(user_input: str):
    """Process a new user message."""
    agent = st.session_state.agent
    if not agent:
        st.error("⚠️ Vui lòng kết nối với OpenAI trước!")
        return

    # Create conversation if needed
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = agent.create_conversation()

    conversation_id = st.session_state.conversation_id

    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
    })

    # Get AI response
    with st.spinner("🤖 AI đang suy nghĩ..."):
        response = agent.send_message(conversation_id, user_input)

    # Add AI message to chat
    ai_msg = {
        "role": "assistant",
        "content": response["raw_response"],
        "explanation": response["explanation"],
        "code": response["code"],
        "status": "pending" if response["code"] else "executed",
        "exec_result": None,
    }

    # Save to logs
    log_id = save_log(
        thread_id=conversation_id,
        user_request=user_input,
        ai_explanation=response["explanation"],
        generated_code=response["code"] or "",
        status="pending" if response["code"] else "executed",
    )
    ai_msg["log_id"] = log_id

    st.session_state.messages.append(ai_msg)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    """Main application entry point."""
    render_sidebar()

    # ---- Header ----
    st.markdown("# 🤖 CareerViet AI Data Analyst")
    st.markdown(
        "Trợ lý phân tích dữ liệu tuyển dụng CareerViet. "
        "Hỏi bất kỳ câu hỏi phân tích nào — AI sẽ viết code, "
        "bạn duyệt và chạy trên dữ liệu thực."
    )

    if not st.session_state.is_connected:
        if st.session_state.connection_error:
            st.error(f"❌ Lỗi kết nối: {st.session_state.connection_error}")
        else:
            st.info("⏳ Đang kết nối với OpenAI...")
        return

    st.markdown("---")

    # ---- Chat history ----
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            # Welcome + suggestions
            st.markdown("### 💡 Gợi ý phân tích")
            suggestions = [
                "Phân tích mức lương trung bình theo ngành nghề",
                "Top 10 công ty tuyển dụng nhiều nhất",
                "Phân bố địa điểm làm việc trên cả nước",
                "Xu hướng tuyển dụng theo thời gian",
                "Phân tích yêu cầu kinh nghiệm theo ngành",
                "So sánh lương giữa các thành phố lớn",
            ]
            cols = st.columns(3)
            for i, suggestion in enumerate(suggestions):
                with cols[i % 3]:
                    if st.button(
                        f"💡 {suggestion}",
                        key=f"suggest_{i}",
                        use_container_width=True,
                    ):
                        handle_user_input(suggestion)
                        st.rerun()
        else:
            # Render all messages
            for i, msg in enumerate(st.session_state.messages):
                render_message(msg, i)

    # ---- Input area ----
    st.markdown("---")
    user_input = st.chat_input(
        "Nhập câu hỏi phân tích...",
        key="chat_input",
    )
    if user_input:
        handle_user_input(user_input)
        st.rerun()


if __name__ == "__main__":
    main()
