"""
Task Create: Natural language input → config draft → preview/edit → confirm.

Flow:
1. User selects skill from sidebar (pre-selected mode) or skill picker (fallback)
2. SmartConfigGenerator generates draft config from NL input
3. Config is shown in editable form
4. Real-time validation via skill.validate()
5. User confirms → task saved as "confirmed" → trigger execution
"""
import json
from pathlib import Path
from typing import Optional
import streamlit as st

from web.core import task_store, skill_catalog, task_executor, favorites
from web.components import settings as settings_mod
from smart_config import SmartConfigGenerator

# Settings file for user_name resolution (fallback)
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "web" / "data" / "settings.json"
DEFAULT_USER = "chenying"  # Fallback if user_name not configured


def _get_current_user(profile_id: str = None) -> str:
    """Get user name from a specific profile, or active profile if none specified."""
    s = settings_mod.load_settings()
    if profile_id:
        profile = settings_mod.get_profile_by_id(s, profile_id)
        if profile and profile.get("user_name", "").strip():
            return profile["user_name"].strip()
    # Fallback to active profile
    active = settings_mod.get_active_profile(s)
    if active and active.get("user_name", "").strip():
        return active["user_name"].strip()
    return DEFAULT_USER


def _get_selected_profile_id() -> Optional[str]:
    """Get the profile ID selected in the task creation form, or the default profile."""
    session_id = st.session_state.get("selected_profile_id")
    if session_id:
        s = settings_mod.load_settings()
        if settings_mod.get_profile_by_id(s, session_id):
            return session_id
    return settings_mod.get_default_profile_id(settings_mod.load_settings())


def _normalize_model_rid(config: dict, user: str = None) -> dict:
    """Replace holdme model RIDs with current user's equivalents."""
    if user is None:
        user = _get_current_user()
    model = config.get("model", {})
    rid = model.get("rid", "")
    if rid.startswith("model/holdme/"):
        model["rid"] = rid.replace("model/holdme/", f"model/{user}/")
        config["model"] = model
    # Also fix pipeline steps if present
    for step in config.get("pipeline", []):
        step_model = step.get("model", {})
        step_rid = step_model.get("rid", "")
        if step_rid.startswith("model/holdme/"):
            step_model["rid"] = step_rid.replace("model/holdme/", f"model/{user}/")
            step["model"] = step_model
    return config


def _render_profile_selector() -> Optional[str]:
    """Render a profile selector dropdown for task creation. Returns selected profile ID."""
    s = settings_mod.load_settings()
    profiles = s.get("profiles", [])
    if not profiles:
        return None

    default_id = settings_mod.get_default_profile_id(s)
    current = st.session_state.get("selected_profile_id", default_id)
    if not current or not settings_mod.get_profile_by_id(s, current):
        current = default_id

    # Build options list
    options = [(p["id"], p.get("name", "未命名")) for p in profiles]

    # Find current index
    idx = 0
    for i, (pid, _) in enumerate(options):
        if pid == current:
            idx = i
            break

    selected_id = st.selectbox(
        "配置方案",
        options=[o[0] for o in options],
        index=idx,
        format_func=lambda pid: next((name for pid2, name in options if pid2 == pid), pid),
        key="profile_selector",
    )

    st.session_state.selected_profile_id = selected_id
    return selected_id


def render():
    st.title("➕ 创建仿真任务")

    # Profile selector at top
    _render_profile_selector()

    # Check if skill pre-selected from sidebar
    pre_selected = st.session_state.get("selected_skill")

    if pre_selected and skill_catalog.get_skill(pre_selected) is not None:
        _render_skill_form(pre_selected)
    else:
        # Fallback: show skill picker if no pre-selection
        _render_skill_picker()


def _render_skill_picker():
    """Fallback skill picker when no skill is pre-selected from sidebar."""
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

    # Quick help panel
    _render_quick_help(selected_skill_name)

    col_a, col_b = st.columns([1, 4])
    if col_a.button("📋 加载示例", help="加载一个可运行的示例配置"):
        _load_example(selected_skill_name)

    # ─── Step 2: Natural Language Input ───────────────────────────
    st.subheader("2️⃣ 描述仿真需求")

    # ─── Sync text_area when draft config exists (from example or NL gen) ──
    if "draft_config" in st.session_state and st.session_state.get("draft_skill") == selected_skill_name:
        prompt = st.session_state.get("draft_prompt", "")
        version = st.session_state.get("draft_version", 0)
        nl_prompt = st.text_area(
            "用自然语言描述仿真需求",
            value=prompt,
            placeholder="例如：帮我跑个IEEE39潮流计算，收敛精度1e-8",
            height=80,
            key=f"nl_prompt_{version}",
        )
    else:
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


