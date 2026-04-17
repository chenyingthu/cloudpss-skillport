"""Pipeline result renderer with DAG, timeline, data flow, and validation."""
import streamlit as st

from web.components.viz_skill import register_renderer, render_step


@register_renderer("study_pipeline")
def render(data: dict, task, context=None):
    """Render study_pipeline execution results with enhanced visualization."""
    steps = data.get("steps", [])
    if not steps:
        st.caption("流水线无步骤")
        return

    # Tab layout for organized display
    tabs = st.tabs(["总体摘要", "执行时间线", "DAG依赖图", "逐步结果", "正确性验证"])

    with tabs[0]:
        _render_summary(steps, data)
    with tabs[1]:
        _render_timeline(steps)
    with tabs[2]:
        _render_dag(steps)
    with tabs[3]:
        _render_steps(steps)
    with tabs[4]:
        _render_validation(steps)


def _render_summary(steps: list, data: dict):
    """Render overall pipeline summary."""
    total = len(steps)
    success = sum(1 for s in steps if s.get("status") == "success")
    failed = sum(1 for s in steps if s.get("status") == "failed")
    skipped = sum(1 for s in steps if s.get("status") == "skipped")
    total_duration = sum(s.get("duration", 0) for s in steps)

    # Overall status
    if failed == 0:
        st.success(f"✅ 流水线执行完成 ({total}/{total} 步骤成功)")
    elif success == 0:
        st.error(f"❌ 所有步骤失败 ({total}/{total} 失败)")
    else:
        st.warning(f"⚠️ 部分步骤失败 ({success} 成功, {failed} 失败, {skipped} 跳过)")

    # Metrics row
    cols = st.columns(6)
    cols[0].metric("总步骤数", total)
    cols[1].metric("成功", success)
    cols[2].metric("失败", failed)
    cols[3].metric("跳过", skipped)
    cols[4].metric("总耗时", f"{total_duration:.1f}s")

    # Parallelism metric
    parallel_steps = sum(1 for s in steps if s.get("parallel", False))
    parallelism = f"{parallel_steps}/{total}" if parallel_steps else "无"
    cols[5].metric("并行步骤", parallelism)

    # Data summary if available
    if data.get("total_steps"):
        st.caption(f"执行统计: {data.get('success_count', 0)} 成功, {data.get('failed_count', 0)} 失败")


def _render_timeline(steps: list):
    """Render execution timeline with parallel group identification."""
    # Identify parallel groups and sequential batches
    # Simple approach: steps with same depends_on are in the same batch
    batches = _identify_batches(steps)

    st.subheader("执行批次")

    for batch_idx, batch in enumerate(batches):
        if len(batch) == 1:
            step = batch[0]
            name = step.get("name", step.get("skill", ""))
            duration = step.get("duration", 0)
            status = step.get("status", "")
            icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
            st.progress(duration / max(s.get("duration", 1) for s in steps) if steps else 0,
                       text=f"{icon} 步骤 {batch_idx + 1}: {name} ({duration:.1f}s)")
        else:
            # Parallel batch
            st.caption(f"🔄 批次 {batch_idx + 1} (并行执行)")
            max_dur = max(s.get("duration", 0) for s in batch)
            cols = st.columns(len(batch))
            for col, step in zip(cols, batch):
                name = step.get("name", step.get("skill", ""))
                duration = step.get("duration", 0)
                status = step.get("status", "")
                icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
                with col:
                    st.metric(f"{icon} {name}", f"{duration:.1f}s")
                    st.progress(duration / max_dur if max_dur else 0)


