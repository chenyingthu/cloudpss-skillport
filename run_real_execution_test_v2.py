#!/usr/bin/env python3
"""
最终版测试脚本 - 解决全部7个技能
"""
import sys
import os
import json
import time
from pathlib import Path
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("CLOUDPSS_TOKEN_FILE", str(PROJECT_ROOT / ".cloudpss_token"))

from web.core import skill_catalog

def get_skill(name):
    return skill_catalog.get_skill(name)

def run_skill_test(skill_name, config):
    """Run skill with proper error handling"""
    print(f"\n{'='*60}")
    print(f"🧪 测试技能: {skill_name}")
    print(f"{'='*60}")
    
    try:
        skill = get_skill(skill_name)
        if not skill:
            return {"status": "failed", "error": "Skill not found"}
        
        # Validate config
        validation = skill.validate(config)
        if not getattr(validation, "valid", True):
            errors = getattr(validation, "errors", ["Unknown"])
            return {"status": "validation_failed", "error": str(errors)}
        
        print(f" ✅ 配置验证通过")
        print(f" 🚀 开始真实执行...")
        
        start_time = time.time()
        result = skill.run(config)
        elapsed = time.time() - start_time
        
        print(f" ⏱️ 执行耗时: {elapsed:.1f}s")
        
        success = getattr(result, "success", False) or "SUCCESS" in str(getattr(result, "status", ""))
        
        return {
            "status": "success" if success else "failed",
            "error": getattr(result, "error", None),
            "time": elapsed,
            "data": getattr(result, "data", {})
        }
        
    except Exception as e:
        print(f" ❌ 执行异常: {type(e).__name__}: {e}")
        traceback.print_exc()
        return {"status": "exception", "error": str(e)}

# 最终配置：测试7个技能
TESTS = [
    {
        "name": "model_validator",
        "config": {
            "skill": "model_validator",
            "models": [{"rid": "model/chenying/IEEE39"}],
            "validation": {"phases": ["topology"], "timeout": 300},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/model_validator_test.json", "timestamp": True}
        }
    },
    {
        "name": "transient_stability_margin",
        "config": {
            "skill": "transient_stability_margin",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"fault_bus": "Bus7", "clearing_time_range": [0.05, 0.2], "steps": 3},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/transient_margin_test.json", "timestamp": True}
        }
    },
    {
        "name": "vsi_weak_bus",
        "config": {
            "skill": "vsi_weak_bus",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"threshold": 3.0, "voltage_check": True},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/vsi_test.json", "timestamp": True}
        }
    },
    {
        "name": "voltage_stability",
        "config": {
            "skill": "voltage_stability",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "scan": {"load_scaling": [1.0, 1.1, 1.2], "scale_generation": True},
            "monitoring": {"buses": [], "collapse_threshold": 0.8},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/voltage_stability_test.json", "timestamp": True}
        }
    },
    {
        "name": "power_quality_analysis",
        "config": {
            "skill": "power_quality_analysis",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"metrics": ["thd"], "buses": ["Bus1"]},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/power_quality_test.json", "timestamp": True}
        }
    },
    {
        "name": "transient_stability",
        "config": {
            "skill": "transient_stability",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "fault": {"clearing_time": 0.1, "location": "Bus7"},
            "simulation": {"duration": 3.0, "step_size": 0.01},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/transient_stability_test.json", "timestamp": True}
        }
    },
    {
        "name": "n1_security",
        "config": {
            "skill": "n1_security",
            "model": {"rid": "model/chenying/IEEE39", "source": "cloud"},
            "analysis": {"max_contingencies": 5, "check_voltage": True, "check_thermal": True},
            "auth": {"base_url": "http://166.111.60.76:50001", "token_file": str(PROJECT_ROOT / ".cloudpss_token_internal")},
            "output": {"format": "json", "path": "./results/n1_security_test.json", "timestamp": True}
        }
    },
]

def main():
    print("="*60)
    print("🔬 最终版真实执行测试 - 7个技能")
    print("="*60)
    
    Path("./results").mkdir(exist_ok=True)
    
    results = {}
    passed = 0
    
    for test in TESTS:
        result = run_skill_test(test["name"], test["config"])
        results[test["name"]] = result
        if result["status"] == "success":
            passed += 1
        time.sleep(1)
    
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    print(f"✅ 成功: {passed}/{len(TESTS)}")
    print(f"❌ 失败: {len(TESTS) - passed}/{len(TESTS)}")
    
    for name, result in results.items():
        emoji = "✅" if result["status"] == "success" else "❌"
        if result["status"] == "success":
            print(f" {emoji} {name}: 成功 ({result['time']:.1f}s)")
        else:
            error = result.get("error", "Unknown")
            print(f" {emoji} {name}: {str(error)[:60]}...")
    
    return results

if __name__ == "__main__":
    main()
