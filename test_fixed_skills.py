#!/usr/bin/env python3
"""
测试已修复的10个技能
验证修复是否生效
"""
import sys
import time
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

from web.core import skill_catalog, task_store
from web.components.task_create import _enhance_config_for_skill

# 已修复的10个技能
FIXED_SKILLS = [
    "model_validator",
    "transient_stability_margin",
    "renewable_integration",
    "voltage_stability",
    "result_compare",
    "visualize",
    "report_generator",
    "power_quality_analysis",
    "transient_stability",
    "n2_security",
]


def test_skill_config(skill_name: str, user: str = "chenying") -> dict:
    """Test that a skill config can be enhanced and validated."""
    print(f"\n🔍 测试技能: {skill_name}")

    # Get skill
    skill = skill_catalog.get_skill(skill_name)
    if skill is None:
        print(f"  ❌ 技能未找到: {skill_name}")
        return {"status": "failed", "error": "Skill not found"}

    # Get default config
    config = skill.get_default_config()

    # Enhance config
    try:
        config = _enhance_config_for_skill(config, skill_name, user)
        print(f"  ✅ 配置增强成功")
    except Exception as e:
        print(f"  ❌ 配置增强失败: {e}")
        return {"status": "failed", "error": str(e)}

    # Validate config
    try:
        validation = skill.validate(config)
        if getattr(validation, "valid", False):
            print(f"  ✅ 配置验证通过")
            return {"status": "success", "config": config}
        else:
            errors = getattr(validation, "errors", [])
            print(f"  ⚠️ 配置验证失败: {errors}")
            return {"status": "validation_failed", "errors": errors}
    except Exception as e:
        print(f"  ❌ 验证过程出错: {e}")
        return {"status": "error", "error": str(e)}


def main():
    """Run tests for all fixed skills."""
    print("=" * 60)
    print("🧪 测试已修复的10个技能")
    print("=" * 60)

    results = {}
    success_count = 0
    fail_count = 0

    for skill_name in FIXED_SKILLS:
        result = test_skill_config(skill_name)
        results[skill_name] = result
        if result["status"] == "success":
            success_count += 1
        else:
            fail_count += 1
        time.sleep(0.1)

    # Summary
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{len(FIXED_SKILLS)}")
    print(f"❌ 失败: {fail_count}/{len(FIXED_SKILLS)}")

    if fail_count > 0:
        print("\n⚠️ 失败的技能:")
        for skill_name, result in results.items():
            if result["status"] != "success":
                print(f"  - {skill_name}: {result.get('error', result.get('errors', 'Unknown'))}")

    return success_count == len(FIXED_SKILLS)


if __name__ == "__main__":
    all_passed = main()
    sys.exit(0 if all_passed else 1)
