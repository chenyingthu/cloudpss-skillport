"""
Task Create: Natural language input → config draft → preview/edit → confirm.

Flow:
1. User enters natural language description
2. SmartConfigGenerator generates draft config
3. Config is shown in editable form
4. Real-time validation via skill.validate()
5. User confirms → task saved as "confirmed" → trigger execution
"""
import json
import streamlit as st

from web.core import task_store, skill_catalog, task_executor
from smart_config import SmartConfigGenerator


def render():
    st.title("➕ 创建仿真任务")

    # ─── Step 1: Skill Selection ──────────────────────────────────
    st.subheader("1️⃣ 选择仿真技能")

    categories = skill_catalog.get_categorized_skills()
    if not categories:
        st.error("技能列表加载失败，请检查 cloudpss-toolkit 是否正确安装")
        return

    # Flatten categories for selection
    skill_options = {}
    for cat_name, skills in categories.items():
        for s in skills:
            skill_options[f"{cat_name} - {s['name']}"] = s["name"]

    selected_label = st.selectbox(
        "选择技能",
        options=list(skill_options.keys()),
        format_func=lambda x: x.split(" - ", 1)[1] + f" ({x.split(' - ', 1)[0]})",
    )
    selected_skill_name = skill_options[selected_label]

    # Show skill description
    skill_info = skill_catalog.get_skill_info(selected_skill_name)
    if skill_info.get("description"):
        st.caption(skill_info["description"])

    # Load example button
    if st.button("📋 加载示例", help="加载一个可运行的示例配置"):
        _load_example(selected_skill_name)

    # ─── Step 2: Natural Language Input ───────────────────────────
    st.subheader("2️⃣ 描述仿真需求")

    nl_prompt = st.text_area(
        "用自然语言描述仿真需求",
        placeholder="例如：帮我跑个IEEE39潮流计算，收敛精度1e-8",
        height=80,
        key="nl_prompt",
    )

    col1, col2 = st.columns([1, 4])
    if col1.button("生成配置", type="primary"):
        if not nl_prompt:
            st.warning("请输入仿真需求描述")
        else:
            _generate_config(nl_prompt, selected_skill_name)

    # ─── Step 3: Config Preview & Edit ────────────────────────────
    if "draft_config" in st.session_state and st.session_state.get("draft_skill") == selected_skill_name:
        st.subheader("3️⃣ 配置预览与编辑")
        _edit_config(selected_skill_name)


def _generate_config(prompt: str, skill_name: str):
    """Generate config from natural language."""
    with st.spinner("正在生成配置..."):
        gen = SmartConfigGenerator()
        config = gen.generate_config(prompt)

        # Override skill with user selection if different
        config["skill"] = skill_name

        st.session_state.draft_config = config
        st.session_state.draft_skill = skill_name
        st.session_state.draft_prompt = prompt
        st.session_state.validation_errors = []
        st.success("配置已生成，请在下方预览和编辑")
        st.rerun()


def _load_example(skill_name: str):
    """Load a working example config for a skill into draft state."""
    if skill_name == "study_pipeline":
        # Pipeline needs a meaningful example with steps, not an empty pipeline
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        tpl = templates["潮流 + N-1 + 可视化"]
        config = {
            "skill": "study_pipeline",
            "auth": {"token_file": ".cloudpss_token"},
            "model": {"rid": "model/holdme/IEEE39", "source": "cloud"},
            "pipeline": tpl,
            "continue_on_failure": False,
            "max_workers": 4,
            "output": {"format": "json", "path": "./results/", "timestamp": True},
        }
    else:
        skill = skill_catalog.get_skill(skill_name)
        if skill is None:
            st.error(f"未找到技能: {skill_name}")
            return
        config = skill.get_default_config()

    st.session_state.draft_config = config
    st.session_state.draft_skill = skill_name
    st.session_state.draft_prompt = f"示例: {skill_name}"
    st.session_state.validation_errors = []
    st.rerun()


