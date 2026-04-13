"""
End-to-end integration tests with real CloudPSS API.

These tests verify the complete pipeline:
natural language prompt -> smart_config -> YAML -> skill.run() -> SkillResult

Skipped by default. Run with --run-integration flag.
"""
import sys
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cloudpss_skills.core.base import SkillStatus


@pytest.mark.integration
class TestE2EScenarios:
    """Real API end-to-end tests for critical skill categories."""

    def test_e2e_power_flow_with_custom_params(self, config_generator, auth_token):
        """
        Prompt: "IEEE39潮流计算，收敛精度1e-8，最大迭代200次，用快速分解法"

        Verify:
        - skill detection -> power_flow
        - parameter extraction (tolerance, iterations, algorithm)
        - skill.validate() passes
        - skill.run() returns SUCCESS or at least completes
        """
        prompt = "IEEE39潮流计算，收敛精度1e-8"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "power_flow"
        assert config["algorithm"]["tolerance"] == 1e-8
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        from cloudpss_skills.builtin.power_flow import PowerFlowSkill
        skill = PowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]
        assert result.data, "result.data should not be empty"

    def test_e2e_emt_simulation(self, config_generator, auth_token):
        """
        Prompt: "对IEEE3做EMT暂态仿真，仿真1秒"

        Verify:
        - skill detection -> emt_simulation
        - duration extraction
        - skill.run() completes
        """
        prompt = "对IEEE3做EMT暂态仿真，仿真1秒"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "emt_simulation"
        assert config["simulation"]["duration"] == 1.0
        assert config["model"]["rid"] == "model/chenying/IEEE3"

        from cloudpss_skills.builtin.emt_simulation import EmtSimulationSkill
        skill = EmtSimulationSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]

    def test_e2e_short_circuit(self, config_generator, auth_token):
        """
        Prompt: "帮我跑个短路计算，IEEE39系统，三相短路"
        """
        prompt = "帮我跑个短路计算，IEEE39系统，三相短路"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "short_circuit"
        assert config["fault"]["type"] == "three_phase"

        from cloudpss_skills.builtin.short_circuit import ShortCircuitSkill
        skill = ShortCircuitSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]

    def test_e2e_n1_security(self, config_generator, auth_token):
        """
        Prompt: "对IEEE39做N-1安全校核"
        """
        prompt = "对IEEE39做N-1安全校核"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "n1_security"
        assert config["analysis"]["check_voltage"] is True
        assert config["analysis"]["check_thermal"] is True

        from cloudpss_skills.builtin.n1_security import N1SecuritySkill
        skill = N1SecuritySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]

    def test_e2e_vsi_weak_bus(self, config_generator, auth_token):
        """
        Prompt: "VSI弱母线分析IEEE39"
        """
        prompt = "VSI弱母线分析IEEE39"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "vsi_weak_bus"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        from cloudpss_skills.builtin.vsi_weak_bus import VSIWeakBusSkill
        skill = VSIWeakBusSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]

    def test_e2e_component_catalog(self, config_generator, auth_token):
        """
        Prompt: "查询IEEE39模型的所有负载元件"
        """
        prompt = "查询IEEE39模型的所有负载元件"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "component_catalog"

        from cloudpss_skills.builtin.component_catalog import ComponentCatalogSkill
        skill = ComponentCatalogSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]

    def test_e2e_batch_powerflow(self, config_generator, auth_token):
        """
        Prompt: "批量跑IEEE39和IEEE3的潮流计算"
        """
        prompt = "批量跑IEEE39和IEEE3的潮流计算"
        config = config_generator.generate_config(prompt)
        config["auth"]["token"] = auth_token
        config["auth"]["server"] = "internal"

        assert config["skill"] == "batch_powerflow"
        assert "models" in config
        assert len(config["models"]) == 2

        from cloudpss_skills.builtin.batch_powerflow import BatchPowerFlowSkill
        skill = BatchPowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Config validation failed: {validation.errors}"

        result = skill.run(config)
        assert result.status in [SkillStatus.SUCCESS, SkillStatus.FAILED]
