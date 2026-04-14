"""
Task Results: Display execution results with tables, charts, and artifacts.

Skill-specific renderers:
- power_flow: convergence status + bus voltage table + branch flow table + system summary
- emt_simulation: simulation status + waveform plot
- Others: generic JSON viewer
"""
import json
from datetime import datetime
from typing import Optional

import streamlit as st

from web.core import task_store, task_executor


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
    """Display results based on skill type."""
    result_data = task.result_data or {}

    # ─── Result Summary ────────────────────────────────────
    st.subheader("📊 仿真结果")

    # Skill-specific rendering
    if task.skill_name == "power_flow":
        _render_power_flow(result_data, task)
    elif task.skill_name == "emt_simulation":
        _render_emt(result_data, task)
    elif task.skill_name == "n1_security":
        _render_n1(result_data)
    else:
        _render_generic(result_data)

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

    # ─── Metrics ──────────────────────────────────────────
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


def _fetch_job_data(job_id: str, config: dict) -> Optional[dict]:
    """Fetch full job result data from CloudPSS API.

    Returns dict with 'buses' and 'branches' lists of dicts,
    or None if fetch fails.
    """
    try:
        from cloudpss import Job
        from cloudpss_skills.core.utils import parse_cloudpss_table

        # Set auth before fetching
        from web.components.settings import load_settings, TOKEN_FILE
        settings = load_settings()
        preset = settings.get("server_preset", "internal")
        if preset == "internal":
            import os
            os.environ["CLOUDPSS_API_URL"] = "http://166.111.60.76:50001"

        job = Job.fetch(job_id)
        result = job.result
        if result is None:
            return None

        buses = []
        branches = []

        if hasattr(result, "getBuses"):
            raw_buses = result.getBuses()
            if raw_buses:
                buses = parse_cloudpss_table(raw_buses)

        if hasattr(result, "getBranches"):
            raw_branches = result.getBranches()
            if raw_branches:
                branches = parse_cloudpss_table(raw_branches)

        # Also parse iteration count from the raw result
        iterations = None
        if hasattr(result, "getIterations"):
            iterations = result.getIterations()

        return {
            "buses": buses,
            "branches": branches,
            "iterations": iterations,
        }
    except Exception as e:
        st.warning(f"⚠️ 从 API 获取详细结果失败: {e}")
        return None


