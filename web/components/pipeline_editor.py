"""
Pipeline Editor: Interactive pipeline step builder for study_pipeline skill.

Provides a visual step-by-step editor替代 generic JSON editing,
supporting depends_on, when, foreach, parallel, and YAML preview.
"""
import json
import streamlit as st


def render_pipeline_editor(config: dict):
    """Interactive pipeline step builder."""
    pipeline_steps = config.get("pipeline", [])
    if not pipeline_steps:
        pipeline_steps = [{"name": "", "skill": "", "config": {}, "depends_on": [], "parallel": False}]

    # Initialize session state for pipeline steps if not present
    if "pipeline_steps" not in st.session_state:
        st.session_state.pipeline_steps = pipeline_steps
    else:
        pipeline_steps = st.session_state.pipeline_steps

    # ─── Global Settings ──────────────────────────────────
    with st.expander("⚙️ 全局设置", expanded=False):
        col1, col2 = st.columns(2)
        config["continue_on_failure"] = col1.checkbox(
            "失败后继续",
            value=config.get("continue_on_failure", False),
            help="某个步骤失败后是否继续执行后续步骤",
        )
        config["max_workers"] = col2.number_input(
            "最大并行度",
            value=config.get("max_workers", 4),
            min_value=1,
            max_value=16,
            help="并行执行的最大线程数",
        )

    # ─── Step List ────────────────────────────────────────
    st.subheader("📋 流水线步骤")

    # Get available skills for selectbox
    from web.core import skill_catalog
    categories = skill_catalog.get_categorized_skills()
    skill_map = {}
    for cat_name, skills in categories.items():
        for s in skills:
            skill_map[s["name"]] = {"label": s["name"], "category": cat_name}

    for i, step in enumerate(pipeline_steps):
        _render_step_card(i, step, pipeline_steps, skill_map)

    # ─── Add / Remove / Reorder ──────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("➕ 添加步骤"):
        pipeline_steps.append({
            "name": "",
            "skill": "",
            "config": {},
            "depends_on": [],
            "parallel": False,
        })
        st.session_state.pipeline_steps = pipeline_steps
        st.rerun()

    if col2.button("⬆️ 上移") and len(pipeline_steps) > 1:
        idx = st.session_state.get("_step_move_idx", 0)
        if idx > 0:
            pipeline_steps[idx - 1], pipeline_steps[idx] = pipeline_steps[idx], pipeline_steps[idx - 1]
            st.session_state.pipeline_steps = pipeline_steps
            st.rerun()

    if col3.button("⬇️ 下移") and len(pipeline_steps) > 1:
        idx = st.session_state.get("_step_move_idx", 0)
        if idx < len(pipeline_steps) - 1:
            pipeline_steps[idx + 1], pipeline_steps[idx] = pipeline_steps[idx], pipeline_steps[idx + 1]
            st.session_state.pipeline_steps = pipeline_steps
            st.rerun()

    if col4.button("🗑️ 删除步骤") and len(pipeline_steps) > 1:
        idx = st.session_state.get("_step_move_idx", 0)
        if len(pipeline_steps) > 1:
            pipeline_steps.pop(idx)
            st.session_state.pipeline_steps = pipeline_steps
            st.rerun()

    # ─── Step selector slider ─────────────────────────────
    if len(pipeline_steps) > 1:
        move_idx = st.slider(
            "选择要移动的步骤",
            min_value=0,
            max_value=len(pipeline_steps) - 1,
            value=0,
            format_func=lambda x: pipeline_steps[x].get("name", pipeline_steps[x].get("skill", f"步骤{x+1}")),
            key="_step_move_idx",
        )

    # ─── Quick Templates ─────────────────────────────────
    st.markdown("---")
    st.subheader("📦 快速模板")
    st.caption("选择预定义的流水线模板快速开始")
    templates = _get_pipeline_templates()
    selected_template = st.selectbox(
        "选择模板",
        options=list(templates.keys()),
        format_func=lambda x: x,
    )
    if st.button("📥 应用模板"):
        tpl = templates[selected_template]
        st.session_state.pipeline_steps = [s.copy() for s in tpl]
        config["continue_on_failure"] = False
        config["max_workers"] = 4
        st.rerun()

    # ─── Dependency Validation ────────────────────────────
    _validate_dependencies(pipeline_steps)

    # ─── YAML Preview ────────────────────────────────────
    st.markdown("---")
    with st.expander("📄 YAML 配置预览"):
        config["pipeline"] = pipeline_steps
        import yaml
        from scripts.smart_config import ConfigDumper
        yaml_str = yaml.dump(config, Dumper=ConfigDumper, allow_unicode=True, sort_keys=False, default_flow_style=False)
        st.code(yaml_str, language="yaml")

    # Update config in session state
    config["pipeline"] = pipeline_steps


