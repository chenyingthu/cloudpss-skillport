"""
Task List: Browse and manage all historical tasks.

Features:
- Table view with name, skill, status, time
- Filter by skill / status
- Click to view results
- Copy / delete tasks
"""
import streamlit as st

from web.core import task_store


def render():
    st.title("📋 任务列表")

    # ─── Filters ───────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input("搜索", placeholder="输入任务名称或技能名...")

    with col2:
        status_filter = st.selectbox(
            "状态",
            options=["全部", "done", "failed", "running", "draft", "confirmed"],
        )

    with col3:
        # Get unique skill names for filter
        tasks = task_store.list_tasks(limit=500)
        skill_names = sorted(set(t.skill_name for t in tasks))
        skill_filter = st.selectbox(
            "技能",
            options=["全部"] + skill_names,
        )

    # ─── Filter Tasks ─────────────────────────────────────
    filtered = tasks
    if status_filter != "全部":
        filtered = [t for t in filtered if t.status == status_filter]
    if skill_filter != "全部":
        filtered = [t for t in filtered if t.skill_name == skill_filter]
    if search:
        search_lower = search.lower()
        filtered = [
            t for t in filtered
            if search_lower in t.name.lower() or search_lower in t.skill_name.lower()
        ]

    st.caption(f"共 {len(filtered)} 个任务")

    if not filtered:
        st.info("没有匹配的任务记录。点击侧边栏「创建任务」开始新的仿真。")
        return

    # ─── Task Table ───────────────────────────────────────
    for task in filtered:
        status_icon = {
            "done": "✅", "failed": "❌", "running": "🔄",
            "draft": "📝", "confirmed": "⏳"
        }.get(task.status, "❓")

        with st.container(border=True):
            col_name, col_skill, col_status, col_time, col_actions = st.columns([3, 2, 1, 2, 2])

            col_name.markdown(f"**{task.name}**")
            col_skill.caption(task.skill_name)
            col_status.markdown(f"{status_icon} {task.status}")
            col_time.caption(task.created_at[:16])

            action_col1, action_col2, action_col3 = col_actions.columns(3)
            if action_col1.button("查看", key=f"view_{task.id}"):
                st.session_state.current_task_id = task.id
                st.session_state.page = "results"
                st.rerun()
            if action_col2.button("复制", key=f"copy_{task.id}"):
                _copy_task(task)
            if action_col3.button("删除", key=f"del_{task.id}"):
                task_store.delete_task(task.id)
                st.rerun()


def _copy_task(task):
    """Create a copy of an existing task."""
    new_task = task_store.create_task(
        name=f"{task.name} (副本)",
        skill_name=task.skill_name,
        config=dict(task.config),
        config_source="manual",
        nl_prompt=task.nl_prompt,
    )
    st.session_state.current_task_id = new_task.id
    st.session_state.draft_config = new_task.config
    st.session_state.draft_skill = new_task.skill_name
    st.session_state.draft_prompt = new_task.nl_prompt
    st.session_state.page = "create"
    st.success(f"已复制任务: {new_task.name}")
    st.rerun()
