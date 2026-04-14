"""
Skill catalog: dynamic discovery from cloudpss-toolkit registry.

Wraps the toolkit's auto_discover() and list_skills() to provide
a cached, portal-friendly skill listing.
"""
from typing import Dict, Any, List, Optional
from functools import lru_cache


@lru_cache(maxsize=1)
def _discover():
    """Auto-discover all skills and cache the result.

    Note: Importing cloudpss_skills.builtin triggers auto-registration
    via module-level side effects in each skill file.
    """
    import cloudpss_skills.builtin  # noqa: F401 — triggers registration
    from cloudpss_skills import list_skills
    return list_skills()


def list_all() -> List[Any]:
    """Return list of all registered skill instances."""
    return _discover()


def get_skill(name: str) -> Optional[Any]:
    """Get a skill instance by name."""
    from cloudpss_skills import get_skill as toolkit_get_skill
    _discover()
    try:
        return toolkit_get_skill(name)
    except Exception:
        return None


def get_config_schema(name: str) -> Optional[Dict[str, Any]]:
    """Get the JSON schema for a skill's config."""
    skill = get_skill(name)
    if skill is None:
        return None
    return getattr(skill, "config_schema", {})


def get_skill_info(name: str) -> Dict[str, str]:
    """Get human-readable skill info for UI display."""
    skill = get_skill(name)
    if skill is None:
        return {"name": name, "description": "Unknown skill", "version": "?"}
    return {
        "name": getattr(skill, "name", name),
        "description": getattr(skill, "description", ""),
        "version": getattr(skill, "version", "1.0.0"),
    }


# Skill category mapping for UI grouping
CATEGORIES = {
    "仿真执行": ["power_flow", "emt_simulation", "emt_fault_study", "short_circuit"],
    "N-1/N-2安全": ["n1_security", "n2_security", "emt_n1_screening", "contingency_analysis", "maintenance_security"],
    "批量与扫描": ["batch_powerflow", "param_scan", "fault_clearing_scan", "fault_severity_scan", "batch_task_manager", "config_batch_runner", "orthogonal_sensitivity"],
    "稳定性分析": ["voltage_stability", "transient_stability", "transient_stability_margin", "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve"],
    "结果处理": ["result_compare", "visualize", "waveform_export", "hdf5_export", "disturbance_severity", "compare_visualization", "comtrade_export"],
    "电能质量": ["harmonic_analysis", "power_quality_analysis", "reactive_compensation_design"],
    "新能源": ["renewable_integration"],
    "模型与拓扑": ["topology_check", "parameter_sensitivity", "auto_channel_setup", "auto_loop_breaker", "model_parameter_extractor", "model_builder", "model_validator", "component_catalog", "thevenin_equivalent", "model_hub"],
    "分析报告": ["loss_analysis", "protection_coordination", "report_generator"],
    "流程编排": ["study_pipeline"],
}


def get_categorized_skills() -> Dict[str, List[Dict[str, str]]]:
    """Return skills grouped by category for the skill picker UI."""
    result = {}
    for category, skill_names in CATEGORIES.items():
        skills_in_cat = []
        for name in skill_names:
            skill = get_skill(name)
            if skill is not None:
                skills_in_cat.append({
                    "name": name,
                    "description": getattr(skill, "description", ""),
                })
        if skills_in_cat:
            result[category] = skills_in_cat
    return result
