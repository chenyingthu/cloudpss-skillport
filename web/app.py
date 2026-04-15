"""
CloudPSS Task-Oriented Web Portal

A task-oriented web interface for CloudPSS power system simulation.
Sidebar: favorites toolbar + skill tree (categories as expanders).
Click a skill → right panel enters that skill's task creation form.
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

from web.core import task_store, skill_catalog, favorites


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

if "selected_skill" not in st.session_state:
    st.session_state.selected_skill = None

# ─── Load Saved Settings ─────────────────────────────────────────────
try:
    from web.components.settings import load_settings, apply_settings
    saved_settings = load_settings()
    if saved_settings:
        apply_settings(saved_settings)
except Exception:
    pass

# ─── Skill name short labels for favorites toolbar ─────────────────────
SKILL_SHORT = {
    "power_flow": "潮流",
    "emt_simulation": "EMT",
    "emt_fault_study": "故障",
    "short_circuit": "短路",
    "n1_security": "N-1",
    "n2_security": "N-2",
    "emt_n1_screening": "EMT-N1",
    "contingency_analysis": "预想事故",
    "maintenance_security": "检修",
    "batch_powerflow": "批量潮流",
    "param_scan": "参数扫描",
    "fault_clearing_scan": "故障清除",
    "fault_severity_scan": "严重度",
    "batch_task_manager": "批量管理",
    "config_batch_runner": "配置批量",
    "orthogonal_sensitivity": "正交敏感",
    "voltage_stability": "电压稳定",
    "transient_stability": "暂态稳定",
    "transient_stability_margin": "稳定裕度",
    "small_signal_stability": "小信号",
    "frequency_response": "频率响应",
    "vsi_weak_bus": "VSI弱母线",
    "dudv_curve": "DUDV",
    "result_compare": "结果对比",
    "visualize": "可视化",
    "waveform_export": "波形导出",
    "hdf5_export": "HDF5导出",
    "disturbance_severity": "扰动严重度",
    "compare_visualization": "对比可视化",
    "comtrade_export": "COMTRADE",
    "harmonic_analysis": "谐波",
    "power_quality_analysis": "电能质量",
    "reactive_compensation_design": "无功补偿",
    "renewable_integration": "新能源",
    "topology_check": "拓扑检查",
    "parameter_sensitivity": "灵敏度",
    "auto_channel_setup": "自动通道",
    "auto_loop_breaker": "自动解环",
    "model_parameter_extractor": "参数提取",
    "model_builder": "模型构建",
    "model_validator": "模型验证",
    "component_catalog": "元件目录",
    "thevenin_equivalent": "戴维南等值",
    "model_hub": "算例中心",
    "loss_analysis": "网损分析",
    "protection_coordination": "保护整定",
    "report_generator": "报告生成",
    "study_pipeline": "流水线",
}


def _select_skill(name: str):
    """Navigate to task creation with the given skill pre-selected."""
    st.session_state.selected_skill = name
    st.session_state.page = "create"


# ─── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚡ CloudPSS 仿真工作台")
    st.markdown("---")

    # Nav buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 创建任务", use_container_width=True, type="primary" if st.session_state.page == "create" else "secondary"):
            st.session_state.page = "create"
            st.session_state.selected_skill = None
            st.session_state.current_task_id = None
    with col2:
        if st.button("📋 任务列表", use_container_width=True, type="primary" if st.session_state.page == "list" else "secondary"):
            st.session_state.page = "list"
            st.session_state.selected_skill = None
            st.session_state.current_task_id = None

    st.markdown("---")

    # ─── Favorites Toolbar ──────────────────────────────────────
    fav_skills = favorites.load_favorites()
    if fav_skills:
        st.caption("⭐ 收藏的技能")
        cols = st.columns(min(len(fav_skills), 4))
        for i, sname in enumerate(fav_skills):
            label = SKILL_SHORT.get(sname, sname[:4])
            btn_type = "primary" if st.session_state.selected_skill == sname else "secondary"
            if cols[i % 4].button(label, key=f"fav_{sname}", use_container_width=True, type=btn_type):
                _select_skill(sname)
        st.markdown("---")

    # ─── Skill Tree ─────────────────────────────────────────────
    categories = skill_catalog.get_categorized_skills()
    if categories:
        st.caption("📂 技能目录")
        for cat_name, skills in categories.items():
            with st.expander(cat_name, expanded=False):
                for s in skills:
                    sname = s["name"]
                    fav_icon = "⭐" if favorites.is_favorite(sname) else ""
                    label = f"{fav_icon} {SKILL_SHORT.get(sname, sname)}" if fav_icon else SKILL_SHORT.get(sname, sname)
                    btn_type = "primary" if st.session_state.selected_skill == sname else "secondary"
                    if st.button(label, key=f"skill_{sname}", use_container_width=True, type=btn_type):
                        _select_skill(sname)

        st.markdown("---")

    # ─── Recent Tasks ───────────────────────────────────────────
    st.caption("📋 最近任务")
    recent = task_store.list_tasks(limit=3)
    if not recent:
        st.caption("暂无任务")
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
            st.session_state.selected_skill = None

    st.markdown("---")

    # Settings + status
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("⚙️ 设置", use_container_width=True):
            st.session_state.page = "settings"
            st.session_state.selected_skill = None
            st.session_state.current_task_id = None
    with col_s2:
        status_text = "✅" if st.session_state.skills_loaded else "❌"
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