def _render_step_card(index: int, step: dict, steps: list, skill_map: dict):
    """Render a single step card."""
    step_name = step.get("name", "") or step.get("skill", "") or f"步骤{index + 1}"
    is_expanded = st.session_state.get(f"_step_expanded_{index}", True)

    with st.expander(f"步骤 {index + 1}: {step_name}", expanded=is_expanded):
        # Basic info row
        col1, col2 = st.columns(2)
        step["name"] = col1.text_input(
            "步骤名称",
            value=step.get("name", ""),
            key=f"_step_name_{index}",
            placeholder="例如：潮流计算",
        )
        step["skill"] = col2.selectbox(
            "选择技能",
            options=[""] + list(skill_map.keys()),
            index=0 if not step.get("skill") else (list(skill_map.keys()).index(step["skill"]) + 1 if step["skill"] in skill_map else 0),
            key=f"_step_skill_{index}",
        )

        # Skill description
        if step.get("skill") and step["skill"] in skill_map:
            info = skill_catalog.get_skill_info(step["skill"])
            if info.get("description"):
                st.caption(info["description"])

        # Skill-specific config editor (rendered directly, no nested expander)
        st.markdown("**⚙️ 步骤配置**")
        _edit_step_config(step, index)

        # Advanced options row
        st.markdown("---")
        st.caption("高级选项")
        col1, col2, col3 = st.columns(3)

        # depends_on: multi-select from other step names
        other_names = [s.get("name", "") or s.get("skill", "") for i, s in enumerate(steps) if i != index and (s.get("name") or s.get("skill"))]
        step["depends_on"] = col1.multiselect(
            "依赖步骤",
            options=other_names,
            default=step.get("depends_on", []),
            key=f"_step_deps_{index}",
            help="此步骤必须等待的前置步骤",
        )

        # when: conditional expression
        step["when"] = col2.text_input(
            "执行条件",
            value=step.get("when", ""),
            key=f"_step_when_{index}",
            placeholder="例如: steps.潮流.success",
            help="条件表达式，为空则始终执行",
        )

        # parallel: checkbox
        step["parallel"] = col3.checkbox(
            "并行执行",
            value=step.get("parallel", False),
            key=f"_step_parallel_{index}",
        )

        # foreach: collapsible section (use container, not expander, to avoid nesting)
        st.markdown("**🔄 foreach 循环**")
        foreach = step.get("foreach", {})
        foreach_col1, foreach_col2 = st.columns(2)
        foreach["items"] = foreach_col1.text_input(
            "迭代数据路径",
            value=foreach.get("items", ""),
            key=f"_step_foreach_items_{index}",
            placeholder="steps.scan.data.items",
            help="前置步骤结果中的数据路径",
        )
        foreach["item_name"] = foreach_col2.text_input(
            "迭代变量名",
            value=foreach.get("item_name", "item"),
            key=f"_step_foreach_name_{index}",
            help="循环中当前项的变量名",
        )
        if foreach.get("items"):
            step["foreach"] = foreach
        elif "foreach" in step:
            del step["foreach"]

        # skip_on_failure
        step["skip_on_failure"] = st.checkbox(
            "前置失败时跳过",
            value=step.get("skip_on_failure", False),
            key=f"_step_skip_{index}",
            help="如果前置依赖步骤失败，是否跳过此步骤",
        )


def _edit_step_config(step: dict, index: int):
    """Edit skill-specific configuration for a step."""
    skill_name = step.get("skill", "")
    step_config = step.get("config", {})

    if skill_name == "power_flow":
        algo = step_config.get("algorithm", {})
        col1, col2, col3 = st.columns(3)
        algo["type"] = col1.selectbox(
            "算法",
            options=["newton_raphson", "fast_decoupled"],
            index=0 if algo.get("type", "newton_raphson") == "newton_raphson" else 1,
            key=f"_pf_algo_{index}",
        )
        algo["tolerance"] = col2.number_input(
            "收敛精度",
            value=float(algo.get("tolerance", 1e-6)),
            format="%.0e",
            key=f"_pf_tol_{index}",
        )
        algo["max_iterations"] = col3.number_input(
            "最大迭代次数",
            value=int(algo.get("max_iterations", 100)),
            key=f"_pf_max_{index}",
        )
        step_config["algorithm"] = algo

    elif skill_name == "emt_simulation":
        sim = step_config.get("simulation", {})
        col1, col2 = st.columns(2)
        sim["duration"] = col1.number_input(
            "仿真时长 (s)",
            value=float(sim.get("duration", 5.0)),
            format="%.2f",
            key=f"_emt_dur_{index}",
        )
        sim["step_size"] = col2.number_input(
            "积分步长 (s)",
            value=float(sim.get("step_size", 0.0001)),
            format="%.0e",
            key=f"_emt_step_{index}",
        )
        step_config["simulation"] = sim

    elif skill_name == "n1_security":
        analysis = step_config.get("analysis", {})
        analysis["check_voltage"] = st.checkbox(
            "电压越限检查",
            value=analysis.get("check_voltage", True),
            key=f"_n1_volt_{index}",
        )
        analysis["check_thermal"] = st.checkbox(
            "热稳定检查",
            value=analysis.get("check_thermal", True),
            key=f"_n1_thermal_{index}",
        )
        step_config["analysis"] = analysis

    else:
        # Generic: editable JSON
        st.caption("技能配置 (JSON)")
        json_str = st.text_area(
            "配置 JSON",
            value=json.dumps(step_config, indent=2, ensure_ascii=False) if step_config else "{}",
            height=120,
            key=f"_step_cfg_{index}",
        )
        try:
            step_config = json.loads(json_str)
        except json.JSONDecodeError:
            st.error("JSON 格式错误")

    step["config"] = step_config


