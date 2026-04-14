"""Generic fallback result renderer with smart data detection."""
import streamlit as st

from web.components.viz_skill import register_renderer, detect_result_type


@register_renderer("generic")
def render(data: dict, task, context=None):
    """Smart fallback renderer for skills without dedicated renderers.

    Automatically detects data shapes and renders appropriately:
    - list-of-dict → data table
    - flat dict → key-value metrics
    - nested dict → collapsible sections
    """
    if not data:
        st.caption("无结果数据")
        return

    # If this looks like a known type but has no dedicated renderer,
    # dispatch to the detected type's renderer
    detected = detect_result_type(data)
    if detected:
        from web.components.viz_skill import render_result
        render_result(detected, data, task, context)
        return

    # ─── List of dicts → Table ─────────────────────────────
    lists = [k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)]
    if lists:
        for key in lists:
            st.subheader(f"📋 {key}")
            import pandas as pd
            df = pd.DataFrame(data[key])
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ─── Flat metrics → Metrics ────────────────────────────
    metrics = {k: v for k, v in data.items()
               if not isinstance(v, (dict, list)) and k not in ("model", "model_rid", "job_id", "timestamp")}
    if metrics:
        cols = st.columns(min(len(metrics), 4))
        for i, (k, v) in enumerate(metrics.items()):
            label = _humanize_key(k)
            cols[i % 4].metric(label, v)

    # ─── Model info ────────────────────────────────────────
    if data.get("model"):
        st.caption(f"模型: {data['model']} ({data.get('model_rid', '')})")
    if data.get("converged") is not None:
        st.success("✅ 收敛") if data["converged"] else st.error("❌ 未收敛")
    if data.get("status"):
        st.success(f"✅ 状态: {data['status']}")

    # ─── Nested dicts → Expandable sections ────────────────
    nested = {k: v for k, v in data.items() if isinstance(v, dict)}
    for key, val in nested.items():
        with st.expander(f"📂 {_humanize_key(key)}", expanded=False):
            st.json(val)

    # ─── Fallback: raw JSON for anything not yet covered ───
    if not lists and not metrics and not nested:
        st.json(data)


def _humanize_key(key: str) -> str:
    """Convert snake_case key to human-readable label."""
    return key.replace("_", " ").title()
