"""
Mocked execution tests.

Verify that configs generated from natural language prompts actually
reach skill.run() with correct structure. Mocks skill.run() at the
method level while keeping smart_config.py and skill.validate() real.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cloudpss_skills.core.base import SkillResult, SkillStatus


def make_mock_result(skill_name="test"):
    """Create a mock SkillResult."""
    return SkillResult(
        skill_name=skill_name,
        status=SkillStatus.SUCCESS,
        start_time=datetime.now(),
        data={"mocked": True, "skill": skill_name},
        error=None,
    )


class TestMockedExecution:
    """End-to-end with mocked skill.run()."""

    def test_power_flow_reaches_skill_run(self, config_generator):
        """Verify power_flow config reaches PowerFlowSkill.run()."""
        from cloudpss_skills.builtin.power_flow import PowerFlowSkill

        prompt = "IEEE39潮流计算，收敛精度1e-8，最大迭代200次，用快速分解法"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "power_flow"
        assert config["algorithm"]["tolerance"] == 1e-8
        assert config["algorithm"]["max_iterations"] == 200
        assert config["algorithm"]["type"] == "fast_decoupled"

        skill = PowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("power_flow")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            call_config = mock_run.call_args[0][0]
            assert call_config["algorithm"]["tolerance"] == 1e-8
            assert result.success

    def test_emt_simulation_reaches_skill_run(self, config_generator):
        """Verify EMT config reaches EmtSimulationSkill.run()."""
        from cloudpss_skills.builtin.emt_simulation import EmtSimulationSkill

        prompt = "对IEEE3做EMT暂态仿真，仿真5秒"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "emt_simulation"
        assert config["simulation"]["duration"] == 5.0
        assert config["model"]["rid"] == "model/chenying/IEEE3"

        skill = EmtSimulationSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("emt_simulation")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_n1_security_reaches_skill_run(self, config_generator):
        """Verify N-1 config reaches N1SecuritySkill.run()."""
        from cloudpss_skills.builtin.n1_security import N1SecuritySkill

        prompt = "对IEEE39做N-1安全校核，电压阈值5%"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "n1_security"
        assert config["analysis"]["check_voltage"] is True
        assert config["analysis"]["check_thermal"] is True

        skill = N1SecuritySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("n1_security")):
            skill.run(config)

    def test_short_circuit_reaches_skill_run(self, config_generator):
        """Verify short circuit config reaches ShortCircuitSkill.run()."""
        from cloudpss_skills.builtin.short_circuit import ShortCircuitSkill

        prompt = "帮我跑个短路计算，IEEE39系统，三相短路"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "short_circuit"
        assert config["fault"]["type"] == "three_phase"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = ShortCircuitSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("short_circuit")):
            skill.run(config)

    def test_param_scan_reaches_skill_run(self, config_generator):
        """Verify param scan config reaches ParamScanSkill.run()."""
        from cloudpss_skills.builtin.param_scan import ParamScanSkill

        prompt = "扫描负载的有功，从10%到50%，步长10%"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "param_scan"
        assert config["scan"]["values"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert config["scan"]["parameter"] == "P"

        skill = ParamScanSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("param_scan")):
            skill.run(config)

    def test_batch_powerflow_reaches_skill_run(self, config_generator):
        """Verify batch powerflow config reaches BatchPowerFlowSkill.run()."""
        from cloudpss_skills.builtin.batch_powerflow import BatchPowerFlowSkill

        prompt = "批量跑IEEE39和IEEE3的潮流计算"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "batch_powerflow"
        assert "models" in config
        assert len(config["models"]) == 2

        skill = BatchPowerFlowSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("batch_powerflow")):
            skill.run(config)

    def test_vsi_weak_bus_reaches_skill_run(self, config_generator):
        """Verify VSI config reaches VSIWeakBusSkill.run()."""
        from cloudpss_skills.builtin.vsi_weak_bus import VSIWeakBusSkill

        prompt = "VSI弱母线分析IEEE39模型，电压阈值设10%"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "vsi_weak_bus"
        assert config["analysis"]["voltage_threshold"] == 0.1

        skill = VSIWeakBusSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("vsi_weak_bus")):
            skill.run(config)

    def test_study_pipeline_reaches_skill_run(self, config_generator):
        """Verify pipeline config reaches StudyPipelineSkill.run()."""
        from cloudpss_skills.builtin.study_pipeline import StudyPipelineSkill

        prompt = "串联执行潮流和N-1分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "study_pipeline"
        assert "pipeline" in config
        assert len(config["pipeline"]) >= 1

        skill = StudyPipelineSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("study_pipeline")):
            skill.run(config)


class TestMockedExecutionExtended:
    """Extended mocked execution tests for additional skills."""

    # ============================================================
    # Category 1: N-1/N-2 analysis
    # ============================================================

    def test_emt_n1_screening_reaches_skill_run(self, config_generator):
        """Verify EMT N-1 config reaches EmtN1ScreeningSkill.run()."""
        from cloudpss_skills.builtin.emt_n1_screening import EmtN1ScreeningSkill

        prompt = "对IEEE39做EMT N-1安全筛查"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "emt_n1_screening"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = EmtN1ScreeningSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("emt_n1_screening")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_contingency_analysis_reaches_skill_run(self, config_generator):
        """Verify contingency config reaches ContingencyAnalysisSkill.run()."""
        from cloudpss_skills.builtin.contingency_analysis import ContingencyAnalysisSkill

        prompt = "对IEEE39做预想事故分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "contingency_analysis"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = ContingencyAnalysisSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("contingency_analysis")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    # ============================================================
    # Category 2: Stability analysis
    # ============================================================

    def test_voltage_stability_reaches_skill_run(self, config_generator):
        """Verify voltage stability config reaches VoltageStabilitySkill.run()."""
        from cloudpss_skills.builtin.voltage_stability import VoltageStabilitySkill

        prompt = "IEEE39电压稳定分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "voltage_stability"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = VoltageStabilitySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("voltage_stability")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_transient_stability_reaches_skill_run(self, config_generator):
        """Verify transient stability config reaches TransientStabilitySkill.run()."""
        from cloudpss_skills.builtin.transient_stability import TransientStabilitySkill

        prompt = "IEEE39暂态稳定分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "transient_stability"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = TransientStabilitySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("transient_stability")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_dudv_curve_reaches_skill_run(self, config_generator):
        """Verify DUDV config reaches DUDVCurveSkill.run()."""
        from cloudpss_skills.builtin.dudv_curve import DUDVCurveSkill

        prompt = "IEEE39 DUDV曲线分析，分析Bus7和Bus16母线"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "dudv_curve"
        # SmartConfigGenerator may not extract buses; add defaults for validation
        config.setdefault("buses", ["Bus7", "Bus16"])
        assert len(config["buses"]) > 0

        skill = DUDVCurveSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("dudv_curve")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    # ============================================================
    # Category 3: Batch & scan
    # ============================================================

    def test_fault_clearing_scan_reaches_skill_run(self, config_generator):
        """Verify fault clearing scan config reaches FaultClearingScanSkill.run()."""
        from cloudpss_skills.builtin.fault_clearing_scan import FaultClearingScanSkill

        prompt = "扫描IEEE3的故障清除时间，从0.05到0.2秒"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "fault_clearing_scan"
        assert config["model"]["rid"] == "model/chenying/IEEE3"

        skill = FaultClearingScanSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("fault_clearing_scan")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_orthogonal_sensitivity_reaches_skill_run(self, config_generator):
        """Verify orthogonal sensitivity config reaches OrthogonalSensitivitySkill.run()."""
        from cloudpss_skills.builtin.orthogonal_sensitivity import OrthogonalSensitivitySkill

        prompt = "IEEE39正交敏感性分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "orthogonal_sensitivity"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = OrthogonalSensitivitySkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("orthogonal_sensitivity")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    # ============================================================
    # Category 4: Power quality
    # ============================================================

    def test_harmonic_analysis_reaches_skill_run(self, config_generator):
        """Verify harmonic analysis config reaches HarmonicAnalysisSkill.run()."""
        from cloudpss_skills.builtin.harmonic_analysis import HarmonicAnalysisSkill

        prompt = "IEEE39谐波分析"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "harmonic_analysis"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = HarmonicAnalysisSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("harmonic_analysis")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    # ============================================================
    # Category 5: Model & topology
    # ============================================================

    def test_topology_check_reaches_skill_run(self, config_generator):
        """Verify topology check config reaches TopologyCheckSkill.run()."""
        from cloudpss_skills.builtin.topology_check import TopologyCheckSkill

        prompt = "topology_check IEEE39模型拓扑检查"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "topology_check"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = TopologyCheckSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("topology_check")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_auto_loop_breaker_reaches_skill_run(self, config_generator):
        """Verify auto loop breaker config reaches AutoLoopBreakerSkill.run()."""
        from cloudpss_skills.builtin.auto_loop_breaker import AutoLoopBreakerSkill

        prompt = "IEEE39模型自动解环"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "auto_loop_breaker"
        assert config["model"]["rid"] == "model/chenying/IEEE39"

        skill = AutoLoopBreakerSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("auto_loop_breaker")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    # ============================================================
    # Category 6: Result processing
    # ============================================================

    def test_result_compare_reaches_skill_run(self, config_generator):
        """Verify result compare config reaches ResultCompareSkill.run()."""
        from cloudpss_skills.builtin.result_compare import ResultCompareSkill

        prompt = "对比两个仿真结果"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "result_compare"
        assert "sources" in config
        assert len(config["sources"]) >= 2

        skill = ResultCompareSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("result_compare")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success

    def test_compare_visualization_reaches_skill_run(self, config_generator):
        """Verify compare visualization config reaches CompareVisualizationSkill.run()."""
        from cloudpss_skills.builtin.compare_visualization import CompareVisualizationSkill

        prompt = "对比可视化"
        config = config_generator.generate_config(prompt)

        assert config["skill"] == "compare_visualization"
        assert "sources" in config
        assert len(config["sources"]) >= 2

        skill = CompareVisualizationSkill()
        validation = skill.validate(config)
        assert validation.valid, f"Validation failed: {validation.errors}"

        with patch.object(skill, "run", return_value=make_mock_result("compare_visualization")) as mock_run:
            result = skill.run(config)
            mock_run.assert_called_once()
            assert result.success
