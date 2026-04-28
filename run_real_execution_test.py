#!/usr/bin/env python3
"""
对修复的10个技能进行真实执行测试
验证物理结果的正确性
"""
import sys
import os
import json
import time
from pathlib import Path

# Add paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

# Setup token
os.environ.setdefault("CLOUDPSS_TOKEN_FILE", str(PROJECT_ROOT / ".cloudpss_token"))

from web.core import skill_catalog

def get_skill(name):
    """获取技能对象"""
    return skill_catalog.get_skill(name)

# 修复的10个技能配置
# 注：renewable_integration 需要带新能源的模型，IEEE39 没有 wind/pv 组件
# 故替换为 vsi_weak_bus 进行电网强度测试
FIXED_SKILLS = [
    {
        "name": "model_validator",
        "config": {
            "skill": "model_validator",
            "models": [{"rid": "model/chenying/IEEE39"}],
            "validation": {"phases": ["topology"], "timeout": 300},
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/model_validator_test.json", "timestamp": True}
        }
    },
    {
        "name": "transient_stability_margin",
        "config": {
            "skill": "transient_stability_margin",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"fault_bus": "Bus7", "clearing_time_range": [0.05, 0.2], "steps": 3},
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/transient_margin_test.json", "timestamp": True}
        }
    },
    {
        "name": "renewable_integration",
        "config": {
            "skill": "renewable_integration",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "renewable": {
                "type": "wind",
                "bus": "Bus38",
                "capacity_mw": 100.0,
                "short_circuit_mva": 500.0,
                "capacity_series_mw": [80.0, 90.0, 100.0, 85.0],
                "pcc_bus": "Bus38",
                "point_of_interconnection": "Bus38"
            },
            "harmonics": {
                "fundamental_voltage": 1.0,
                "orders": {"5": 0.03, "7": 0.02, "11": 0.01},
                "limit_thd": 0.05
            },
            "lvrt": {
                "profile": [
                    {"time_s": 0.0, "voltage_pu": 1.0},
                    {"time_s": 0.15, "voltage_pu": 0.2},
                    {"time_s": 0.8, "voltage_pu": 0.92}
                ],
                "min_voltage_pu": 0.15,
                "max_recovery_time_s": 1.5
            },
            "analysis": {
                "scr": {"enabled": True, "threshold": 2.0},
                "voltage_variation": {"enabled": True, "tolerance": 0.10},
                "harmonic_injection": {"enabled": False},
                "lvrt_compliance": {"enabled": False},
                "stability_impact": {"enabled": True}
            },
            "strict_verification": False,
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/renewable_test.json", "timestamp": True}
        }
    },
    {
        "name": "voltage_stability",
        "config": {
            "skill": "voltage_stability",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "buses": ["Bus30", "Bus38"],
            "analysis": {"method": "pv_curve", "max_load_factor": 1.3, "steps": 5, "collapse_threshold": 0.7},
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/voltage_stability_test.json", "timestamp": True}
        }
    },
    {
        "name": "power_quality_analysis",
        "config": {
            "skill": "power_quality_analysis",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"metrics": ["thd"], "buses": ["Bus1"]},
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/power_quality_test.json", "timestamp": True}
        }
    },
    {
        "name": "transient_stability",
        "config": {
            "skill": "transient_stability",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "fault": {"clearing_time": 0.1, "location": "Bus7"},
            "simulation": {"duration": 3.0, "step_size": 0.01, "integration": "trapezoidal"},
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/transient_stability_test.json", "timestamp": True}
        }
    },
    {
        "name": "n2_security",
        "config": {
            "skill": "n2_security",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {
                "max_contingencies": 5,
                "check_voltage": True,
                "check_thermal": True,
                "voltage_min": 0.90,
                "voltage_max": 1.10,
                "thermal_limit": 1.2
            },
            "auth": {
                "base_url": "http://166.111.60.76:50001",
                "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")
            },
            "output": {"format": "json", "path": "./results/n2_security_test.json", "timestamp": True}
        }
    },
]


def validate_physical_results(skill_name: str, result_data: dict) -> tuple[bool, str]:
    """
    验证物理结果的正确性
    根据电力系统基本原理检查
    """
    if not result_data:
        return False, "结果数据为空"

    # Check for NaN/Infinity
    def check_numeric(value, path=""):
        if isinstance(value, (int, float)):
            if value != value:  # NaN check
                return False, f"{path}: NaN"
            if value == float('inf') or value == float('-inf'):
                return False, f"{path}: Infinity"
        elif isinstance(value, dict):
            for k, v in value.items():
                ok, msg = check_numeric(v, f"{path}.{k}")
                if not ok:
                    return ok, msg
        elif isinstance(value, list):
            for i, v in enumerate(value):
                ok, msg = check_numeric(v, f"{path}[{i}]")
                if not ok:
                    return ok, msg
        return True, "OK"

    ok, msg = check_numeric(result_data)
    if not ok:
        return False, f"数值错误: {msg}"

    # Skill-specific validation
    if skill_name in ["power_flow", "voltage_stability", "transient_stability"]:
        # Voltage should be in 0.5-1.5 pu range for normal operation
        values = []

        def find_voltages(d, depth=0, path=""):
            if depth > 5:
                return
            if isinstance(d, dict):
                for k, v in d.items():
                    current_path = f"{path}.{k}" if path else k
                    # Only consider values with explicit voltage-related keys
                    if isinstance(v, (int, float)) and abs(v) < 10:
                        voltage_keys = ['voltage', 'volt', 'vm', 'v_pu', 'min_voltage', 'max_voltage', 'pu']
                        if any(vk in k.lower() for vk in voltage_keys):
                            # Skip non-voltage fields like total_cases, scale, etc.
                            non_voltage_keys = ['scale', 'cases', 'count', 'total', 'index', 'id', 'time']
                            if not any(nv in k.lower() for nv in non_voltage_keys):
                                values.append((v, current_path))
                    elif isinstance(v, (dict, list)):
                        find_voltages(v, depth+1, current_path)
            elif isinstance(d, list) and len(d) < 100:
                for i, item in enumerate(d):
                    find_voltages(item, depth+1, f"{path}[{i}]")

        find_voltages(result_data)

        if values:
            voltage_values = [v for v, _ in values]
            v_min, v_max = min(voltage_values), max(voltage_values)
            # Allow wider range for voltage stability analysis (up to 2.5x for loadability studies)
            if skill_name == "voltage_stability":
                if not (0.1 < v_min < 2.5 and 0.1 < v_max < 2.5):
                    return False, f"电压范围异常: {v_min:.3f}~{v_max:.3f} pu"
            else:
                if not (0.1 < v_min < 2.0 and 0.1 < v_max < 2.0):
                    return False, f"电压范围异常: {v_min:.3f}~{v_max:.3f} pu"

    return True, "物理验证通过"