def _render_skill_form(skill_name: str):
    """Render task creation form for a pre-selected skill from sidebar."""
    skill_info = skill_catalog.get_skill_info(skill_name)

    # Show skill name and description
    st.subheader(skill_info.get("name", skill_name))
    if skill_info.get("description"):
        st.caption(skill_info["description"])

    # Quick help panel (includes favorite button)
    _render_quick_help(skill_name, show_favorite=True)

    col_a, col_b = st.columns([1, 4])
    if col_a.button("📋 加载示例", help="加载一个可运行的示例配置"):
        _load_example(skill_name)

    # Natural Language Input
    st.subheader("描述仿真需求")

    # ─── Sync text_area when draft config exists (from example or NL gen) ──
    if "draft_config" in st.session_state and st.session_state.get("draft_skill") == skill_name:
        prompt = st.session_state.get("draft_prompt", "")
        version = st.session_state.get("draft_version", 0)
        nl_prompt = st.text_area(
            "用自然语言描述仿真需求",
            value=prompt,
            placeholder="例如：帮我跑个IEEE39潮流计算，收敛精度1e-8",
            height=80,
            key=f"nl_prompt_v{version}",
        )
    else:
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
            _generate_config(nl_prompt, skill_name)

    # Config Preview & Edit
    if "draft_config" in st.session_state and st.session_state.get("draft_skill") == skill_name:
        st.subheader("配置预览与编辑")
        _edit_config(skill_name)


def _render_quick_help(skill_name: str, show_favorite: bool = False):
    """Render a quick help expander with skill features, use cases, and doc link."""
    from web.core import skill_catalog as sc

    quick = sc.get_quick_help(skill_name)
    doc_url = sc.get_skill_doc_url(skill_name)

    with st.expander("📖 快捷说明", expanded=False):
        # Favorite toggle button
        if show_favorite:
            fav = favorites.is_favorite(skill_name)
            col_fav, _ = st.columns([1, 4])
            if col_fav.button("⭐ 收藏" if not fav else "💫 已收藏", key="fav_toggle"):
                favorites.toggle_favorite(skill_name)
                st.rerun()

        # Features
        if quick.get("features"):
            st.markdown("**功能特性**")
            for f in quick["features"]:
                st.markdown(f"- {f}")

        # Use cases
        if quick.get("use_cases"):
            st.markdown("**典型用途**")
            for u in quick["use_cases"]:
                st.markdown(f"- {u}")

        # Example prompt
        if quick.get("example"):
            st.markdown(f"**自然语言示例**: `{quick['example']}`")

        # Doc link
        st.markdown(f"[📄 完整文档]({doc_url})")


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
        st.session_state.draft_version = st.session_state.get("draft_version", 0) + 1
        st.session_state.validation_errors = []
        st.success("配置已生成，请在下方预览和编辑")
        st.rerun()



