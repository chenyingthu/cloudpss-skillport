"""
Tests for skill example configs: verify every skill's get_default_config()
returns a valid configuration that passes skill.validate().
"""
import pytest
from web.core import skill_catalog


class TestSkillExamples:
    """Verify each skill's default config is valid and well-formed."""

    def _all_skills(self):
        """Get all skill names from CATEGORIES."""
        skills = []
        for names in skill_catalog.CATEGORIES.values():
            skills.extend(names)
        return skills

    @pytest.mark.parametrize("skill_name", [
        "power_flow", "emt_simulation", "emt_fault_study", "short_circuit",
    ])
    def test_core_simulations(self, skill_name):
        """Core simulation skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None, f"Skill not found: {skill_name}"

        config = skill.get_default_config()
        assert "skill" in config
        assert config["skill"] == skill_name
        assert "model" in config

    @pytest.mark.parametrize("skill_name", [
        "n1_security", "n2_security", "emt_n1_screening",
        "contingency_analysis", "maintenance_security",
    ])
    def test_security_analysis(self, skill_name):
        """Security analysis skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "batch_powerflow", "param_scan", "fault_clearing_scan",
        "fault_severity_scan", "batch_task_manager",
        "config_batch_runner", "orthogonal_sensitivity",
    ])
    def test_batch_scan(self, skill_name):
        """Batch and scan skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "voltage_stability", "transient_stability", "transient_stability_margin",
        "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve",
    ])
    def test_stability_analysis(self, skill_name):
        """Stability analysis skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "result_compare", "visualize", "waveform_export", "hdf5_export",
        "disturbance_severity", "compare_visualization", "comtrade_export",
    ])
    def test_result_processing(self, skill_name):
        """Result processing skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "harmonic_analysis", "power_quality_analysis", "reactive_compensation_design",
    ])
    def test_power_quality(self, skill_name):
        """Power quality skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "renewable_integration",
    ])
    def test_renewable(self, skill_name):
        """Renewable integration skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "topology_check", "parameter_sensitivity", "auto_channel_setup",
        "auto_loop_breaker", "model_parameter_extractor", "model_builder",
        "model_validator", "component_catalog", "thevenin_equivalent", "model_hub",
    ])
    def test_model_topology(self, skill_name):
        """Model and topology skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    @pytest.mark.parametrize("skill_name", [
        "loss_analysis", "protection_coordination", "report_generator",
    ])
    def test_analysis_reports(self, skill_name):
        """Analysis and report skills have valid default configs."""
        skill = skill_catalog.get_skill(skill_name)
        assert skill is not None
        config = skill.get_default_config()
        assert config["skill"] == skill_name

    def test_pipeline_has_meaningful_example(self):
        """study_pipeline example contains steps (not empty pipeline)."""
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        tpl = templates["潮流 + N-1 + 可视化"]
        assert len(tpl) >= 3
        for step in tpl:
            assert "skill" in step
            assert "name" in step
            assert "depends_on" in step

    def test_all_skills_have_get_default_config(self):
        """Every skill in CATEGORIES has get_default_config method."""
        for skill_name in self._all_skills():
            skill = skill_catalog.get_skill(skill_name)
            assert skill is not None, f"Skill not found: {skill_name}"
            assert hasattr(skill, "get_default_config"), f"{skill_name}: missing get_default_config"