def _render_power_flow(data: dict, task):
    """Render power flow results with full data from API."""
    # Basic status
    if data.get("converged") is not None:
        st.success("✅ 潮流收敛") if data["converged"] else st.error("❌ 潮流未收敛")

    # Model info
    if data.get("model"):
        st.caption(f"模型: {data['model']} ({data.get('model_rid', '')})")

    # ─── System Summary ───────────────────────────────────
    job_id = data.get("job_id") or task.config.get("auth", {}).get("job_id")
    # job_id is stored at task.result_data level
    if not job_id and "job_id" in data:
        job_id = data["job_id"]

    enriched = None
    if job_id:
        with st.spinner("正在获取详细结果..."):
            enriched = _fetch_job_data(job_id, task.config)

    buses = enriched["buses"] if enriched else []
    branches = enriched["branches"] if enriched else []

    if buses:
        # System totals
        total_gen_p = sum(float(b.get("Pgen", 0) or 0) for b in buses)
        total_gen_q = sum(float(b.get("Qgen", 0) or 0) for b in buses)
        total_load_p = sum(float(b.get("Pload", 0) or 0) for b in buses)
        total_load_q = sum(float(b.get("Qload", 0) or 0) for b in buses)
        loss_p = total_gen_p - total_load_p
        loss_q = total_gen_q - total_load_q

        # Find max/min voltage buses
        vm_values = [(b.get("Bus", f"#{i}"), float(b.get("Vm", 0))) for i, b in enumerate(buses)]
        max_bus, max_vm = max(vm_values, key=lambda x: x[1])
        min_bus, min_vm = min(vm_values, key=lambda x: x[1])

        st.subheader("📊 系统概览")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("母线数", data.get("bus_count", len(buses)))
        m2.metric("支路数", data.get("branch_count", len(branches)))
        m3.metric("总发电 (MW)", f"{total_gen_p:.1f}")
        m4.metric("总负荷 (MW)", f"{total_load_p:.1f}")
        m5.metric("网损 (MW)", f"{loss_p:.2f}")
        m6.metric("网损 (%)", f"{(loss_p / total_gen_p * 100) if total_gen_p else 0:.2f}")

        v1, v2, v3 = st.columns(3)
        v1.metric("最高电压", f"{max_vm:.4f} p.u.", delta=f"({max_bus})")
        v2.metric("最低电压", f"{min_vm:.4f} p.u.", delta=f"({min_bus})")
        v3.metric("电压偏差", f"{max_vm - min_vm:.4f} p.u.")

        # Iteration count
        iterations = enriched.get("iterations") if enriched else None
        if iterations is not None:
            st.caption(f"迭代次数: {iterations}")

    # ─── Bus Voltage Table ─────────────────────────────────
    if buses:
        st.subheader("⚡ 母线电压")
        import pandas as pd
        bus_cols = ["Bus", "Vm", "Va", "Pgen", "Qgen", "Pload", "Qload"]
        bus_labels = {"Bus": "母线", "Vm": "电压 (p.u.)", "Va": "相角 (°)",
                      "Pgen": "发电P (MW)", "Qgen": "发电Q (MVar)",
                      "Pload": "负荷P (MW)", "Qload": "负荷Q (MVar)"}
        bus_df = pd.DataFrame([{bus_labels.get(c, c): b.get(c, "-") for c in bus_cols if c in b} for b in buses])
        # Round numeric columns
        for c in ["电压 (p.u.)", "相角 (°)", "发电P (MW)", "发电Q (MVar)", "负荷P (MW)", "负荷Q (MVar)"]:
            if c in bus_df.columns:
                bus_df[c] = pd.to_numeric(bus_df[c], errors="coerce").round(4)
        st.dataframe(bus_df, use_container_width=True, hide_index=True)

        # Voltage bar chart
        st.subheader("📊 母线电压分布")
        vm_data = pd.DataFrame(buses)
        vm_data["Vm"] = pd.to_numeric(vm_data["Vm"], errors="coerce")
        vm_data = vm_data.dropna(subset=["Vm"]).sort_values("Bus")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 4))
        bars = ax.bar(range(len(vm_data)), vm_data["Vm"], color=["#2ecc71" if 0.95 <= v <= 1.05 else "#e74c3c" for v in vm_data["Vm"]], width=0.8)
        ax.axhline(y=1.0, color="#3498db", linestyle="--", alpha=0.5, label="1.0 p.u.")
        ax.axhline(y=1.05, color="#f39c12", linestyle=":", alpha=0.5)
        ax.axhline(y=0.95, color="#f39c12", linestyle=":", alpha=0.5)
        ax.set_xlabel("母线编号")
        ax.set_ylabel("电压 (p.u.)")
        ax.set_title("母线电压分布 (绿: 0.95-1.05, 红: 越限)")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)

    # ─── Branch Flow Table ─────────────────────────────────
    if branches:
        st.subheader("🔌 支路潮流")
        import pandas as pd
        br_cols = ["Branch", "From bus", "To bus", "Pij", "Pji", "Qij", "Qji"]
        br_labels = {"Branch": "支路", "From bus": "首端母线", "To bus": "末端母线",
                     "Pij": "P首→末 (MW)", "Pji": "P末→首 (MW)",
                     "Qij": "Q首→末 (MVar)", "Qji": "Q末→首 (MVar)"}
        br_df = pd.DataFrame([{br_labels.get(c, c): br.get(c, "-") for c in br_cols if c in br} for br in branches])
        for c in ["P首→末 (MW)", "P末→首 (MW)", "Q首→末 (MVar)", "Q末→首 (MVar)"]:
            if c in br_df.columns:
                br_df[c] = pd.to_numeric(br_df[c], errors="coerce").round(4)
        st.dataframe(br_df, use_container_width=True, hide_index=True)

    elif not enriched and not data.get("bus_results"):
        st.caption("详细数据不可用（无 job_id 或 API 请求失败）。查看使用的配置了解参数详情。")


def _render_emt(data: dict, task):
    """Render EMT simulation results."""
    if data.get("status") == "DONE":
        st.success("✅ 仿真完成")
    elif data.get("status") == "FAILED":
        st.error("❌ 仿真失败")

    if data.get("duration"):
        st.caption(f"仿真时长: {data['duration']:.2f}s")

    if task.artifacts:
        st.caption(f"输出文件数: {len(task.artifacts)}")
        for artifact in task.artifacts:
            st.caption(f"  - {artifact.get('path', '')}")


def _render_n1(data: dict):
    """Render N-1 security check results."""
    if data.get("total_branches") is not None:
        st.metric("总检查支路数", data["total_branches"])

    if data.get("safe_count") is not None:
        st.metric("安全支路", data["safe_count"])

    if data.get("violation_count") is not None and data["violation_count"] > 0:
        st.warning(f"⚠️ {data['violation_count']} 条支路存在越限")
        if data.get("violations"):
            st.dataframe(data["violations"], use_container_width=True)
    elif data.get("safe_count") is not None:
        st.success("✅ 所有支路安全")


def _render_generic(data: dict):
    """Fallback: show raw JSON."""
    st.subheader("原始结果数据")
    st.json(data)


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