def _identify_batches(steps: list) -> list[list]:
    """Identify execution batches based on dependency groups."""
    if not steps:
        return []

    # Build dependency graph
    name_to_idx = {}
    for i, s in enumerate(steps):
        name = s.get("name", s.get("skill", ""))
        name_to_idx[name] = i

    # Topological batch: steps with no deps = batch 0, deps resolved = next batch
    batches = []
    resolved = set()
    remaining = list(range(len(steps)))

    while remaining:
        # Find steps whose all dependencies are resolved
        current_batch = []
        still_remaining = []
        for idx in remaining:
            deps = set(steps[idx].get("depends_on", []))
            if deps.issubset(resolved):
                current_batch.append(steps[idx])
            else:
                still_remaining.append(idx)

        if not current_batch:
            # Circular dependency or unresolved - add remaining
            current_batch = [steps[i] for i in remaining]
            still_remaining = []

        batches.append(current_batch)
        for s in current_batch:
            resolved.add(s.get("name", s.get("skill", "")))
        remaining = still_remaining

    return batches


def _render_dag(steps: list):
    """Render DAG visualization using matplotlib/networkx."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
    except ImportError:
        st.caption("DAG可视化需要 matplotlib，当前未安装")
        _render_dag_text(steps)
        return

    try:
        import networkx as nx
    except ImportError:
        st.caption("DAG可视化需要 networkx，当前未安装")
        _render_dag_text(steps)
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    # Build DAG
    G = nx.DiGraph()
    status_colors = {
        "success": "#2ecc71",
        "failed": "#e74c3c",
        "skipped": "#95a5a6",
        "error": "#c0392b",
    }

    name_to_idx = {}
    for i, step in enumerate(steps):
        name = step.get("name", step.get("skill", f"step_{i}"))
        name_to_idx[name] = i
        G.add_node(name,
                   skill=step.get("skill", ""),
                   status=step.get("status", ""),
                   duration=step.get("duration", 0))

    # Add edges
    for step in steps:
        name = step.get("name", step.get("skill", ""))
        for dep in step.get("depends_on", []):
            if dep in G.nodes:
                G.add_edge(dep, name)

    # Layout: topological sort based
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except (ImportError, Exception):
        pos = nx.spectral_layout(G)

    # Node colors
    node_colors = [status_colors.get(G.nodes[n].get("status", ""), "#bdc3c7") for n in G.nodes]

    # Draw
    nx.draw(G, pos, ax=ax, with_labels=True, node_color=node_colors,
            node_size=2000, font_size=8, font_weight="bold",
            arrows=True, arrowsize=15, edge_color="#7f8c8d",
            width=1.5, alpha=0.9)

    # Add skill name below node
    labels = {}
    for n in G.nodes:
        skill = G.nodes[n].get("skill", "")
        dur = G.nodes[n].get("duration", 0)
        labels[n] = f"{n}\n{skill}\n{dur:.1f}s"

    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7)

    ax.set_title("Pipeline DAG 依赖关系图", fontsize=14, fontweight="bold")
    st.pyplot(fig)
    plt.close(fig)

    # Legend
    st.caption("节点颜色: 🟢 成功 | 🔴 失败 | ⚪ 跳过")


def _render_dag_text(steps: list):
    """Fallback text-based DAG visualization."""
    st.caption("步骤依赖关系:")
    for i, step in enumerate(steps):
        name = step.get("name", step.get("skill", f"步骤{i+1}"))
        deps = step.get("depends_on", [])
        parallel = step.get("parallel", False)
        status = step.get("status", "")
        icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
        dep_str = f" ← {', '.join(deps)}" if deps else ""
        parallel_str = " [并行]" if parallel else ""
        st.text(f"  {icon} {name}{parallel_str}{dep_str}")


def _render_steps(steps: list):
    """Render per-step results with skill dispatch."""
    for i, step in enumerate(steps):
        status = step.get("status", "")
        skill = step.get("skill", "")
        name = step.get("name", skill)
        depends = step.get("depends_on", [])
        when = step.get("when", "")
        parallel = step.get("parallel", False)
        duration = step.get("duration", 0)

        icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
        label = f"{icon} {name} ({skill})"
        extra_parts = []
        if parallel:
            extra_parts.append("并行")
        if depends:
            extra_parts.append(f"依赖: {', '.join(depends)}")
        if when:
            extra_parts.append(f"条件: {when}")
        if extra_parts:
            label = f"{label} | {' | '.join(extra_parts)}"

        with st.expander(label, expanded=(status == "failed")):
            st.caption(f"耗时: {duration:.1f}s")
            if status == "success":
                result_data = step.get("result_data", {})
                if result_data:
                    ctx = _build_context_for_step(steps, i)
                    render_step(step, ctx)
            elif status == "failed":
                st.error(f"步骤失败: {step.get('error', '未知错误')}")
            elif status == "skipped":
                st.caption("⏭️ 跳过（前置步骤失败或条件不满足）")


def _render_validation(steps: list):
    """Render result correctness validation for each step."""
    findings = _validate_pipeline(steps)

    if not findings:
        st.success("✅ 所有验证项通过")
        return

    # Summary
    passes = sum(1 for f in findings if f["result"] == "pass")
    warnings = sum(1 for f in findings if f["result"] == "warning")
    fails = sum(1 for f in findings if f["result"] == "fail")

    col1, col2, col3 = st.columns(3)
    col1.metric("通过", passes)
    col2.metric("警告", warnings)
    col3.metric("失败", fails)

    # Detailed findings
    st.markdown("---")
    for finding in findings:
        if finding["result"] == "pass":
            st.success(f"✅ [{finding['step']}] {finding['check']}: {finding['detail']}")
        elif finding["result"] == "warning":
            with st.expander(f"⚠️ [{finding['step']}] {finding['check']}: {finding['detail']}"):
                st.caption(f"物理依据: {finding.get('physical_basis', '')}")
        else:
            st.error(f"❌ [{finding['step']}] {finding['check']}: {finding['detail']}")
            st.caption(f"物理依据: {finding.get('physical_basis', '')}")


def _validate_pipeline(steps: list) -> list[dict]:
    """Validate pipeline results for correctness."""
    findings = []
    for step in steps:
        skill = step.get("skill", "")
        result = step.get("result_data", {})
        name = step.get("name", skill)

        if skill == "power_flow":
            findings.extend(_validate_power_flow(name, result))
        elif skill == "emt_simulation":
            findings.extend(_validate_emt(name, result))
        elif skill == "n1_security":
            findings.extend(_validate_n1(name, result))
        elif skill == "vsi_weak_bus":
            findings.extend(_validate_vsi(name, result))
        elif skill == "short_circuit":
            findings.extend(_validate_short_circuit(name, result))

    return findings


def _validate_power_flow(step_name: str, result: dict) -> list[dict]:
    """Validate power flow results."""
    checks = []

    # Voltage range check
    buses = result.get("buses", [])
    if buses:
        for bus in buses:
            vm = float(bus.get("Vm", 1.0))
            if vm < 0.90 or vm > 1.10:
                checks.append({
                    "step": step_name,
                    "check": "电压越限",
                    "result": "fail",
                    "detail": f"母线 {bus.get('Bus', '?')} 电压 {vm:.4f} p.u. 超出 0.90-1.10 安全范围",
                    "physical_basis": "电力系统安全运行要求母线电压在 0.90-1.10 p.u. 范围内",
                })
            elif vm < 0.95 or vm > 1.05:
                checks.append({
                    "step": step_name,
                    "check": "电压偏离推荐值",
                    "result": "warning",
                    "detail": f"母线 {bus.get('Bus', '?')} 电压 {vm:.4f} p.u. 偏离 0.95-1.05 推荐范围",
                    "physical_basis": "IEEE 标准推荐运行电压在 0.95-1.05 p.u.",
                })

    # Power balance check
    if buses:
        total_gen_p = sum(float(b.get("Pgen", 0) or 0) for b in buses)
        total_load_p = sum(float(b.get("Pload", 0) or 0) for b in buses)
        loss_p = total_gen_p - total_load_p
        loss_pct = (loss_p / total_gen_p * 100) if total_gen_p else 0
        if loss_pct > 15:
            checks.append({
                "step": step_name,
                "check": "网损过高",
                "result": "warning",
                "detail": f"网损 {loss_pct:.1f}% 偏高，通常 < 5%",
                "physical_basis": "正常电力系统网损一般 < 5%，> 15% 可能存在模型错误",
            })

    # Convergence check
    if not result.get("converged", True):
        checks.append({
            "step": step_name,
            "check": "收敛性",
            "result": "fail",
            "detail": "潮流计算未收敛",
            "physical_basis": "潮流计算必须收敛，否则结果无物理意义",
        })

    if not checks:
        checks.append({
            "step": step_name,
            "check": "潮流结果验证",
            "result": "pass",
            "detail": "潮流计算收敛，电压在正常范围内",
            "physical_basis": "",
        })

    return checks


def _validate_emt(step_name: str, result: dict) -> list[dict]:
    """Validate EMT simulation results."""
    checks = []

    converged = result.get("converged", True)
    if not converged:
        checks.append({
            "step": step_name,
            "check": "EMT收敛性",
            "result": "fail",
            "detail": "EMT仿真未收敛",
            "physical_basis": "EMT暂态仿真必须数值稳定收敛",
        })

    if not checks:
        checks.append({
            "step": step_name,
            "check": "EMT结果验证",
            "result": "pass",
            "detail": "EMT仿真收敛",
            "physical_basis": "",
        })

    return checks


def _validate_n1(step_name: str, result: dict) -> list[dict]:
    """Validate N-1 security analysis results."""
    checks = []

    violations = result.get("violations", [])
    if violations:
        checks.append({
            "step": step_name,
            "check": "N-1越限统计",
            "result": "warning",
            "detail": f"发现 {len(violations)} 个N-1越限场景",
            "physical_basis": "N-1准则要求任意单一元件退出后系统仍安全运行",
        })

    if not checks:
        checks.append({
            "step": step_name,
            "check": "N-1安全验证",
            "result": "pass",
            "detail": "所有N-1场景通过",
            "physical_basis": "",
        })

    return checks


def _validate_vsi(step_name: str, result: dict) -> list[dict]:
    """Validate VSI weak bus analysis results."""
    checks = []

    vsi_results = result.get("vsi_results", [])
    for vsi in vsi_results:
        vsi_val = float(vsi.get("vsi", 0))
        if vsi_val < 0 or vsi_val > 1:
            checks.append({
                "step": step_name,
                "check": "VSI值范围",
                "result": "fail",
                "detail": f"母线 {vsi.get('bus', '?')} VSI={vsi_val:.4f} 超出 [0,1] 范围",
                "physical_basis": "VSI电压稳定指数应在 [0, 1] 范围内",
            })

    weak_buses = result.get("weak_buses", [])
    if weak_buses:
        checks.append({
            "step": step_name,
            "check": "弱母线检测",
            "result": "warning",
            "detail": f"检测到 {len(weak_buses)} 个弱母线",
            "physical_basis": "弱母线VSI接近1，电压稳定裕度不足",
        })

    if not checks:
        checks.append({
            "step": step_name,
            "check": "VSI结果验证",
            "result": "pass",
            "detail": "VSI值在合理范围内",
            "physical_basis": "",
        })

    return checks


def _validate_short_circuit(step_name: str, result: dict) -> list[dict]:
    """Validate short circuit analysis results."""
    checks = []

    fault_info = result.get("fault_location", {})
    if fault_info:
        current = float(fault_info.get("fault_current", 0))
        if current > 100:
            checks.append({
                "step": step_name,
                "check": "短路电流限值",
                "result": "warning",
                "detail": f"短路电流 {current:.1f} kA 超过常规限值",
                "physical_basis": "常规断路器短路开断能力通常 < 63 kA",
            })

    if not checks:
        checks.append({
            "step": step_name,
            "check": "短路结果验证",
            "result": "pass",
            "detail": "短路电流在合理范围内",
            "physical_basis": "",
        })

    return checks


def _build_context_for_step(steps, current_idx):
    """Build a context dict with previous step results for variable resolution."""
    ctx = {"steps": {}}
    for i, step in enumerate(steps):
        if i >= current_idx:
            break
        name = step.get("name", step.get("skill", ""))
        ctx["steps"][name] = {
            "status": step.get("status", ""),
            "result": step.get("result_data", {}),
            "data": step.get("result_data", {}),
            "artifacts": step.get("artifacts", []),
        }
    return ctx
