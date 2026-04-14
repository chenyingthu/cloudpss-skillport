"""Short Circuit Analysis result renderer."""
import streamlit as st

from web.components.viz_skill import register_renderer


@register_renderer("short_circuit")
def render(data: dict, task, context=None):
    """Render short circuit analysis results."""
    # Model and fault info
    if data.get("model"):
        st.caption(f"模型: {data['model']}")

    st.subheader("⚡ 短路信息")
    cols = st.columns(3)
    cols[0].metric("短路位置", data.get("fault_location", "-"))
    cols[1].metric("短路类型", _fault_type_label(data.get("fault_type", "")))
    cols[2].metric("短路电阻", f"{data.get('fault_resistance', 0)} Ω")

    # Base values
    base_cols = st.columns(2)
    base_cols[0].metric("基准电压", f"{data.get('base_voltage', '-')} kV")
    base_cols[1].metric("基准容量", f"{data.get('base_capacity', '-')} MVA")

    # Short circuit capacity summary
    scc_mva = data.get("short_circuit_mva", {})
    if scc_mva:
        st.subheader("📊 短路容量")
        import pandas as pd
        scc_rows = []
        for ch, info in scc_mva.items():
            scc_rows.append({
                "通道": ch,
                "稳态电流 (kA)": f"{info.get('steady_current_ka', 0):.4f}",
                "短路容量 (MVA)": f"{info.get('short_circuit_mva', 0):.2f}",
            })
        scc_df = pd.DataFrame(scc_rows)
        st.dataframe(scc_df, use_container_width=True, hide_index=True)

        # Max short circuit capacity
        max_scc = max(info.get("short_circuit_mva", 0) for info in scc_mva.values())
        if max_scc > 0:
            st.metric("最大短路容量", f"{max_scc:.2f} MVA")

    # Analysis details (current channels)
    analysis = data.get("analysis", {})
    current_channels = {ch: info for ch, info in analysis.items() if "peak_current" in info}
    if current_channels:
        st.subheader("📈 短路电流分析")
        import pandas as pd
        ch_rows = []
        for ch, info in current_channels.items():
            ch_rows.append({
                "通道": ch,
                "峰值电流 (kA)": f"{info.get('peak_current', 0):.4f}",
                "稳态电流 (kA)": f"{info.get('steady_current', 0):.4f}",
                "直流分量 (kA)": f"{info.get('dc_component', 0):.4f}",
                "时间常数 (ms)": f"{info.get('time_constant', 0):.2f}",
            })
        ch_df = pd.DataFrame(ch_rows)
        st.dataframe(ch_df, use_container_width=True, hide_index=True)

    # Voltage channels
    voltage_channels = {ch: info for ch, info in analysis.items() if "min_voltage" in info}
    if voltage_channels:
        st.subheader("⚡ 母线电压跌落")
        import pandas as pd
        v_rows = []
        for ch, info in voltage_channels.items():
            v_rows.append({
                "通道": ch,
                "最低电压 (pu)": f"{info.get('min_voltage', 0):.4f}",
            })
        v_df = pd.DataFrame(v_rows)
        st.dataframe(v_df, use_container_width=True, hide_index=True)


def _fault_type_label(fault_type: str) -> str:
    """Translate fault type to Chinese label."""
    labels = {
        "three_phase": "三相短路",
        "line_to_ground": "单相接地",
        "line_to_line": "两相短路",
    }
    return labels.get(fault_type, fault_type)
