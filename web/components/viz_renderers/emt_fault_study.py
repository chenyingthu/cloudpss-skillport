"""EMT Fault Study result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer


@register_renderer("emt_fault_study")
def render(data: dict, task, context=None):
    """Render EMT fault study comparison results."""
    # Model info
    if data.get("model_name"):
        st.caption(f"模型: {data['model_name']} ({data.get('model_rid', '')})")

    # Scenario table
    scenarios = data.get("scenarios", [])
    if scenarios:
        st.subheader("📊 工况对比汇总")
        import pandas as pd

        labels = {
            "baseline": "基线故障",
            "delayed_clearing": "延迟切除",
            "mild_fault": "轻故障",
        }
        rows = []
        for s in scenarios:
            rows.append({
                "工况": labels.get(s.get("scenario", ""), s.get("scenario", "")),
                "描述": s.get("description", ""),
                "故障结束时间 (s)": s.get("fault_end_time", ""),
                "故障电阻 (Ω)": s.get("fault_chg", ""),
                "故障前RMS (V)": s.get("prefault_rms", ""),
                "故障RMS (V)": s.get("fault_rms", ""),
                "故障后RMS (V)": s.get("postfault_rms", ""),
                "恢复缺口 (V)": s.get("postfault_gap_vs_prefault", ""),
                "观察": s.get("observation", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Conclusion / findings
    summary = data.get("summary", {})
    findings = summary.get("findings", [])
    if findings:
        st.subheader("🔍 关键发现")
        for finding in findings:
            status = "✅ 支持" if finding.get("supported") else "❌ 未满足"
            with st.expander(f"{finding.get('title', '')} — {status}", expanded=False):
                st.caption(f"证据: {finding.get('evidence', '')}")

    # Error state
    if summary.get("error"):
        st.error(f"❌ {summary['error']}")
