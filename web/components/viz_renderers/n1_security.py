"""N-1 security check result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer


@register_renderer("n1_security")
def render(data: dict, task, context=None):
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
