"""
CloudPSS Task-Oriented Web Portal

A task-oriented web interface for CloudPSS power system simulation.
Each task has its own page with: config preview → edit → confirm → execute → results.
"""
import sys
from pathlib import Path

# Ensure smart_config is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import streamlit as st

from web.core import task_store, skill_catalog


# ─── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="CloudPSS 仿真工作台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Token Check ───────────────────────────────────────────────────────
def check_token():
    """Check if CloudPSS token is available."""
    token_paths = [
        PROJECT_ROOT / ".cloudpss_token",
        Path.home() / ".cloudpss_token",
    ]
    for p in token_paths:
        if p.exists() and p.read_text().strip():
            return True
    return False


if not check_token():
    st.warning("⚠️ 未检测到 CloudPSS Token")
    st.info(
        "请先配置 Token：\n\n"
        "1. 访问 https://www.cloudpss.net 或内部服务器\n"
        "2. 登录 → 个人中心 → API Token\n"
        "3. 将 Token 保存到项目根目录：\n\n"
        '```bash\n'
        'echo "your_token" > .cloudpss_token\n'
        "```\n\n"
        "配置完成后可继续使用。"
    )

# ─── Session State Init ───────────────────────────────────────────────
if "skills_loaded" not in st.session_state:
    try:
        skill_catalog.list_all()
        st.session_state.skills_loaded = True
    except Exception:
        st.session_state.skills_loaded = False

if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

if "page" not in st.session_state:
    st.session_state.page = "create"

# ─── Load Saved Settings ─────────────────────────────────────────────
try:
    from web.components.settings import load_settings, apply_settings
    saved_settings = load_settings()
    if saved_settings:
        apply_settings(saved_settings)
except Exception:
    pass  # Settings will be configured by user later

# ─── Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚡ CloudPSS 仿真工作台")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 创建任务", use_container_width=True, type="primary"):
            st.session_state.page = "create"
            st.session_state.current_task_id = None
    with col2:
        if st.button("📋 任务列表", use_container_width=True):
            st.session_state.page = "list"
            st.session_state.current_task_id = None

    st.markdown("---")

    # Recent tasks
    st.caption("最近任务")
    recent = task_store.list_tasks(limit=5)
    for t in recent:
        status_icon = {"done": "✅", "failed": "❌", "running": "🔄", "draft": "📝", "confirmed": "⏳"}.get(t.status, "❓")
        if st.button(
            f"{status_icon} {t.name}",
            key=f"recent_{t.id}",
            use_container_width=True,
            type="primary" if st.session_state.current_task_id == t.id else "secondary",
        ):
            st.session_state.current_task_id = t.id
            st.session_state.page = "results"

    st.markdown("---")

    # Settings
    if st.button("⚙️ 设置", use_container_width=True):
        st.session_state.page = "settings"
        st.session_state.current_task_id = None

    st.markdown("---")
    st.caption("技能状态")
    status_text = "✅ 已加载" if st.session_state.skills_loaded else "❌ 加载失败"
    st.caption(status_text)


# ─── Page Routing ─────────────────────────────────────────────────────
if st.session_state.page == "create":
    from web.components.task_create import render
    render()
elif st.session_state.page == "list":
    from web.components.task_list import render
    render()
elif st.session_state.page == "settings":
    from web.components.settings import render
    render()
elif st.session_state.page == "results":
    if st.session_state.current_task_id:
        from web.components.task_results import render
        render(st.session_state.current_task_id)
    else:
        st.info("请先选择一个任务")