def _edit_config(skill_name: str):
    """Display editable config with real-time validation."""
    config = st.session_state.draft_config

    skill = skill_catalog.get_skill(skill_name)

    # ─── Show NL prompt info ───────────────────────────────
    prompt = st.session_state.get("draft_prompt", "")
    if prompt:
        st.caption(f"📝 原始输入: {prompt}")

    # ─── Editable sections using expander UI ────────────────
    # Model section
    with st.expander("📦 模型配置", expanded=True):
        model = config.get("model", {})
        model["rid"] = st.text_input("模型 RID", value=model.get("rid", ""), key="edit_model_rid")
        model["source"] = st.selectbox(
            "模型来源",
            options=["cloud", "local"],
            index=0 if model.get("source", "cloud") == "cloud" else 1,
            key="edit_model_source",
        )
        config["model"] = model

    # Skill-specific section - show key parameters based on skill type
    if skill_name == "study_pipeline":
        from web.components.pipeline_editor import render_pipeline_editor
        render_pipeline_editor(config)
    else:
        _edit_skill_params(config, skill_name)

    # Output section
    with st.expander("📤 输出配置", expanded=False):
        output = config.get("output", {})
        output["format"] = st.selectbox(
            "输出格式",
            options=["json", "csv", "yaml"],
            index=["json", "csv", "yaml"].index(output.get("format", "json")),
            key="edit_output_format",
        )
        config["output"] = output

    # ─── YAML Preview ──────────────────────────────────────
    with st.expander("📄 完整 YAML 预览", expanded=False):
        import yaml
        from scripts.smart_config import ConfigDumper
        yaml_str = yaml.dump(config, Dumper=ConfigDumper, allow_unicode=True, sort_keys=False, default_flow_style=False)
        st.code(yaml_str, language="yaml")

    # ─── Validation ────────────────────────────────────────
    if skill is not None:
        try:
            validation = skill.validate(config)
            is_valid = getattr(validation, "valid", False)
            errors = getattr(validation, "errors", [])

            if is_valid:
                st.success("✅ 配置验证通过")
            else:
                st.error(f"❌ 配置验证失败 ({len(errors)} 个错误):")
                for err in errors:
                    st.warning(f"- {err}")
                st.session_state.validation_errors = errors
        except Exception as e:
            st.warning(f"⚠️ 验证过程出错: {e}")

    # ─── Confirm & Run ────────────────────────────────────
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    if col1.button("✅ 确认执行", type="primary"):
        _confirm_and_run(config, skill_name)

    if col2.button("🔄 重新生成"):
        st.session_state.draft_config = None
        st.session_state.draft_skill = None
        st.rerun()


def _edit_skill_params(config: dict, skill_name: str):
    """Edit skill-specific parameters based on skill type."""
    labels = {
        "power_flow": "⚡ 潮流计算参数",
        "emt_simulation": "📈 EMT暂态仿真参数",
        "emt_fault_study": "🔥 EMT故障研究参数",
        "short_circuit": "💥 短路计算参数",
        "n1_security": "🔒 N-1安全校核参数",
        "param_scan": "📊 参数扫描参数",
    }

    section_label = labels.get(skill_name, "⚙️ 技能参数")
    with st.expander(section_label, expanded=True):
        if skill_name == "power_flow":
            algo = config.get("algorithm", {})
            algo["type"] = st.selectbox(
                "算法",
                options=["newton_raphson", "fast_decoupled"],
                index=0 if algo.get("type", "newton_raphson") == "newton_raphson" else 1,
                key="edit_algo_type",
            )
            algo["tolerance"] = st.number_input(
                "收敛精度",
                value=float(algo.get("tolerance", 1e-6)),
                format="%.0e",
                key="edit_tolerance",
            )
            algo["max_iterations"] = st.number_input(
                "最大迭代次数",
                value=int(algo.get("max_iterations", 100)),
                key="edit_max_iterations",
            )
            config["algorithm"] = algo

        elif skill_name == "emt_simulation":
            sim = config.get("simulation", {})
            sim["duration"] = st.number_input(
                "仿真时长（秒）",
                value=float(sim.get("duration", 5.0)),
                format="%.4f",
                key="edit_duration",
            )
            sim["step_size"] = st.number_input(
                "积分步长（秒）",
                value=float(sim.get("step_size", 0.0001)),
                format="%.0e",
                key="edit_step_size",
            )
            sim["timeout"] = st.number_input(
                "最大等待时间（秒）",
                value=int(sim.get("timeout", 300)),
                key="edit_timeout",
            )
            config["simulation"] = sim

        else:
            # Generic: show editable JSON
            st.caption("该技能的配置参数（可编辑 JSON）")
            # Remove common sections to show only skill-specific config
            skill_config = {k: v for k, v in config.items() if k not in ("skill", "auth", "model", "output")}
            if skill_config:
                json_str = st.text_area(
                    "技能配置 (JSON)",
                    value=json.dumps(skill_config, indent=2, ensure_ascii=False),
                    height=200,
                    key="edit_skill_json",
                )
                try:
                    parsed = json.loads(json_str)
                    # Merge back into config
                    for k, v in parsed.items():
                        if k not in ("skill", "auth", "model", "output"):
                            config[k] = v
                except json.JSONDecodeError:
                    st.error("JSON 格式错误，请检查")


def _confirm_and_run(config: dict, skill_name: str):
    """Save task and trigger async execution."""
    name = st.session_state.get("draft_prompt", "")[:50] or f"{skill_name}_task"
    prompt = st.session_state.get("draft_prompt", "")

    task = task_store.create_task(
        name=name,
        skill_name=skill_name,
        config=config,
        config_source="nl",
        nl_prompt=prompt,
    )
    task.status = "confirmed"
    task_store.save_task(task)

    # Start execution in background
    task_executor.run_async(task.id)

    st.session_state.current_task_id = task.id
    st.session_state.page = "results"
    st.success(f"✅ 任务已创建并开始执行: {task.id}")
    st.rerun()