def _validate_dependencies(steps: list) -> list[str]:
    """Validate pipeline dependencies and show warnings.

    Returns list of issue strings (empty if all valid).
    """
    names = {s.get("name", "") or s.get("skill", "") for s in steps if s.get("name") or s.get("skill")}
    issues = []

    for i, step in enumerate(steps):
        sname = step.get("name", "") or step.get("skill", "")
        if not sname:
            issues.append(f"步骤 {i + 1}: 未指定名称或技能")
            continue

        # Check depends_on references
        for dep in step.get("depends_on", []):
            if dep not in names:
                issues.append(f"步骤 '{sname}': 依赖的步骤 '{dep}' 不存在")

        # Check circular dependencies (simple: A depends on B, B depends on A)
        for dep in step.get("depends_on", []):
            dep_step = next((s for s in steps if (s.get("name", "") or s.get("skill", "")) == dep), None)
            if dep_step:
                dep_deps = dep_step.get("depends_on", [])
                if sname in dep_deps:
                    issues.append(f"循环依赖: '{sname}' ↔ '{dep}'")

    if issues:
        st.error("⚠️ 依赖验证失败:")
        for issue in issues:
            st.warning(f"- {issue}")
    else:
        st.success("✅ 依赖验证通过")

    return issues


def _get_pipeline_templates() -> dict:
    """Return predefined pipeline templates."""
    return {
        "潮流 + N-1 + 可视化": [
            {
                "name": "潮流计算",
                "skill": "power_flow",
                "config": {"algorithm": {"type": "newton_raphson", "tolerance": 1e-6, "max_iterations": 100}},
                "depends_on": [],
                "parallel": False,
            },
            {
                "name": "N-1分析",
                "skill": "n1_security",
                "config": {"analysis": {"check_voltage": True, "check_thermal": True}},
                "depends_on": ["潮流计算"],
                "parallel": False,
            },
            {
                "name": "可视化",
                "skill": "visualize",
                "config": {},
                "depends_on": ["N-1分析"],
                "parallel": False,
            },
        ],
        "EMT故障研究 + 对比分析": [
            {
                "name": "EMT仿真",
                "skill": "emt_simulation",
                "config": {"simulation": {"duration": 5.0, "step_size": 0.0001}},
                "depends_on": [],
                "parallel": False,
            },
            {
                "name": "故障研究",
                "skill": "emt_fault_study",
                "config": {},
                "depends_on": ["EMT仿真"],
                "parallel": False,
            },
            {
                "name": "对比分析",
                "skill": "result_compare",
                "config": {},
                "depends_on": ["故障研究"],
                "parallel": False,
            },
        ],
        "VSI弱母线 + 无功补偿": [
            {
                "name": "潮流计算",
                "skill": "power_flow",
                "config": {"algorithm": {"type": "newton_raphson", "tolerance": 1e-6, "max_iterations": 100}},
                "depends_on": [],
                "parallel": False,
            },
            {
                "name": "VSI弱母线分析",
                "skill": "vsi_weak_bus",
                "config": {},
                "depends_on": ["潮流计算"],
                "parallel": False,
            },
            {
                "name": "无功补偿设计",
                "skill": "reactive_compensation_design",
                "config": {},
                "depends_on": ["VSI弱母线分析"],
                "parallel": False,
            },
        ],
        "并行参数扫描": [
            {
                "name": "扫描A",
                "skill": "param_scan",
                "config": {},
                "depends_on": [],
                "parallel": True,
            },
            {
                "name": "扫描B",
                "skill": "param_scan",
                "config": {},
                "depends_on": [],
                "parallel": True,
            },
            {
                "name": "结果汇总",
                "skill": "result_compare",
                "config": {},
                "depends_on": ["扫描A", "扫描B"],
                "parallel": False,
            },
        ],
    }
