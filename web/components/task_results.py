"""
Task Results: Display execution results with skill-specific rendering.

All result rendering is delegated to viz_skill's registry-based dispatcher.
Skill-specific renderers live in web/components/viz_renderers/.
"""
from datetime import datetime
from typing import Optional

import streamlit as st

from web.core import task_store, task_executor
from web.components.viz_skill import render_result, is_pipeline_result, render_pipeline


def render(task_id: str):
    task = task_store.get_task(task_id)
    if task is None:
        st.error(f"任务 {task_id} 不存在")
        if st.button("← 返回任务列表"):
            st.session_state.page = "list"
        return

    st.session_state.current_task_id = task_id

    # ─── Task Header ────────────────────────────────────────
    st.title(f"📋 {task.name}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("技能", task.skill_name)
    col2.metric("状态", _status_icon(task.status))
    if task.started_at and task.completed_at:
        try:
            duration = (
                datetime.fromisoformat(task.completed_at)
                - datetime.fromisoformat(task.started_at)
            ).total_seconds()
            col3.metric("耗时", f"{duration:.1f}s")
        except Exception:
            col3.metric("耗时", "-")
    col4.metric("创建时间", task.created_at[:16])

    # ─── Running State: Show Progress ───────────────────────
    if task.status == "running":
        st.warning("⏳ 任务执行中...")
        st.progress(0.5, text="正在等待仿真结果...")
        st.caption("页面将自动刷新。完成后会跳转结果页。")
        _auto_refresh(task_id)
        return

    # ─── Failed State ───────────────────────────────────────
    if task.status == "failed":
        st.error(f"❌ 执行失败: {task.error}")
        col1, col2 = st.columns(2)
        if col1.button("🔄 重新编辑"):
            st.session_state.draft_config = task.config
            st.session_state.draft_skill = task.skill_name
            st.session_state.draft_prompt = task.nl_prompt
            st.session_state.page = "create"
            st.rerun()
        if col2.button("🔁 重新执行"):
            task.status = "confirmed"
            task.error = None
            task_store.save_task(task)
            task_executor.run_async(task.id)
            st.rerun()
        return

    # ─── Done State: Show Results ──────────────────────────
    if task.status == "done":
        _show_results(task)


def _show_results(task):
    """Display results, delegated to viz_skill dispatcher."""
    result_data = task.result_data or {}

    st.subheader("📊 仿真结果")

    # Dispatch to viz_skill renderers
    if is_pipeline_result(result_data):
        render_pipeline(task)
    else:
        render_result(task.skill_name, result_data, task)

    # ─── Artifacts ─────────────────────────────────────────
    if task.artifacts:
        st.subheader("📁 输出文件")
        _check_format_mismatch(task)
        for artifact in task.artifacts:
            col1, col2 = st.columns([3, 1])
            col1.text(f"{artifact.get('type', '')}: {artifact.get('path', '')}")
            if artifact.get("description"):
                col2.caption(artifact["description"])
    else:
        st.caption("无输出文件")

    # ─── Metrics ─────────────────────────────────────────
    if task.metrics:
        st.subheader("📈 执行指标")
        cols = st.columns(min(len(task.metrics), 4))
        for i, (k, v) in enumerate(task.metrics.items()):
            cols[i % 4].metric(k, v)

    # ─── Config Used ───────────────────────────────────────
    with st.expander("⚙️ 使用的配置", expanded=False):
        import yaml
        from scripts.smart_config import ConfigDumper
        yaml_str = yaml.dump(task.config, Dumper=ConfigDumper, allow_unicode=True, sort_keys=False, default_flow_style=False)
        st.code(yaml_str, language="yaml")

    # ─── Actions ───────────────────────────────────────────
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    if col1.button("🔄 重新执行"):
        task.status = "confirmed"
        task.error = None
        task_store.save_task(task)
        task_executor.run_async(task.id)
        st.rerun()
    if col2.button("📋 复制为新任务"):
        new_task = task_store.create_task(
            name=f"{task.name} (副本)",
            skill_name=task.skill_name,
            config=task.config.copy(),
            config_source=task.config_source,
            nl_prompt=task.nl_prompt,
        )
        st.session_state.current_task_id = new_task.id
        st.session_state.page = "create"
        st.session_state.draft_config = new_task.config
        st.session_state.draft_skill = new_task.skill_name
        st.session_state.draft_prompt = new_task.nl_prompt
        st.rerun()
    if col3.button("🗑️ 删除任务"):
        task_store.delete_task(task.id)
        st.session_state.current_task_id = None
        st.session_state.page = "list"
        st.rerun()


def _check_format_mismatch(task):
    """Warn when configured output format doesn't match actual files."""
    configured_fmt = task.config.get("output", {}).get("format", "")
    if not configured_fmt or configured_fmt == "json":
        return
    actual_exts = set()
    for artifact in task.artifacts:
        path = artifact.get("path", "")
        if "." in path:
            ext = path.rsplit(".", 1)[-1]
            actual_exts.add(ext)
    if actual_exts and configured_fmt not in actual_exts:
        st.warning(
            f"⚠️ 输出格式不匹配：配置为 **{configured_fmt}**，但实际输出为 **{', '.join(sorted(actual_exts))}**\n\n"
            f"技能当前仅支持 JSON 输出，CSV/YAML 格式尚未实现。"
        )


def _auto_refresh(task_id: str):
    """Auto-refresh using st.fragment for progress polling."""
    import time

    for _ in range(60):
        time.sleep(2)
        task = task_store.get_task(task_id)
        if task is None:
            break
        if task.status in ("done", "failed"):
            st.rerun()
            break
    st.rerun()


def _status_icon(status: str) -> str:
    icons = {
        "done": "✅ 完成",
        "failed": "❌ 失败",
        "running": "🔄 运行中",
        "draft": "📝 草稿",
        "confirmed": "⏳ 已确认",
    }
    return icons.get(status, status)
