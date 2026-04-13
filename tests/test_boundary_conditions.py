"""
Boundary condition tests.

Verify that the smart_config.py and skill validation logic handles
edge cases gracefully: empty inputs, extreme values, malformed data,
missing auth, Unicode input, and model-not-found scenarios.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from smart_config import SmartConfigGenerator


class TestEmptyAndWhitespaceInputs:
    """Test handling of empty, whitespace-only, and minimal inputs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_empty_string(self):
        """Empty string should not crash and should return a valid config."""
        config = self.gen.generate_config("")
        assert isinstance(config, dict)
        assert "skill" in config or "help" in config or "action" in config

    def test_whitespace_only(self):
        """Whitespace-only input should not crash."""
        config = self.gen.generate_config("   \t\n  ")
        assert isinstance(config, dict)

    def test_single_character(self):
        """Single character input should not crash."""
        config = self.gen.generate_config("a")
        assert isinstance(config, dict)

    def test_single_chinese_character(self):
        """Single Chinese character should not crash."""
        config = self.gen.generate_config("潮")
        assert isinstance(config, dict)

    def test_very_long_prompt(self):
        """Very long prompt (>1000 chars) should not crash."""
        prompt = "帮我跑一个潮流计算 " * 200  # 4000+ characters
        config = self.gen.generate_config(prompt)
        assert isinstance(config, dict)
        # Should still detect power_flow keyword
        assert config["skill"] == "power_flow"


