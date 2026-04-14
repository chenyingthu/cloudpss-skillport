"""
Parameter extraction accuracy tests.

Verify that specific parameters are extracted with exact values from
natural language prompts. These are focused unit-level tests for the
extraction logic within SmartConfigGenerator.
"""
import sys
import math
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestParameterExtractionAccuracy:
    """Verify extraction logic accuracy."""

    # ---- Tolerance Extraction ----
    def test_tolerance_scientific_notation(self, config_generator):
        cases = [
            ("收敛精度1e-8", 1e-8),
            ("收敛精度1e-6", 1e-6),
            ("收敛精度1e-4", 1e-4),
        ]
        for prompt_suffix, expected in cases:
            config = config_generator.generate_config(
                f"IEEE39潮流计算，{prompt_suffix}"
            )
            actual = config["algorithm"]["tolerance"]
            assert math.isclose(actual, expected, rel_tol=1e-10), (
                f"Failed for '{prompt_suffix}': expected {expected}, got {actual}"
            )

    def test_tolerance_decimal_notation(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，收敛精度0.0001"
        )
        assert config["algorithm"]["tolerance"] == 1e-4

    def test_tolerance_high_precision_keyword(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，精度高一点"
        )
        assert config["algorithm"]["tolerance"] == 1e-8

    def test_tolerance_power_of_ten_notation(self, config_generator):
        """Test '10-3' style notation meaning 10^-3."""
        cases = [
            ("精度要求10-3", 1e-3),
            ("精度为10-4", 1e-4),
            ("精度要求10-6", 1e-6),
        ]
        for prompt, expected in cases:
            config = config_generator.generate_config(f"IEEE39潮流计算，{prompt}")
            actual = config["algorithm"]["tolerance"]
            assert math.isclose(actual, expected, rel_tol=1e-10), (
                f"Failed for '{prompt}': expected {expected}, got {actual}"
            )

    def test_tolerance_with_requirement_keyword(self, config_generator):
        """Test '精度要求' + scientific notation."""
        config = config_generator.generate_config(
            "IEEE39潮流计算，精度要求1e-8"
        )
        assert config["algorithm"]["tolerance"] == 1e-8

    # ---- Iteration Extraction ----
    def test_iterations(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，最大迭代200次"
        )
        assert config["algorithm"]["max_iterations"] == 200

    def test_iterations_alternate_format(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，迭代50次"
        )
        assert config["algorithm"]["max_iterations"] == 50

    # ---- Algorithm Extraction ----
    def test_algorithm_newton_raphson(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，用牛顿法"
        )
        assert config["algorithm"]["type"] == "newton_raphson"

    def test_algorithm_fast_decoupled(self, config_generator):
        config = config_generator.generate_config(
            "IEEE39潮流计算，用快速分解法"
        )
        assert config["algorithm"]["type"] == "fast_decoupled"

    # ---- Duration Extraction ----
    def test_duration_seconds(self, config_generator):
        cases = [
            ("仿真5秒钟", 5.0),
            ("仿真3.5秒", 3.5),
            ("仿真0.1s", 0.1),
        ]
        for prompt_suffix, expected in cases:
            config = config_generator.generate_config(
                f"对IEEE3做EMT暂态仿真，{prompt_suffix}"
            )
            actual = config["simulation"]["duration"]
            assert math.isclose(actual, expected, rel_tol=1e-10), (
                f"Failed for '{prompt_suffix}': expected {expected}, got {actual}"
            )

    # ---- Step Size Extraction ----
    def test_step_size(self, config_generator):
        config = config_generator.generate_config(
            "对IEEE3做EMT暂态仿真，步长0.00005"
        )
        assert config["simulation"]["step_size"] == 5e-5

    # ---- Scan Value Extraction ----
    def test_scan_percentage_values(self, config_generator):
        config = config_generator.generate_config(
            "扫描负载的有功，从10%到50%，步长10%"
        )
        expected = [0.1, 0.2, 0.3, 0.4, 0.5]
        actual = config["scan"]["values"]
        assert actual == expected, f"Expected {expected}, got {actual}"

    def test_scan_numeric_range(self, config_generator):
        config = config_generator.generate_config(
            "我想扫描Load_1的有功功率P，从10到50，每隔10一个点"
        )
        expected = [10, 20, 30, 40, 50]
        actual = config["scan"]["values"]
        assert actual == expected, f"Expected {expected}, got {actual}"

    # ---- Voltage Threshold Extraction ----
    def test_voltage_threshold_percentage(self, config_generator):
        config = config_generator.generate_config(
            "对IEEE39做N-1安全校核，电压阈值设成10%"
        )
        assert config["analysis"]["voltage_threshold"] == 0.1

    def test_vsi_weak_bus_threshold_percentage(self, config_generator):
        config = config_generator.generate_config(
            "VSI弱母线分析IEEE39模型，电压阈值设10%"
        )
        assert config["analysis"]["voltage_threshold"] == 0.1

    # ---- Model Extraction ----
    def test_model_ieee39(self, config_generator):
        config = config_generator.generate_config("IEEE39潮流计算")
        assert config["model"]["rid"] == "model/chenying/IEEE39"

    def test_model_ieee3(self, config_generator):
        config = config_generator.generate_config("IEEE3暂态仿真")
        assert config["model"]["rid"] == "model/chenying/IEEE3"

    def test_model_ieee9(self, config_generator):
        config = config_generator.generate_config("IEEE9潮流计算")
        assert config["model"]["rid"] == "model/chenying/IEEE9"

    # ---- Fault Type Extraction ----
    def test_fault_three_phase(self, config_generator):
        config = config_generator.generate_config(
            "帮我跑个短路计算，IEEE39系统，三相短路"
        )
        assert config["fault"]["type"] == "three_phase"

    def test_fault_single_phase(self, config_generator):
        config = config_generator.generate_config(
            "对IEEE3做EMT故障研究，Bus1单相接地"
        )
        assert config["fault"]["type"] == "single_phase"

    # ---- Fault Location Extraction ----
    def test_fault_location_bus(self, config_generator):
        config = config_generator.generate_config(
            "计算Bus5故障的临界切除时间CCT"
        )
        assert config["fault_scenarios"][0]["location"] == "Bus5"

    # ---- Renewable Type Extraction ----
    def test_renewable_wind(self, config_generator):
        config = config_generator.generate_config(
            "分析风电接入点的SCR和LVRT合规性"
        )
        assert config["renewable"]["type"] == "wind"

    def test_renewable_pv(self, config_generator):
        config = config_generator.generate_config(
            "分析光伏接入的SCR和LVRT合规性"
        )
        assert config["renewable"]["type"] == "pv"

    # ---- Combined Parameter Extraction ----
    def test_combined_power_flow_params(self, config_generator):
        """Test multiple parameters in one prompt."""
        config = config_generator.generate_config(
            "IEEE39潮流计算，收敛精度1e-8，最大迭代200次，用快速分解法"
        )
        assert config["algorithm"]["tolerance"] == 1e-8
        assert config["algorithm"]["max_iterations"] == 200
        assert config["algorithm"]["type"] == "fast_decoupled"
        assert config["model"]["rid"] == "model/chenying/IEEE39"
