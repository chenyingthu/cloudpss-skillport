"""Power flow result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer


def _fetch_job_data(job_id: str, config: dict):
    """Fetch full bus/branch data from CloudPSS API via WebSocket replay.

    Key insight: Job result data is streamed via WebSocket. After job
    completion, the receiver's message buffer is empty. Calling
    result._receiver.waitFor() reconnects the WebSocket and the server
    replays all historical messages, including buses-table and
    branches-table data.

    Returns dict with 'buses' and 'branches' lists, or None on failure.
    """
    try:
        from cloudpss import Job
        from cloudpss_skills.core.auth_utils import setup_auth
        from cloudpss_skills.core.utils import parse_cloudpss_table

        # Authenticate (required for Job.fetch to work).
        if config.get("auth"):
            setup_auth(config)

        job = Job.fetch(job_id)
        result = job.result
        if result is None:
            return None

        # Reconnect WebSocket and replay all historical messages.
        # Without this, _receiver.messages is empty and getBuses/getBranches
        # return []. The server replays the full message stream including
        # buses-table and branches-table.
        try:
            result._receiver.waitFor(timeOut=10000)
        except Exception:
            pass  # Some servers don't support replay — buses will be empty

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


@register_renderer("power_flow")
def render(data: dict, task, context=None):
    """Render power flow results with full data from API."""
    # Basic status
    if data.get("converged") is not None:
        st.success("✅ 潮流收敛") if data["converged"] else st.error("❌ 潮流未收敛")

    # Model info
    if data.get("model"):
        st.caption(f"模型: {data['model']} ({data.get('model_rid', '')})")

    # ─── System Summary ───────────────────────────────────
    # Use skill-provided data directly (preferred for new tasks)
    buses = data.get("buses", [])
    branches = data.get("branches", [])

    # Fallback: fetch detailed data via WebSocket replay only if skill didn't provide data
    enriched = None
    if not buses and not branches and data.get("job_id"):
        # Only fetch from API for historical tasks that don't have complete data
        with st.spinner("正在获取详细结果..."):
            enriched = _fetch_job_data(data["job_id"], task.config)
            if enriched:
                buses = enriched["buses"]
                branches = enriched["branches"]

    if buses:
        # Use skill-provided summary if available (preferred), otherwise compute from buses
        summary = data.get("summary")
        if summary:
            # Skill provides pre-computed summary
            total_gen_p = summary.get("total_generation", {}).get("p_mw", 0)
            total_gen_q = summary.get("total_generation", {}).get("q_mvar", 0)
            total_load_p = summary.get("total_load", {}).get("p_mw", 0)
            total_load_q = summary.get("total_load", {}).get("q_mvar", 0)
            loss_p = summary.get("total_loss_mw", 0)
            voltage_range = summary.get("voltage_range", {})
            min_vm = voltage_range.get("min_pu", 0)
            max_vm = voltage_range.get("max_pu", 0)
            # Find max/min voltage buses for display (use skill summary for values)
            vm_values = [(b.get("Bus", f"#{i}"), float(b.get("Vm", 0))) for i, b in enumerate(buses)]
            max_bus, _ = max(vm_values, key=lambda x: x[1])
            min_bus, _ = min(vm_values, key=lambda x: x[1])
        else:
            # Compute from buses (fallback for old tasks)
            total_gen_p = sum(float(b.get("Pgen", 0) or 0) for b in buses)
            total_gen_q = sum(float(b.get("Qgen", 0) or 0) for b in buses)
            total_load_p = sum(float(b.get("Pload", 0) or 0) for b in buses)
            total_load_q = sum(float(b.get("Qload", 0) or 0) for b in buses)
            loss_p = total_gen_p - total_load_p
            loss_q = total_gen_q - total_load_q
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
        iterations = data.get("iterations") or (enriched.get("iterations") if enriched else None)
        if iterations is not None:
            st.caption(f"迭代次数: {iterations}")

        # ─── Bus Voltage Table ─────────────────────────────────
        st.subheader("⚡ 母线电压")
        import pandas as pd
        bus_cols = ["Bus", "Vm", "Va", "Pgen", "Qgen", "Pload", "Qload"]
        bus_labels = {"Bus": "母线", "Vm": "电压 (p.u.)", "Va": "相角 (°)",
                      "Pgen": "发电P (MW)", "Qgen": "发电Q (MVar)",
                      "Pload": "负荷P (MW)", "Qload": "负荷Q (MVar)"}
        bus_df = pd.DataFrame([{bus_labels.get(c, c): b.get(c, "-") for c in bus_cols if c in b} for b in buses])
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
        ax.bar(range(len(vm_data)), vm_data["Vm"],
               color=["#2ecc71" if 0.95 <= v <= 1.05 else "#e74c3c" for v in vm_data["Vm"]],
               width=0.8)
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

    else:
        # No detailed bus/branch data — show summary metrics
        st.subheader("📋 结果摘要")
        cols = st.columns(4)
        cols[0].metric("母线数", data.get("bus_count", "-"))
        cols[1].metric("支路数", data.get("branch_count", "-"))
        cols[2].metric("任务ID", data.get("job_id", "-")[:8] + "..." if data.get("job_id") else "-")
        cols[3].metric("时间", data.get("timestamp", "-")[:16] if data.get("timestamp") else "-")

        st.info(
            "💡 此为历史任务，详细结果数据未保存。\n"
            "新执行的潮流计算任务将保存完整的母线/支路表格数据。"
        )