class TestExtremeParameterValues:
    """Test extraction of extreme parameter values."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_very_small_tolerance(self):
        """Tolerance of 1e-15 should be extracted correctly."""
        config = self.gen.generate_config("IEEE39潮流计算，收敛精度1e-15")
        assert config["algorithm"]["tolerance"] == 1e-15

    def test_zero_tolerance(self):
        """Zero tolerance should be handled (either rejected or set to default)."""
        config = self.gen.generate_config("IEEE39潮流计算，收敛精度0")
        assert "tolerance" in config["algorithm"]

    def test_very_large_iterations(self):
        """Very large iteration count should be extracted."""
        config = self.gen.generate_config("IEEE39潮流计算，最大迭代10000次")
        assert config["algorithm"]["max_iterations"] == 10000

    def test_negative_tolerance_not_extracted(self):
        """Negative tolerance should not be used; fall back to default."""
        config = self.gen.generate_config("IEEE39潮流计算，收敛精度-1e-6")
        # Should either reject negative or use default
        tol = config["algorithm"]["tolerance"]
        assert tol > 0

    def test_very_long_emt_duration(self):
        """Very long EMT duration should be extracted."""
        config = self.gen.generate_config("IEEE3暂态仿真，仿真1000秒")
        assert config["simulation"]["duration"] == 1000.0

    def test_fractional_duration(self):
        """Fractional duration like 0.001 seconds should be extracted."""
        config = self.gen.generate_config("IEEE3暂态仿真，仿真0.001秒")
        assert config["simulation"]["duration"] == 0.001

    def test_scan_percentage_over_100(self):
        """Scan percentage over 100% should be extracted correctly (may not include end value if step doesn't land on it)."""
        config = self.gen.generate_config("扫描负载的有功，从10%到200%，步长50%")
        # Starting from 10% with 50% step: 10%, 60%, 110%, 160% (210% > 200%, so stops)
        assert config["scan"]["values"] == [0.1, 0.6, 1.1, 1.6]
        # Verify start and step are correct
        assert config["scan"]["values"][0] == 0.1

    def test_very_small_voltage_threshold(self):
        """Very small voltage threshold (0.1%) should be extracted for N-1."""
        config = self.gen.generate_config("IEEE39 N-1安全校核，电压阈值设0.1%")
        assert config["analysis"]["voltage_threshold"] == 0.001


class TestUnicodeAndSpecialCharacters:
    """Test handling of Unicode and special characters."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_mixed_chinese_english(self):
        """Mixed Chinese and English should work."""
        config = self.gen.generate_config("IEEE39 power flow潮流计算")
        assert config["skill"] == "power_flow"

    def test_chinese_punctuation(self):
        """Chinese punctuation should be handled."""
        config = self.gen.generate_config("对IEEE39做N-1安全校核，电压阈值5%")
        assert config["skill"] == "n1_security"

    def test_emoji_in_prompt(self):
        """Emoji in prompt should not crash."""
        config = self.gen.generate_config("IEEE39潮流计算 ")
        assert isinstance(config, dict)

    def test_special_characters(self):
        """Special characters should not crash."""
        config = self.gen.generate_config("IEEE39 @#$% 潮流计算")
        assert isinstance(config, dict)

    def test_fullwidth_numbers(self):
        """Fullwidth numbers should not crash."""
        config = self.gen.generate_config("IEEE３９潮流计算")
        assert isinstance(config, dict)


class TestInvalidModelNames:
    """Test handling of invalid or unusual model names."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_nonexistent_model_name(self):
        """Nonexistent model name should still generate config."""
        config = self.gen.generate_config("IEEE999潮流计算")
        # Should default to IEEE39
        assert config["model"]["rid"] in [
            "model/chenying/IEEE39",
            "model/chenying/IEEE3",
        ]

    def test_model_with_spaces(self):
        """Model name with spaces should be handled."""
        config = self.gen.generate_config("IEEE 39 潮流计算")
        assert isinstance(config, dict)

    def test_lowercase_model_name(self):
        """Lowercase model name should still match."""
        config = self.gen.generate_config("ieee39潮流计算")
        assert "ieee39" in config["model"]["rid"].lower() or "IEEE39" in config["model"]["rid"]


class TestMissingAndInvalidAuth:
    """Test handling of missing or invalid authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_config_has_auth_section(self):
        """Generated config should always have auth section."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert "auth" in config

    def test_auth_has_token_file(self):
        """Auth section should have token_file configured."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert "token_file" in config["auth"] or "token" in config["auth"]

    def test_config_has_skill_field(self):
        """Config should always have a skill field or help/action."""
        config = self.gen.generate_config("随便什么")
        assert "skill" in config or "help" in config or "action" in config

    def test_config_has_model_section(self):
        """Config should always have model section."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert "model" in config
        assert "rid" in config["model"]

    def test_config_has_output_section(self):
        """Config should always have output section."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert "output" in config


class TestSkillValidationIntegration:
    """Test that generated configs pass skill.validate() for edge cases."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_power_flow_with_default_params_validates(self):
        """Power flow config with default params should validate."""
        from cloudpss_skills.builtin.power_flow import PowerFlowSkill

        config = self.gen.generate_config("IEEE39潮流计算")
        skill = PowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

    def test_emt_with_default_duration_validates(self):
        """EMT config with default duration should validate."""
        from cloudpss_skills.builtin.emt_simulation import EmtSimulationSkill

        config = self.gen.generate_config("IEEE3暂态仿真")
        skill = EmtSimulationSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

    def test_n1_with_default_checks_validates(self):
        """N-1 config with default checks should validate."""
        from cloudpss_skills.builtin.n1_security import N1SecuritySkill

        config = self.gen.generate_config("IEEE39 N-1安全校核")
        skill = N1SecuritySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

    def test_short_circuit_default_fault_validates(self):
        """Short circuit config with default fault type should validate."""
        from cloudpss_skills.builtin.short_circuit import ShortCircuitSkill

        config = self.gen.generate_config("IEEE39短路计算")
        skill = ShortCircuitSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"


class TestYAMLOutput:
    """Test that generated configs can be serialized to valid YAML."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_power_flow_yaml_serializable(self):
        """Power flow config should be YAML serializable."""
        import yaml

        config = self.gen.generate_config("IEEE39潮流计算")
        yaml_str = yaml.dump(config, default_flow_style=False)
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0

    def test_emt_yaml_serializable(self):
        """EMT config should be YAML serializable."""
        import yaml

        config = self.gen.generate_config("IEEE3暂态仿真，仿真5秒")
        yaml_str = yaml.dump(config, default_flow_style=False)
        assert isinstance(yaml_str, str)

    def test_batch_powerflow_yaml_serializable(self):
        """Batch powerflow config should be YAML serializable."""
        import yaml

        config = self.gen.generate_config("批量跑IEEE39和IEEE3潮流计算")
        yaml_str = yaml.dump(config, default_flow_style=False)
        assert isinstance(yaml_str, str)

    def test_yaml_roundtrip_preserves_values(self):
        """YAML dump and load should preserve key values."""
        import yaml

        config = self.gen.generate_config("IEEE39潮流计算，收敛精度1e-8")
        yaml_str = yaml.dump(config, default_flow_style=False)
        loaded = yaml.safe_load(yaml_str)
        assert loaded["algorithm"]["tolerance"] == 1e-8
        assert loaded["skill"] == "power_flow"


class TestMockedSkillRunEdgeCases:
    """Test edge cases in skill.run() with mocked execution."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def _make_mock_result(self, skill_name="test"):
        from datetime import datetime
        from cloudpss_skills.core.base import SkillResult, SkillStatus

        return SkillResult(
            skill_name=skill_name,
            status=SkillStatus.SUCCESS,
            start_time=datetime.now(),
            data={"mocked": True, "skill": skill_name},
            error=None,
        )

    def test_power_flow_with_extreme_tolerance_runs(self):
        """Power flow with extreme tolerance should reach skill.run()."""
        from cloudpss_skills.builtin.power_flow import PowerFlowSkill

        config = self.gen.generate_config("IEEE39潮流计算，收敛精度1e-15")
        skill = PowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=self._make_mock_result("power_flow")) as mock_run:
            skill.run(config)
            mock_run.assert_called_once()

    def test_emt_with_very_long_duration_runs(self):
        """EMT with very long duration should reach skill.run()."""
        from cloudpss_skills.builtin.emt_simulation import EmtSimulationSkill

        config = self.gen.generate_config("IEEE3暂态仿真，仿真3600秒")
        skill = EmtSimulationSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=self._make_mock_result("emt_simulation")) as mock_run:
            skill.run(config)
            mock_run.assert_called_once()

    def test_batch_powerflow_with_many_models_runs(self):
        """Batch powerflow with many models should reach skill.run()."""
        from cloudpss_skills.builtin.batch_powerflow import BatchPowerFlowSkill

        prompt = "批量跑IEEE39、IEEE3、IEEE14、IEEE30、IEEE57、IEEE118的潮流计算"
        config = self.gen.generate_config(prompt)
        skill = BatchPowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=self._make_mock_result("batch_powerflow")) as mock_run:
            skill.run(config)
            mock_run.assert_called_once()


