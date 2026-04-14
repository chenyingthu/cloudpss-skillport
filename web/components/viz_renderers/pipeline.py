"""Pipeline result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer, render_step


@register_renderer("study_pipeline")
def render(data: dict, task, context=None):
    """Render study_pipeline execution results with per-step rendering."""
    steps = data.get("steps", [])
    if not steps:
        st.caption("流水线无步骤")
        return

    # ─── Overall Summary ──────────────────────────────────
    total = len(steps)
    success = sum(1 for s in steps if s.get("status") == "success")
    failed = sum(1 for s in steps if s.get("status") == "failed")
    total_duration = sum(s.get("duration", 0) for s in steps)

    if failed == 0:
        st.success(f"✅ 流水线执行完成 ({total}/{total} 步骤成功)")
    elif success == 0:
        st.error(f"❌ 所有步骤失败 ({total}/{total} 失败)")
    else:
        st.warning(f"⚠️ 部分步骤失败 ({success} 成功, {failed} 失败)")

    st.caption(f"总耗时: {total_duration:.1f}s")

    # ─── Per-Step Rendering ───────────────────────────────
    st.subheader("📋 步骤详情")
    for i, step in enumerate(steps):
        status = step.get("status", "")
        skill = step.get("skill", "")
        name = step.get("name", skill)
        depends = step.get("depends_on", [])
        when = step.get("when", "")
        parallel = step.get("parallel", False)
        duration = step.get("duration", 0)

        # Status icon
        if status == "success":
            icon = "✅"
        elif status == "failed":
            icon = "❌"
        elif status == "skipped":
            icon = "⏭️"
        else:
            icon = "❓"

        # Build label
        label = f"{icon} {name} ({skill})"
        extra_parts = []
        if parallel:
            extra_parts.append("并行")
        if depends:
            extra_parts.append(f"依赖: {', '.join(depends)}")
        if when:
            extra_parts.append(f"条件: {when}")
        extra = " | ".join(extra_parts)
        if extra:
            label = f"{label} — {extra}"

        with st.expander(label, expanded=(status == "failed")):
            if status == "success":
                st.caption(f"耗时: {duration:.1f}s")
                # Render step result via dispatcher
                result_data = step.get("result_data", {})
                if result_data:
                    # Build a minimal context for cross-step references
                    ctx = _build_context_for_step(steps, i)
                    render_step(step, ctx)
            elif status == "failed":
                st.error(f"步骤失败: {step.get('error', '未知错误')}")
            elif status == "skipped":
                st.caption("⏭️ 跳过（前置步骤失败或条件不满足）")


def _build_context_for_step(steps, current_idx):
    """Build a context dict with previous step results for variable resolution."""
    ctx = {"steps": {}}
    for i, step in enumerate(steps):
        if i > current_idx:
            break
        name = step.get("name", step.get("skill", ""))
        ctx["steps"][name] = {
            "status": step.get("status", ""),
            "result": step.get("result_data", {}),
            "data": step.get("result_data", {}),
            "artifacts": step.get("artifacts", []),
        }
    return ctx
