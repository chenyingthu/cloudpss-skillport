"""VSI Weak Bus Analysis result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer


@register_renderer("vsi_weak_bus")
def render(data: dict, task, context=None):
    """Render VSI weak bus analysis results."""
    # Model info
    if data.get("model_rid"):
        st.caption(f"模型: {data['model_rid']}")

    # Summary metrics
    summary = data.get("summary", {})
    if summary:
        st.subheader("📊 分析概览")
        cols = st.columns(4)
        cols[0].metric("测试母线数", summary.get("total_buses", data.get("test_bus_count", "-")))
        cols[1].metric("弱母线数", summary.get("weak_bus_count", "-"))
        cols[2].metric("VSI最大值", f"{summary.get('max_vsi', 0):.6f}")
        cols[3].metric("VSI平均值", f"{summary.get('avg_vsi', 0):.6f}")

    # Weak buses
    weak_buses = data.get("weak_buses", [])
    if weak_buses:
        st.warning(f"⚠️ 发现 {len(weak_buses)} 条弱母线（VSI ≥ 0.01）")
        st.subheader("🔴 弱母线列表")
        import pandas as pd
        weak_df = pd.DataFrame([
            {"排名": i + 1, "母线": wb.get("label", ""), "VSI": f"{wb.get('vsi', 0):.6f}"}
            for i, wb in enumerate(weak_buses)
        ])
        st.dataframe(weak_df, use_container_width=True, hide_index=True)
    elif summary.get("weak_bus_count", 0) == 0:
        st.success("✅ 未发现弱母线")

    # All bus VSI bar chart
    vsi_results = data.get("vsi_results", {})
    vsi_i = vsi_results.get("vsi_i", {})
    if vsi_i:
        st.subheader("📊 VSI指标分布")
        sorted_buses = sorted(vsi_i.items(), key=lambda x: x[1], reverse=True)
        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.DataFrame(sorted_buses, columns=["母线", "VSI"])
        df = df.sort_values("VSI", ascending=True)

        fig, ax = plt.subplots(figsize=(10, max(4, len(df) * 0.3)))
        colors = ["#e74c3c" if v >= 0.01 else "#3498db" for v in df["VSI"]]
        ax.barh(range(len(df)), df["VSI"], color=colors, height=0.8)
        ax.axvline(x=0.01, color="#f39c12", linestyle="--", alpha=0.7, label="阈值 0.01")
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df["母线"])
        ax.set_xlabel("VSI (Voltage Stability Index)")
        ax.set_title("各母线VSI指标 (红: 弱母线 ≥ 0.01)")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)

    # Unsupported buses
    unsupported = data.get("unsupported_buses", [])
    if unsupported:
        with st.expander(f"⚠️ {len(unsupported)} 条母线无法分析", expanded=False):
            st.text(", ".join(str(b) for b in unsupported))
