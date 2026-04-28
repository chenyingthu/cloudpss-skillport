#!/usr/bin/env python3
"""
Playwright MCP Batch Testing Script for CloudPSS Skills
Automates testing of all 50 skills via web UI
"""

import subprocess
import json
import time
from datetime import datetime

# All 50 skills to test
SKILLS_TO_TEST = [
    # 仿真执行 (4个)
    ("power_flow", "潮流"),
    ("emt_simulation", "EMT仿真"),
    ("emt_fault_study", "EMT故障研究"),
    ("short_circuit", "短路计算"),

    # N-1/N-2安全 (5个)
    ("n1_security", "N-1安全"),
    ("n2_security", "N-2安全"),
    ("emt_n1_screening", "EMT N-1筛查"),
    ("contingency_analysis", "预想事故分析"),
    ("maintenance_security", "检修安全"),

    # 批量与扫描 (7个)
    ("batch_powerflow", "批量潮流"),
    ("param_scan", "参数扫描"),
    ("fault_clearing_scan", "故障清除扫描"),
    ("fault_severity_scan", "故障严重度扫描"),
    ("batch_task_manager", "批量任务管理"),
    ("config_batch_runner", "配置批量运行"),
    ("orthogonal_sensitivity", "正交敏感性"),

    # 稳定性分析 (7个)
    ("voltage_stability", "电压稳定"),
    ("transient_stability", "暂态稳定"),
    ("transient_stability_margin", "暂态稳定裕度"),
    ("small_signal_stability", "小信号稳定"),
    ("frequency_response", "频率响应"),
    ("vsi_weak_bus", "VSI弱母线"),
    ("dudv_curve", "DUDV曲线"),

    # 结果处理 (7个)
    ("result_compare", "结果对比"),
    ("visualize", "可视化"),
    ("waveform_export", "波形导出"),
    ("hdf5_export", "HDF5导出"),
    ("disturbance_severity", "扰动严重度"),
    ("compare_visualization", "对比可视化"),
    ("comtrade_export", "COMTRADE导出"),

    # 电能质量 (3个)
    ("harmonic_analysis", "谐波分析"),
    ("power_quality_analysis", "电能质量"),
    ("reactive_compensation_design", "无功补偿设计"),

    # 新能源 (1个)
    ("renewable_integration", "新能源接入"),

    # 模型与拓扑 (10个)
    ("topology_check", "拓扑检查"),
    ("parameter_sensitivity", "参数灵敏度"),
    ("auto_channel_setup", "自动量测配置"),
    ("auto_loop_breaker", "自动解环"),
    ("model_parameter_extractor", "参数提取"),
    ("model_builder", "模型构建"),
    ("model_validator", "模型验证"),
    ("component_catalog", "元件目录"),
    ("thevenin_equivalent", "戴维南等值"),
    ("model_hub", "算例中心"),

    # 分析报告 (3个)
    ("loss_analysis", "网损分析"),
    ("protection_coordination", "保护整定"),
    ("report_generator", "报告生成"),

    # 流程编排 (1个)
    ("study_pipeline", "流程编排"),
]

# Skills that need longer timeout (EMT simulations)
LONG_TIMEOUT_SKILLS = [
    "emt_simulation", "emt_fault_study", "emt_n1_screening",
    "transient_stability", "frequency_response"
]

# Skills that may timeout due to complexity
KNOWN_SLOW_SKILLS = [
    "n1_security", "n2_security", "maintenance_security",
    "reactive_compensation_design", "study_pipeline"
]


def run_skill_via_playwright(skill_name, skill_desc):
    """Run a single skill test via Playwright MCP"""
    print(f"\n{'='*60}")
    print(f"Testing: {skill_name} ({skill_desc})")
    print(f"{'='*60}")

    # Determine timeout
    if skill_name in LONG_TIMEOUT_SKILLS:
        timeout = 60  # 60 seconds for EMT
    elif skill_name in KNOWN_SLOW_SKILLS:
        timeout = 120  # 120 seconds for slow skills
    else:
        timeout = 30  # 30 seconds for normal skills

    # Create test script for this skill
    test_script = f'''
import asyncio
from playwright.async_api import async_playwright

async def test_skill():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to the app
        await page.goto("http://localhost:8502")
        await page.wait_for_timeout(2000)

        # Click EMT button for EMT skills, otherwise click 潮流
        if "emt" in "{skill_name}":
            await page.click("button:has-text('EMT')", timeout=5000)
        else:
            # Click dropdown and select skill
            await page.click("[data-testid=\"stSelectbox\"]", timeout=5000)
            await page.wait_for_timeout(500)
            # Type skill name to search
            await page.keyboard.type("{skill_name}")
            await page.wait_for_timeout(500)
            await page.keyboard.press("Enter")

        await page.wait_for_timeout(2000)

        # Click 加载示例
        load_btn = await page.wait_for_selector("button:has-text('加载示例')", timeout=5000)
        await load_btn.click()
        await page.wait_for_timeout(2000)

        # Check for validation passed
        validation = await page.content()
        if "配置验证通过" in validation:
            print("✅ Config validation passed")
        else:
            print("❌ Config validation failed")
            await browser.close()
            return False

        # Click 确认执行
        exec_btn = await page.wait_for_selector("button:has-text('确认执行')", timeout=5000)
        await exec_btn.click()

        # Wait for completion (longer timeout)
        print(f"Waiting up to {timeout}s for execution...")

        # Wait for status to change from pending to complete
        for i in range(timeout):
            await page.wait_for_timeout(1000)
            content = await page.content()

            if "完成" in content or "✅" in content:
                if "执行指标" in content or "仿真结果" in content or "output" in content:
                    print(f"✅ Execution completed in {{i+1}}s")
                    await browser.close()
                    return True

            if "失败" in content or "❌" in content:
                print("❌ Execution failed")
                await browser.close()
                return False

        print("⏱️ Timeout waiting for completion")
        await browser.close()
        return False

result = asyncio.run(test_skill())
print(f"Result: {{result}}")
'''

    # Save and run the script
    script_file = f"/tmp/test_{skill_name}.py"
    with open(script_file, "w") as f:
        f.write(test_script)

    try:
        result = subprocess.run(
            ["python", script_file],
            capture_output=True,
            text=True,
            timeout=timeout + 10
        )
        output = result.stdout + result.stderr

        if "✅ Execution completed" in output:
            return {"status": "PASS", "output": output}
        elif "⏱️ Timeout" in output:
            return {"status": "TIMEOUT", "output": output}
        else:
            return {"status": "FAIL", "output": output}

    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "output": "Test script timed out"}
    except Exception as e:
        return {"status": "ERROR", "output": str(e)}


def main():
    """Run all skill tests"""
    print("="*80)
    print("CloudPSS Skills - Playwright Batch Test")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []
    passed = 0
    failed = 0
    timeout = 0

    for skill_name, skill_desc in SKILLS_TO_TEST:
        result = run_skill_via_playwright(skill_name, skill_desc)
        results.append({
            "skill": skill_name,
            "desc": skill_desc,
            "status": result["status"],
            "output": result["output"]
        })

        if result["status"] == "PASS":
            passed += 1
        elif result["status"] == "TIMEOUT":
            timeout += 1
        else:
            failed += 1

        # Small delay between tests
        time.sleep(1)

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total: {len(SKILLS_TO_TEST)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Timeout: {timeout} ⏱️")
    print(f"Success Rate: {passed/len(SKILLS_TO_TEST)*100:.1f}%")

    # Save results
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {results_file}")

    return results


if __name__ == "__main__":
    main()