def _load_example(skill_name: str):
    """Load a working example config for a skill into draft state."""
    profile_id = _get_selected_profile_id()
    user = _get_current_user(profile_id)

    if skill_name == "study_pipeline":
        # Pipeline needs a meaningful example with steps, not an empty pipeline
        from web.components.pipeline_editor import _get_pipeline_templates
        import copy

        model_config = {"rid": f"model/{user}/IEEE39", "source": "cloud"}
        # Use absolute path for token file to ensure child steps can find it
        profile = settings_mod.get_profile_by_id(settings_mod.load_settings(), profile_id) if profile_id else None
        token_path = str(settings_mod.TOKEN_FILE)
        auth_config = {"token_file": token_path, "server": profile.get("server_preset", "public") if profile else "public"}

        templates = _get_pipeline_templates()
        tpl = templates["潮流 + N-1 + 可视化"]

        # Inject model and auth into each step's config
        injected_steps = []
        for step in tpl:
            step_copy = copy.deepcopy(step)
            if "config" not in step_copy:
                step_copy["config"] = {}
            # Always inject model and auth with absolute paths
            step_copy["config"]["model"] = copy.deepcopy(model_config)
            step_copy["config"]["auth"] = copy.deepcopy(auth_config)
            injected_steps.append(step_copy)

        config = {
            "skill": "study_pipeline",
            "auth": auth_config,
            "model": model_config,
            "pipeline": injected_steps,
            "continue_on_failure": False,
            "max_workers": 4,
            "output": {"format": "json", "path": "./results/", "timestamp": True},
        }

        # Also update pipeline_editor's session state
        st.session_state.pipeline_steps = injected_steps
    else:
        skill = skill_catalog.get_skill(skill_name)
        if skill is None:
            st.error(f"未找到技能: {skill_name}")
            return
        config = skill.get_default_config()
        config = _normalize_model_rid(config, user)

    st.session_state.draft_config = config
    st.session_state.draft_skill = skill_name
    st.session_state.draft_prompt = f"示例: {skill_name}"
    st.session_state.draft_version = st.session_state.get("draft_version", 0) + 1
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
        "vsi_weak_bus": "📊 VSI 弱母线分析参数",
        "param_scan": "📊 参数扫描参数",
    }

    section_label = labels.get(skill_name, "⚙️ 技能参数")
    with st.expander(section_label, expanded=True):
        if skill_name == "power_flow":
            algo = config.get("algorithm", {})
            col1, col2, col3 = st.columns(3)
            algo["type"] = col1.selectbox(
                "算法",
                options=["newton_raphson", "fast_decoupled"],
                index=0 if algo.get("type", "newton_raphson") == "newton_raphson" else 1,
                key="edit_algo_type",
            )
            algo["tolerance"] = col2.number_input(
                "收敛精度",
                value=float(algo.get("tolerance", 1e-6)),
                format="%.0e",
                key="edit_tolerance",
            )
            algo["max_iterations"] = col3.number_input(
                "最大迭代次数",
                value=int(algo.get("max_iterations", 100)),
                key="edit_max_iterations",
            )
            config["algorithm"] = algo

        elif skill_name == "emt_simulation":
            sim = config.get("simulation", {})
            col1, col2 = st.columns(2)
            sim["duration"] = col1.number_input(
                "仿真时长 (s)",
                value=float(sim.get("duration", 5.0)),
                format="%.2f",
                key="edit_duration",
            )
            sim["step_size"] = col2.number_input(
                "积分步长 (s)",
                value=float(sim.get("step_size", 0.0001)),
                format="%.0e",
                key="edit_step_size",
            )
            sim["timeout"] = col2.number_input(
                "最大等待时间 (s)",
                value=int(sim.get("timeout", 300)),
                key="edit_timeout",
            )
            config["simulation"] = sim

        elif skill_name == "n1_security":
            analysis = config.get("analysis", {})
            col1, col2 = st.columns(2)
            analysis["check_voltage"] = col1.checkbox(
                "电压越限检查",
                value=analysis.get("check_voltage", True),
                key="edit_check_voltage",
            )
            analysis["check_thermal"] = col2.checkbox(
                "热稳定检查",
                value=analysis.get("check_thermal", True),
                key="edit_check_thermal",
            )
            col3, col4 = st.columns(2)
            analysis["voltage_threshold"] = col3.number_input(
                "电压越限阈值 (p.u.)",
                value=float(analysis.get("voltage_threshold", 0.05)),
                format="%.3f",
                key="edit_voltage_threshold",
            )
            analysis["thermal_threshold"] = col4.number_input(
                "热稳定阈值 (p.u.)",
                value=float(analysis.get("thermal_threshold", 1.0)),
                format="%.2f",
                key="edit_thermal_threshold",
            )
            config["analysis"] = analysis

        elif skill_name == "vsi_weak_bus":
            vsi = config.get("vsi_setup", {})
            col1, col2 = st.columns(2)
            injection = vsi.get("injection", {})
            injection["v_base"] = col1.number_input(
                "基准电压 (kV)",
                value=float(injection.get("v_base", 220)),
                format="%.1f",
                key="edit_v_base",
            )
            injection["q_base"] = col2.number_input(
                "注入无功 (MVar)",
                value=float(injection.get("q_base", 100)),
                format="%.1f",
                key="edit_q_base",
            )
            injection["start_time"] = col1.number_input(
                "开始时间 (s)",
                value=float(injection.get("start_time", 8.0)),
                format="%.2f",
                key="edit_start_time",
            )
            injection["duration"] = col2.number_input(
                "无功注入持续时间 (s)",
                value=float(injection.get("duration", 0.5)),
                format="%.2f",
                key="edit_vsi_duration",
            )
            vsi["injection"] = injection

            bus_filter = vsi.get("bus_filter", {})
            col3, col4 = st.columns(2)
            bus_filter["v_min"] = col3.number_input(
                "母线最小电压 (kV)",
                value=float(bus_filter.get("v_min", 0.6)),
                format="%.1f",
                key="edit_v_min",
            )
            bus_filter["v_max"] = col4.number_input(
                "母线最大电压 (kV)",
                value=float(bus_filter.get("v_max", 300)),
                format="%.1f",
                key="edit_v_max",
            )
            vsi["bus_filter"] = bus_filter
            config["vsi_setup"] = vsi

        elif skill_name == "short_circuit":
            fault = config.get("fault", {})
            col1, col2 = st.columns(2)
            fault["location"] = col1.text_input(
                "短路位置母线 ID",
                value=fault.get("location", ""),
                key="edit_fault_location",
            )
            fault["type"] = col2.selectbox(
                "短路类型",
                options=["three_phase", "line_to_ground", "line_to_line"],
                index=["three_phase", "line_to_ground", "line_to_line"].index(
                    fault.get("type", "three_phase")
                ),
                key="edit_fault_type",
            )
            col3, col4 = st.columns(2)
            fault["resistance"] = col3.number_input(
                "短路电阻 (Ω)",
                value=float(fault.get("resistance", 0.0001)),
                format="%.4f",
                key="edit_fault_resistance",
            )
            fault["fs"] = col4.number_input(
                "故障开始时间 (s)",
                value=float(fault.get("fs", 2.0)),
                format="%.2f",
                key="edit_fault_fs",
            )
            fault["fe"] = col4.number_input(
                "故障结束时间 (s)",
                value=float(fault.get("fe", 2.1)),
                format="%.2f",
                key="edit_fault_fe",
            )
            config["fault"] = fault

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

    # Store the selected profile ID for auth injection at execution time
    profile_id = _get_selected_profile_id()
    if profile_id:
        config["_profile_id"] = profile_id

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
    st.session_state.selected_skill = None  # Clear pre-selection
    st.success(f"✅ 任务已创建并开始执行: {task.id}")
    st.rerun()