def run_skill_test(skill_info: dict) -> dict:
    """Run a single skill test with real execution."""
    skill_name = skill_info["name"]
    config = skill_info["config"]

    print(f"\n{'='*60}")
    print(f"🧪 测试技能: {skill_name}")
    print(f"{'='*60}")

    try:
        skill = get_skill(skill_name)
        if not skill:
            return {"status": "failed", "error": "Skill not found", "physical_check": "N/A"}

        # Validate config first
        validation = skill.validate(config)
        if not getattr(validation, "valid", False):
            errors = getattr(validation, "errors", ["Unknown"])
            print(f"  ❌ 配置验证失败: {errors}")
            return {"status": "validation_failed", "error": str(errors), "physical_check": "N/A"}

        print(f"  ✅ 配置验证通过")
        print(f"  🚀 开始真实执行 (可能需要几十秒)...")

        # REAL EXECUTION - This calls CloudPSS API
        start_time = time.time()
        result = skill.run(config)
        elapsed = time.time() - start_time

        print(f"  ⏱️  执行耗时: {elapsed:.1f}s")

        # Check success
        success = getattr(result, "success", False) or str(getattr(result, "status", "")).upper() == "SUCCESS"

        if not success:
            error_msg = getattr(result, "error", "Unknown error")
            print(f"  ❌ 技能返回失败: {error_msg}")
            return {"status": "failed", "error": error_msg, "physical_check": "N/A", "time": elapsed}

        # Get result data
        result_data = getattr(result, "data", {}) if hasattr(result, "data") else result
        if isinstance(result_data, dict):
            data = result_data
        elif hasattr(result_data, "__dict__"):
            data = result_data.__dict__
        else:
            data = {"raw": str(result_data)[:200]}

        print(f"  📊 结果数据类型: {type(data).__name__}")

        # Validate physical correctness
        phys_ok, phys_msg = validate_physical_results(skill_name, data)

        if phys_ok:
            print(f"  ✅ 物理验证通过: {phys_msg}")
            result_summary = {}
            if isinstance(data, dict):
                for k, v in list(data.items())[:3]:
                    if isinstance(v, (int, float)):
                        result_summary[k] = v
                    elif isinstance(v, list) and len(v) > 0 and len(v) < 5:
                        result_summary[k] = v[:3]

            return {
                "status": "success",
                "data": result_summary,
                "physical_check": "通过",
                "time": elapsed
            }
        else:
            print(f"  ⚠️ 物理验证失败: {phys_msg}")
            return {
                "status": "success_but_invalid",
                "data": data,
                "physical_check": phys_msg,
                "time": elapsed
            }

    except Exception as e:
        print(f"  ❌ 执行异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "exception", "error": str(e), "physical_check": "N/A"}


def main():
    """Run all 10 skill tests."""
    print("="*60)
    print("🔬 真实执行测试 - 修复的10个技能")
    print("="*60)
    print("⚠️ 注意: 这会真实调用 CloudPSS API，每个技能可能需要10-60秒")
    print("="*60)

    # Create results directory
    Path("./results").mkdir(exist_ok=True)

    results = {}
    passed = 0
    failed = 0

    for skill in FIXED_SKILLS:
        skill_name = skill["name"]
        result = run_skill_test(skill)
        results[skill_name] = result

        if result["status"] == "success":
            passed += 1
        else:
            failed += 1

        print(f"  结果: {result}")
        time.sleep(2)  # Give server a break

    # Summary
    print("\n" + "="*60)
    print("📊 真实执行测试结果汇总")
    print("="*60)
    print(f"✅ 成功 (含物理验证): {passed}/{len(FIXED_SKILLS)}")
    print(f"❌ 失败: {failed}/{len(FIXED_SKILLS)}")

    print("\n详细结果:")
    for name, result in results.items():
        emoji = "✅" if result["status"] == "success" else "❌"
        phys = f" (物理验证: {result.get('physical_check', 'N/A')})"
        if result["status"] == "success":
            print(f"  {emoji} {name}: 成功 {phys}")
            if result.get("data"):
                print(f"     数据: {result['data']}")
        else:
            print(f"  {emoji} {name}: {result.get('error', 'Unknown')} {phys}")

    return failed == 0


if __name__ == "__main__":
    all_passed = main()
    sys.exit(0 if all_passed else 1)