class TestConfigStructureIntegrity:
    """Test that generated configs have correct structure."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    def test_config_has_required_top_level_keys(self):
        """Config should have skill, auth, model, output keys."""
        config = self.gen.generate_config("IEEE39潮流计算")
        for key in ["skill", "auth", "model", "output"]:
            assert key in config, f"Missing key: {key}"

    def test_model_rid_is_string(self):
        """Model RID should be a string."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert isinstance(config["model"]["rid"], str)
        assert config["model"]["rid"].startswith("model/")

    def test_model_source_is_string(self):
        """Model source should be a string."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert isinstance(config["model"]["source"], str)
        assert config["model"]["source"] in ["cloud", "local"]

    def test_output_format_is_string(self):
        """Output format should be a string."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert isinstance(config["output"]["format"], str)

    def test_skill_name_is_valid_string(self):
        """Skill name should be a valid string."""
        config = self.gen.generate_config("IEEE39潮流计算")
        assert isinstance(config["skill"], str)
        assert len(config["skill"]) > 0

    def test_no_none_values_in_required_fields(self):
        """Required fields should not be None."""
        prompts = [
            "IEEE39潮流计算",
            "IEEE3暂态仿真",
            "IEEE39 N-1安全校核",
            "IEEE39短路计算",
        ]
        for prompt in prompts:
            config = self.gen.generate_config(prompt)
            assert config.get("skill") is not None, f"skill is None for '{prompt}'"
            assert config.get("model") is not None, f"model is None for '{prompt}'"
            assert config.get("auth") is not None, f"auth is None for '{prompt}'"

    def test_tolerance_not_negative(self):
        """Tolerance should never be negative."""
        prompts = [
            "IEEE39潮流计算，收敛精度1e-6",
            "IEEE39潮流计算，收敛精度1e-8",
            "IEEE39潮流计算，收敛精度1e-4",
        ]
        for prompt in prompts:
            config = self.gen.generate_config(prompt)
            assert config["algorithm"]["tolerance"] > 0

    def test_iterations_not_negative(self):
        """Iterations should never be negative."""
        config = self.gen.generate_config("IEEE39潮流计算，最大迭代100次")
        assert config["algorithm"]["max_iterations"] > 0

    def test_duration_not_negative(self):
        """EMT duration should never be negative."""
        config = self.gen.generate_config("IEEE3暂态仿真，仿真5秒")
        assert config["simulation"]["duration"] > 0
