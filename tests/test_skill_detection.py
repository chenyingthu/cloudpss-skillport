"""
Skill detection accuracy tests.

Verify that the smart_config.py skill detection logic correctly maps
natural language prompts to the right skill, including:
- Similar skill differentiation (emt_simulation vs emt_fault_study)
- Alias recognition (pf -> power_flow)
- Combined keyword patterns (批量.*潮流 -> batch_powerflow)
- False positive prevention (irrelevant input shouldn't match random skills)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from smart_config import SmartConfigGenerator


class TestSkillDetectionAccuracy:
    """Verify skill detection accuracy across all 48 skills."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SmartConfigGenerator()

    # ============================================================
    # Similar skill differentiation
    # ============================================================

    def test_emt_simulation_vs_fault_study(self):
        """EMT simulation should not be confused with EMT fault study."""
        c1 = self.gen.generate_config("对IEEE3做EMT暂态仿真，仿真5秒")
        c2 = self.gen.generate_config("对IEEE3做EMT故障研究，Bus1三相短路")

        assert c1["skill"] == "emt_simulation"
        assert c2["skill"] == "emt_fault_study"

    def test_n1_vs_n2_vs_contingency(self):
        """N-1, N-2, and contingency analysis should be distinct."""
        c1 = self.gen.generate_config("对IEEE39做N-1安全校核")
        c2 = self.gen.generate_config("对IEEE39做N-2双重故障分析")
        c3 = self.gen.generate_config("对IEEE39做预想事故分析")

        assert c1["skill"] == "n1_security"
        assert c2["skill"] == "n2_security"
        assert c3["skill"] == "contingency_analysis"

    def test_vsi_vs_voltage_stability(self):
        """VSI weak bus should not be confused with voltage stability."""
        c1 = self.gen.generate_config("VSI弱母线分析IEEE39")
        c2 = self.gen.generate_config("IEEE39电压稳定分析")

        assert c1["skill"] == "vsi_weak_bus"
        assert c2["skill"] == "voltage_stability"

    def test_short_circuit_vs_fault_study(self):
        """Short circuit calculation vs EMT fault study."""
        c1 = self.gen.generate_config("帮我跑个短路计算，IEEE39系统")
        c2 = self.gen.generate_config("对IEEE3做EMT故障研究")

        assert c1["skill"] == "short_circuit"
        assert c2["skill"] == "emt_fault_study"

    def test_visualize_vs_result_compare(self):
        """Visualization should not be confused with result comparison."""
        c1 = self.gen.generate_config("可视化潮流计算结果")
        c2 = self.gen.generate_config("对比两个仿真结果的Bus1电压")

        assert c1["skill"] == "visualize"
        assert c2["skill"] == "result_compare"

    def test_waveform_export_vs_hdf5_export(self):
        """Waveform export vs HDF5 export."""
        c1 = self.gen.generate_config("提取上次的EMT仿真波形")
        c2 = self.gen.generate_config("HDF5格式导出")

        assert c1["skill"] == "waveform_export"
        assert c2["skill"] == "hdf5_export"

    def test_comtrade_vs_waveform_export(self):
        """COMTRADE export vs waveform export."""
        c1 = self.gen.generate_config("导出COMTRADE格式")
        c2 = self.gen.generate_config("提取Bus7的三相电压波形")

        assert c1["skill"] == "comtrade_export"
        assert c2["skill"] == "waveform_export"

    def test_loss_analysis_vs_param_sensitivity(self):
        """Loss analysis vs parameter sensitivity."""
        c1 = self.gen.generate_config("分析IEEE39网损分布")
        c2 = self.gen.generate_config("IEEE39参数灵敏度分析")

        assert c1["skill"] == "loss_analysis"
        assert c2["skill"] == "parameter_sensitivity"

    def test_topo_check_vs_loop_breaker(self):
        """Topology check vs auto loop breaker."""
        c1 = self.gen.generate_config("检查IEEE39模型拓扑")
        c2 = self.gen.generate_config("IEEE39模型自动解环")

        assert c1["skill"] == "topology_check"
        assert c2["skill"] == "auto_loop_breaker"

    # ============================================================
    # Alias recognition
    # ============================================================

    def test_power_flow_aliases(self):
        """Various aliases for power flow should all map correctly."""
        aliases = [
            "帮我跑个IEEE39的潮流计算",
            "IEEE39 power flow",
            "IEEE39 load flow",
            "IEEE39稳态仿真",
            "帮我跑个pf仿真",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "power_flow", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_emt_aliases(self):
        """Various aliases for EMT should all map correctly."""
        aliases = [
            "IEEE3暂态仿真",
            "IEEE3 EMT仿真",
            "IEEE3 transient simulation",
            "IEEE3电磁暂态",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "emt_simulation", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_short_circuit_aliases(self):
        """Aliases for short circuit."""
        aliases = [
            "帮我跑个短路计算，IEEE39",
            "IEEE39 short circuit",
            "IEEE39短路电流",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "short_circuit", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_n1_aliases(self):
        """Aliases for N-1."""
        aliases = [
            "对IEEE39做N-1安全校核",
            "IEEE39 n1安全",
            "IEEE39安全评估",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "n1_security", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_vsi_aliases(self):
        """Aliases for VSI weak bus."""
        aliases = [
            "VSI弱母线分析IEEE39",
            "IEEE39 weak bus",
            "IEEE39电压稳定指标分析",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "vsi_weak_bus", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_pipeline_aliases(self):
        """Aliases for study pipeline."""
        aliases = [
            "串联执行潮流和N-1分析",
            "IEEE39 pipeline",
            "IEEE39流程编排",
            "IEEE39研究流程",
        ]
        for prompt in aliases:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "study_pipeline", f"Failed for '{prompt}': got '{config['skill']}'"

    # ============================================================
    # Combined keyword patterns
    # ============================================================

    def test_batch_powerflow_combined_keywords(self):
        """Combined keywords should trigger batch_powerflow, not power_flow."""
        combined = [
            "批量跑IEEE39和IEEE3的潮流计算",
            "批量运行IEEE39和IEEE9的潮流",
            "多模型潮流计算",
        ]
        for prompt in combined:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "batch_powerflow", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_auto_channel_combined_keywords(self):
        """Combined keywords for auto channel setup."""
        combined = [
            "自动配置EMT量测通道",
            "配置电压和电流量测通道",
        ]
        for prompt in combined:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "auto_channel_setup", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_component_catalog_patterns(self):
        """Component catalog should match various query patterns."""
        patterns = [
            "查询IEEE3模型的所有负载元件",
            "IEEE39模型有哪些发电机？",
            "列出所有可用模型",
            "列出IEEE39所有变压器元件",
        ]
        for prompt in patterns:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "component_catalog", f"Failed for '{prompt}': got '{config['skill']}'"

    def test_model_builder_patterns(self):
        """Model builder should match add/modify/delete patterns."""
        patterns = [
            "在IEEE3模型添加一个新的负载元件",
            "建模一个新的发电机",
            "添加新元件到IEEE39",
        ]
        for prompt in patterns:
            config = self.gen.generate_config(prompt)
            assert config["skill"] == "model_builder", f"Failed for '{prompt}': got '{config['skill']}'"

    # ============================================================
    # False positive prevention
    # ============================================================

    def test_power_flow_not_matched_by_unrelated(self):
        """Unrelated prompts should not trigger power_flow."""
        # Default is power_flow when no skill detected, so we check
        # that specific unrelated keywords go to the right skill
        c1 = self.gen.generate_config("cloudpss怎么使用？")
        assert c1.get("help") is not None or c1.get("skill") != "power_flow"

    def test_emt_not_matched_by_power_flow(self):
        """EMT-related should not be power_flow."""
        c = self.gen.generate_config("EMT暂态仿真是什么")
        assert c.get("action") == "explain" or c.get("skill") != "power_flow"

    def test_meta_operations_not_matched_as_skills(self):
        """Meta operations should produce help/action configs, not skill configs."""
        prompts = [
            ("cloudpss怎么使用？", "help"),
            ("验证这个配置文件: config.yaml", "action"),
            ("我的配置报错了: model not found", "action"),
            ("emt暂态仿真是什么", "action"),
        ]
        for prompt, expected_key in prompts:
            config = self.gen.generate_config(prompt)
            assert expected_key in config, (
                f"Failed for '{prompt}': expected key '{expected_key}' not in config. "
                f"Got skill='{config.get('skill')}', keys={list(config.keys())}"
            )

    # ============================================================
    # Default behavior
    # ============================================================

    def test_default_skill_for_unknown_input(self):
        """Unknown input should default to power_flow."""
        config = self.gen.generate_config("帮我跑个仿真")
        assert config["skill"] == "power_flow"

    def test_default_model_for_unknown(self):
        """Unknown model should default to IEEE39."""
        config = self.gen.generate_config("帮我跑个潮流计算")
        assert config["model"]["rid"] == "model/chenying/IEEE39"

    # ============================================================
    # Cross-category coverage (all 48 skills detectable)
    # ============================================================

    def test_all_skills_detectable(self):
        """Every skill in SKILL_KEYWORDS should be detectable with at least one prompt."""
        # Test a representative sample from each category
        test_cases = {
            # 仿真执行类
            "power_flow": "帮我跑个IEEE39潮流计算",
            "emt_simulation": "IEEE3暂态仿真",
            "emt_fault_study": "IEEE3故障研究",
            "short_circuit": "IEEE39短路计算",
            # N-1安全分析类
            "n1_security": "IEEE39 N-1安全校核",
            "n2_security": "IEEE39 N-2双重故障",
            "emt_n1_screening": "IEEE39 EMT暂态N-1筛查",
            "contingency_analysis": "IEEE39预想事故分析",
            "maintenance_security": "IEEE39检修安全校核",
            # 批量与扫描类
            "batch_powerflow": "批量跑IEEE39和IEEE3潮流",
            "param_scan": "参数扫描分析",
            "fault_clearing_scan": "故障清除时间扫描",
            "fault_severity_scan": "故障严重度扫描",
            "batch_task_manager": "批处理任务管理",
            "config_batch_runner": "多个配置场景运行",
            "orthogonal_sensitivity": "正交敏感性分析",
            # 稳定性分析类
            "voltage_stability": "电压稳定分析",
            "transient_stability": "暂态稳定分析",
            "transient_stability_margin": "CCT临界切除时间",
            "small_signal_stability": "小信号稳定分析",
            "frequency_response": "频率响应分析",
            "vsi_weak_bus": "VSI弱母线分析",
            "dudv_curve": "DUDV曲线分析",
            # 结果处理类
            "result_compare": "对比结果",
            "visualize": "我要看结果",
            "waveform_export": "提取仿真波形",
            "hdf5_export": "HDF5导出",
            "disturbance_severity": "扰动严重度分析",
            "compare_visualization": "对比可视化",
            "comtrade_export": "COMTRADE导出",
            # 电能质量类
            "harmonic_analysis": "谐波分析",
            "power_quality_analysis": "电能质量分析",
            "reactive_compensation_design": "无功补偿设计",
            # 模型与拓扑类
            "topology_check": "检查模型拓扑",
            "parameter_sensitivity": "参数灵敏度",
            "auto_channel_setup": "自动配置量测通道",
            "auto_loop_breaker": "模型自动解环",
            "model_parameter_extractor": "提取模型参数",
            "model_builder": "添加新元件",
            "model_validator": "验证模型",
            "component_catalog": "列出所有元件",
            "thevenin_equivalent": "戴维南等值阻抗",
            "model_hub": "算例中心克隆",
            # 分析与报告类
            "loss_analysis": "网损分析",
            "protection_coordination": "保护配合校验",
            "report_generator": "生成报告",
            # 流程编排类
            "study_pipeline": "串联执行潮流和N-1",
        }

        for expected_skill, prompt in test_cases.items():
            config = self.gen.generate_config(prompt)
            actual_skill = config.get("skill", config.get("action", "N/A"))
            assert actual_skill == expected_skill, (
                f"Skill detection mismatch for '{prompt}': "
                f"expected '{expected_skill}', got '{actual_skill}'"
            )
