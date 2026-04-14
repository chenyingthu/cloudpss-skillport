"""EMT simulation result renderer."""
import json

import streamlit as st
import matplotlib.pyplot as plt

from web.components.viz_skill import register_renderer


@register_renderer("emt_simulation")
def render(data: dict, task, context=None):
    """Render EMT simulation results with waveform charts."""
    if data.get("status") == "DONE":
        st.success("✅ 仿真完成")
    elif data.get("status") == "FAILED":
        st.error("❌ 仿真失败")
    else:
        st.success("✅ 仿真完成")

    if data.get("duration"):
        st.caption(f"仿真时长: {data['duration']:.2f}s")
    if data.get("step_size"):
        st.caption(f"仿真步长: {data['step_size']}s")

    if not task.artifacts:
        st.caption("无输出文件")
        return

    st.subheader("📈 波形数据")

    for artifact in task.artifacts:
        fpath = artifact.get("path", "")
        if not fpath or not fpath.endswith(".json"):
            continue

        try:
            with open(fpath, "r") as f:
                plot_data = json.load(f)

            plot_idx = plot_data.get("plot_index", "?")
            channels = plot_data.get("channels", {})
            if not channels:
                continue

            st.caption(f"图表 {plot_idx}: {artifact.get('description', '')}")

            fig, ax = plt.subplots(figsize=(12, 3))
            for ch_name, ch_data in channels.items():
                if isinstance(ch_data, dict) and "x" in ch_data and "y" in ch_data:
                    x = ch_data["x"]
                    y = ch_data["y"]
                    if len(x) > 2000:
                        step = len(x) // 2000
                        x = x[::step]
                        y = y[::step]
                    ax.plot(x, y, label=ch_name, linewidth=0.8)

            ax.set_xlabel("时间 (s)")
            ax.set_ylabel("幅值")
            ax.legend(loc="upper right", fontsize="small", ncol=min(len(channels), 4))
            ax.grid(True, alpha=0.3)
            ax.set_title(f"波形数据 (图表 {plot_idx})")
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            st.caption(f"加载 {fpath} 失败: {e}")
