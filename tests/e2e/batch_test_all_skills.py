"""
批量测试所有50个技能 - 快速收集问题并生成PR要求

使用方法:
    python tests/e2e/batch_test_all_skills.py

输出:
    - tests/e2e/reports/full_test_report.json
    - tests/e2e/reports/full_test_report.html
    - tests/e2e/PR_REQUIREMENTS.md
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright

# 所有技能列表
ALL_SKILLS = [
    # 仿真执行 (4)
    "power_flow", "emt_simulation", "emt_fault_study", "short_circuit",
    # N-1/N-2安全 (5)
    "n1_security", "n2_security", "emt_n1_screening", "contingency_analysis", "maintenance_security",
    # 批量与扫描 (7)
    "batch_powerflow", "param_scan", "fault_clearing_scan", "fault_severity_scan",
    "batch_task_manager", "config_batch_runner", "orthogonal_sensitivity",
    # 稳定性分析 (7)
    "voltage_stability", "transient_stability", "transient_stability_margin",
    "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve",
    # 结果处理 (7)
    "result_compare", "visualize", "waveform_export", "hdf5_export",
    "disturbance_severity", "compare_visualization", "comtrade_export",
    # 电能质量 (3)
    "harmonic_analysis", "power_quality_analysis", "reactive_compensation_design",
    # 新能源 (1)
    "renewable_integration",
    # 模型与拓扑 (10)
    "topology_check", "parameter_sensitivity", "auto_channel_setup", "auto_loop_breaker",
    "model_parameter_extractor", "model_builder", "model_validator", "component_catalog",
    "thevenin_equivalent", "model_hub",
    # 分析报告 (3)
    "loss_analysis", "protection_coordination", "report_generator",
    # 流程编排 (1)
    "study_pipeline",
]

SKILL_CATEGORIES = {
    "power_flow": "仿真执行",
    "emt_simulation": "仿真执行",
    "emt_fault_study": "仿真执行",
    "short_circuit": "仿真执行",
    "n1_security": "N-1/N-2安全",
    "n2_security": "N-1/N-2安全",
    "emt_n1_screening": "N-1/N-2安全",
    "contingency_analysis": "N-1/N-2安全",
    "maintenance_security": "N-1/N-2安全",
    "batch_powerflow": "批量与扫描",
    "param_scan": "批量与扫描",
    "fault_clearing_scan": "批量与扫描",
    "fault_severity_scan": "批量与扫描",
    "batch_task_manager": "批量与扫描",
    "config_batch_runner": "批量与扫描",
    "orthogonal_sensitivity": "批量与扫描",
    "voltage_stability": "稳定性分析",
    "transient_stability": "稳定性分析",
    "transient_stability_margin": "稳定性分析",
    "small_signal_stability": "稳定性分析",
    "frequency_response": "稳定性分析",
    "vsi_weak_bus": "稳定性分析",
    "dudv_curve": "稳定性分析",
    "result_compare": "结果处理",
    "visualize": "结果处理",
    "waveform_export": "结果处理",
    "hdf5_export": "结果处理",
    "disturbance_severity": "结果处理",
    "compare_visualization": "结果处理",
    "comtrade_export": "结果处理",
    "harmonic_analysis": "电能质量",
    "power_quality_analysis": "电能质量",
    "reactive_compensation_design": "电能质量",
    "renewable_integration": "新能源",
    "topology_check": "模型与拓扑",
    "parameter_sensitivity": "模型与拓扑",
    "auto_channel_setup": "模型与拓扑",
    "auto_loop_breaker": "模型与拓扑",
    "model_parameter_extractor": "模型与拓扑",
    "model_builder": "模型与拓扑",
    "model_validator": "模型与拓扑",
    "component_catalog": "模型与拓扑",
    "thevenin_equivalent": "模型与拓扑",
    "model_hub": "模型与拓扑",
    "loss_analysis": "分析报告",
    "protection_coordination": "分析报告",
    "report_generator": "分析报告",
    "study_pipeline": "流程编排",
}


@dataclass
class SkillTestResult:
    skill_name: str
    category: str
    status: str  # success, failed, timeout, error, navigation_failed, config_invalid
    duration: float
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # 错误分类
    fix_required: bool = False
    fix_priority: str = "low"  # critical, high, medium, low


class SkillBatchTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8702"):
        self.base_url = base_url
        self.results: List[SkillTestResult] = []
        self.browser = None
        self.page = None

    async def setup(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page(viewport={"width": 1920, "height": 1080})
        await self.page.goto(self.base_url)
        await asyncio.sleep(2)

    async def teardown(self):
        if self.browser:
            await self.browser.close()

    async def test_skill(self, skill_name: str) -> SkillTestResult:
        """测试单个技能"""
        start_time = time.time()
        category = SKILL_CATEGORIES.get(skill_name, "未知")

        try:
            # 1. 点击创建任务
            create_btn = await self.page.query_selector('button:has-text("创建任务")')
            if create_btn:
                await create_btn.click()
                await asyncio.sleep(1)

            # 2. 展开所有分类
            expanders = await self.page.query_selector_all('summary')
            for exp in expanders:
                try:
                    await exp.click()
                    await asyncio.sleep(0.3)
                except:
                    pass

            # 3. 尝试找到技能按钮
            skill_btn = None
            for btn in await self.page.query_selector_all('button'):
                text = await btn.text_content()
                if text and skill_name.replace('_', '').lower() in text.lower().replace(' ', ''):
                    skill_btn = btn
                    break

            if not skill_btn:
                # 尝试通过JavaScript点击
                clicked = await self.page.evaluate(f'''() => {{
                    const buttons = document.querySelectorAll('button');
                    for (const btn of buttons) {{
                        const text = btn.textContent.toLowerCase().replace(/[_\s]/g, '');
                        if (text.includes('{skill_name.replace('_', '').lower()}')) {{
                            btn.click();
                            return true;
                        }}
                    }}
                    return false;
                }}''')
                if not clicked:
                    return SkillTestResult(
                        skill_name=skill_name,
                        category=category,
                        status="navigation_failed",
                        duration=time.time() - start_time,
                        error_message="无法找到技能按钮",
                        error_type="UI_NAVIGATION",
                        fix_required=True,
                        fix_priority="medium"
                    )
            else:
                await skill_btn.click()
                await asyncio.sleep(2)

            # 4. 加载示例
            load_btn = await self.page.query_selector('button:has-text("加载示例")')
            if not load_btn:
                return SkillTestResult(
                    skill_name=skill_name,
                    category=category,
                    status="error",
                    duration=time.time() - start_time,
                    error_message="未找到加载示例按钮",
                    error_type="UI_MISSING_ELEMENT",
                    fix_required=True,
                    fix_priority="high"
                )

            await load_btn.click()
            await asyncio.sleep(3)

            # 5. 检查配置验证状态
            page_content = await self.page.content()

            # 检查各种错误类型
            if "list.index(x): x not in list" in page_content:
                return SkillTestResult(
                    skill_name=skill_name,
                    category=category,
                    status="config_invalid",
                    duration=time.time() - start_time,
                    error_message="前端渲染错误: list.index(x): x not in list",
                    error_type="FRONTEND_INDEX_ERROR",
                    fix_required=True,
                    fix_priority="critical"
                )

            if 'Variable "$rid" got invalid value ""' in page_content:
                return SkillTestResult(
                    skill_name=skill_name,
                    category=category,
                    status="config_invalid",
                    duration=time.time() - start_time,
                    error_message="后端错误: model.rid 为空字符串",
                    error_type="BACKEND_EMPTY_RID",
                    fix_required=True,
                    fix_priority="critical"
                )

            if "NameError: name 'base_model' is not defined" in page_content:
                return SkillTestResult(
                    skill_name=skill_name,
                    category=category,
                    status="failed",
                    duration=time.time() - start_time,
                    error_message="后端错误: base_model 变量未定义",
                    error_type="BACKEND_VARIABLE_ERROR",
                    fix_required=True,
                    fix_priority="critical"
                )

            alert = await self.page.query_selector('[role="alert"], [data-testid="stAlert"]')
            if alert:
                alert_text = await alert.text_content()
                if "验证通过" in alert_text:
                    # 配置验证通过
                    pass
                elif "验证失败" in alert_text:
                    return SkillTestResult(
                        skill_name=skill_name,
                        category=category,
                        status="config_invalid",
                        duration=time.time() - start_time,
                        error_message=f"配置验证失败: {alert_text}",
                        error_type="CONFIG_VALIDATION",
                        fix_required=True,
                        fix_priority="high"
                    )

            # 6. 执行
            exec_btn = await self.page.query_selector('button:has-text("确认执行")')
            if not exec_btn:
                return SkillTestResult(
                    skill_name=skill_name,
                    category=category,
                    status="error",
                    duration=time.time() - start_time,
                    error_message="未找到确认执行按钮",
                    error_type="UI_MISSING_ELEMENT",
                    fix_required=True,
                    fix_priority="medium"
                )

            await exec_btn.click()

            # 7. 等待结果
            max_wait = 120 if skill_name in ["emt_simulation", "emt_n1_screening", "n1_security", "n2_security"] else 60
            elapsed = 0
            check_interval = 2

            while elapsed < max_wait:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

                content = await self.page.content()

                # 检查成功
                if "仿真结果" in content or "输出文件" in content or "✅ 完成" in content:
                    return SkillTestResult(
                        skill_name=skill_name,
                        category=category,
                        status="success",
                        duration=time.time() - start_time,
                        error_message=None,
                        error_type=None,
                        fix_required=False,
                        fix_priority="low"
                    )

                # 检查失败
                if "执行失败" in content or "❌ 失败" in content:
                    error_match = await self.page.evaluate('''() => {
                        const alert = document.querySelector('[role="alert"]');
                        return alert ? alert.textContent : '';
                    }''')
                    return SkillTestResult(
                        skill_name=skill_name,
                        category=category,
                        status="failed",
                        duration=time.time() - start_time,
                        error_message=f"执行失败: {error_match}",
                        error_type="EXECUTION_ERROR",
                        fix_required=True,
                        fix_priority="high"
                    )

            # 超时
            return SkillTestResult(
                skill_name=skill_name,
                category=category,
                status="timeout",
                duration=time.time() - start_time,
                error_message=f"执行超时 (>{max_wait}s)",
                error_type="TIMEOUT",
                fix_required=True,
                fix_priority="medium"
            )

        except Exception as e:
            return SkillTestResult(
                skill_name=skill_name,
                category=category,
                status="error",
                duration=time.time() - start_time,
                error_message=str(e),
                error_type="EXCEPTION",
                fix_required=True,
                fix_priority="high"
            )

    async def run_all_tests(self):
        print(f"开始测试 {len(ALL_SKILLS)} 个技能...\n")

        await self.setup()

        for i, skill in enumerate(ALL_SKILLS, 1):
            print(f"[{i}/{len(ALL_SKILLS)}] 测试 {skill}...", end=" ")
            result = await self.test_skill(skill)
            self.results.append(result)

            status_icon = {
                "success": "✅",
                "failed": "❌",
                "timeout": "⏱️",
                "error": "💥",
                "navigation_failed": "🧭",
                "config_invalid": "⚙️"
            }.get(result.status, "❓")

            print(f"{status_icon} {result.status.upper()} - {result.duration:.1f}s")
            if result.error_message:
                print(f"    错误: {result.error_message[:100]}...")

            # 重置到首页
            await self.page.goto(self.base_url)
            await asyncio.sleep(1)

        await self.teardown()

    def generate_reports(self):
        """生成测试报告"""
        reports_dir = Path("tests/e2e/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 统计
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == "success")
        failed = sum(1 for r in self.results if r.status == "failed")
        timeout = sum(1 for r in self.results if r.status == "timeout")
        config_invalid = sum(1 for r in self.results if r.status == "config_invalid")
        navigation_failed = sum(1 for r in self.results if r.status == "navigation_failed")
        error = sum(1 for r in self.results if r.status == "error")

        critical_fixes = sum(1 for r in self.results if r.fix_priority == "critical" and r.fix_required)
        high_fixes = sum(1 for r in self.results if r.fix_priority == "high" and r.fix_required)

        # JSON报告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "success": success,
                "failed": failed,
                "timeout": timeout,
                "config_invalid": config_invalid,
                "navigation_failed": navigation_failed,
                "error": error,
                "success_rate": round(success / total * 100, 1),
                "critical_fixes": critical_fixes,
                "high_fixes": high_fixes,
            },
            "results": [asdict(r) for r in self.results]
        }

        json_path = reports_dir / "full_test_report.json"
        json_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON报告已生成: {json_path}")

        # HTML报告
        self._generate_html_report(report_data, reports_dir / "full_test_report.html")

        # PR要求文档
        self._generate_pr_requirements(report_data)

        return report_data

    def _generate_html_report(self, data: Dict, path: Path):
        """生成HTML报告"""
        summary = data["summary"]
        results = data["results"]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CloudPSS 50技能全面测试报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-box {{ padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-box.success {{ background: #e8f5e9; color: #2e7d32; }}
        .stat-box.failed {{ background: #ffebee; color: #c62828; }}
        .stat-box.timeout {{ background: #fff3e0; color: #ef6c00; }}
        .stat-box.total {{ background: #e3f2fd; color: #1565c0; }}
        .stat-number {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: 600; position: sticky; top: 0; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-success {{ color: #4CAF50; font-weight: 600; }}
        .status-failed {{ color: #f44336; font-weight: 600; }}
        .status-timeout {{ color: #ff9800; font-weight: 600; }}
        .status-config_invalid {{ color: #9c27b0; font-weight: 600; }}
        .priority-critical {{ background: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 4px; font-weight: bold; }}
        .priority-high {{ background: #fff3e0; color: #ef6c00; padding: 2px 8px; border-radius: 4px; }}
        .priority-medium {{ background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; }}
        .error-msg {{ color: #666; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .category-tag {{ background: #f0f0f0; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ CloudPSS 50技能全面测试报告</h1>
        <p>测试时间: {data['timestamp']}</p>

        <div class="summary">
            <div class="stat-box total">
                <div class="stat-number">{summary['total']}</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat-box success">
                <div class="stat-number">{summary['success']} ({summary['success_rate']}%)</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat-box failed">
                <div class="stat-number">{summary['failed'] + summary['config_invalid'] + summary['navigation_failed'] + summary['error']}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-box timeout">
                <div class="stat-number">{summary['timeout']}</div>
                <div class="stat-label">超时</div>
            </div>
        </div>

        <h2>📊 错误分类统计</h2>
        <table>
            <tr><th>错误类型</th><th>数量</th><th>优先级</th></tr>
            <tr><td>配置验证失败</td><td>{summary['config_invalid']}</td><td><span class="priority-high">High</span></td></tr>
            <tr><td>执行失败</td><td>{summary['failed']}</td><td><span class="priority-high">High</span></td></tr>
            <tr><td>导航失败</td><td>{summary['navigation_failed']}</td><td><span class="priority-medium">Medium</span></td></tr>
            <tr><td>执行超时</td><td>{summary['timeout']}</td><td><span class="priority-medium">Medium</span></td></tr>
            <tr><td>其他错误</td><td>{summary['error']}</td><td><span class="priority-high">High</span></td></tr>
        </table>

        <h2>🔧 需要修复的问题</h2>
        <p><strong>Critical:</strong> {summary['critical_fixes']} 个 | <strong>High:</strong> {summary['high_fixes']} 个</p>

        <h2>📋 详细结果</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>技能名称</th>
                    <th>类别</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>错误类型</th>
                    <th>优先级</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, r in enumerate(results, 1):
            priority_class = f"priority-{r['fix_priority']}"
            status_class = f"status-{r['status']}"
            error_msg = (r['error_message'] or "-")[:80]
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td><code>{r['skill_name']}</code></td>
                    <td><span class="category-tag">{r['category']}</span></td>
                    <td class="{status_class}">{r['status'].upper()}</td>
                    <td>{r['duration']:.1f}s</td>
                    <td>{r['error_type'] or "-"}</td>
                    <td><span class="{priority_class}">{r['fix_priority'].upper()}</span></td>
                    <td class="error-msg" title="{r['error_message'] or ''}">{error_msg}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        path.write_text(html, encoding="utf-8")
        print(f"HTML报告已生成: {path}")

    def _generate_pr_requirements(self, data: Dict):
        """生成PR要求文档"""
        results = data["results"]

        # 按错误类型分组
        error_groups: Dict[str, List[SkillTestResult]] = {}
        for r in self.results:
            if r.fix_required:
                error_type = r.error_type or "UNKNOWN"
                if error_type not in error_groups:
                    error_groups[error_type] = []
                error_groups[error_type].append(r)

        md = """# CloudPSS 技能修复 - PR 要求文档

## 📊 测试概况

"""
        summary = data["summary"]
        md += f"""
- **总测试数:** {summary['total']} 个技能
- **通过率:** {summary['success_rate']}%
- **需要修复:** {summary['critical_fixes'] + summary['high_fixes']} 个问题
- **测试时间:** {data['timestamp']}

## 🎯 修复优先级

| 优先级 | 数量 | 说明 |
|--------|------|------|
| 🔴 Critical | {summary['critical_fixes']} | 阻塞性问题，必须立即修复 |
| 🟠 High | {summary['high_fixes']} | 重要功能问题，尽快修复 |
| 🟡 Medium | {sum(1 for r in self.results if r.fix_priority == 'medium' and r.fix_required)} | 一般问题，计划修复 |

---

## 🔴 Critical 优先级修复

"""

        # Critical fixes
        critical_results = [r for r in self.results if r.fix_priority == "critical" and r.fix_required]
        if critical_results:
            for r in critical_results:
                md += f"""### {r.skill_name}
- **类别:** {r.category}
- **错误类型:** {r.error_type}
- **错误信息:** {r.error_message}
- **修复建议:** 见下方详细方案

"""
        else:
            md += "暂无 Critical 优先级问题\n\n"

        md += """---

## 🟠 High 优先级修复

"""

        # High fixes
        high_results = [r for r in self.results if r.fix_priority == "high" and r.fix_required]
        if high_results:
            for r in high_results:
                md += f"""### {r.skill_name}
- **类别:** {r.category}
- **错误类型:** {r.error_type}
- **错误信息:** {r.error_message}

"""
        else:
            md += "暂无 High 优先级问题\n\n"

        md += """---

## 📋 按错误类型分类

"""

        for error_type, items in sorted(error_groups.items()):
            md += f"""### {error_type}
**影响技能:** {len(items)} 个

| 技能名称 | 类别 | 优先级 |
|----------|------|--------|
"""
            for r in items:
                md += f"| {r.skill_name} | {r.category} | {r.fix_priority.upper()} |\n"
            md += "\n"

        md += """---

## 🔧 详细修复方案

### 1. FRONTEND_INDEX_ERROR (前端渲染错误)

**问题:** `list.index(x): x not in list`

**影响技能:**
"""
        frontend_errors = error_groups.get("FRONTEND_INDEX_ERROR", [])
        for r in frontend_errors:
            md += f"- {r.skill_name}\n"

        md += """
**修复文件:** `web/components/task_create.py`

**修复代码:**
```python
# 在所有使用 list.index() 的地方添加 try-except
format_options = ["json", "csv", "yaml"]
current_format = output.get("format", "json")
try:
    format_index = format_options.index(current_format)
except ValueError:
    format_index = 0  # 使用默认值
```

---

### 2. BACKEND_EMPTY_RID (后端空RID)

**问题:** `Variable "$rid" got invalid value ""`

**影响技能:**
"""
        rid_errors = error_groups.get("BACKEND_EMPTY_RID", [])
        for r in rid_errors:
            md += f"- {r.skill_name}\n"

        md += """
**修复文件:** `web/components/task_create.py`

**修复代码:**
```python
def _normalize_model_rid(config: dict, user: str = None) -> dict:
    model = config.get("model", {})
    rid = model.get("rid", "")

    # 如果 rid 为空，设置默认模型
    if not rid:
        model["rid"] = f"model/{user}/IEEE39"
        model["source"] = "cloud"
        config["model"] = model
```

---

### 3. BACKEND_VARIABLE_ERROR (后端变量未定义)

**问题:** `NameError: name 'base_model' is not defined`

**影响技能:**
"""
        var_errors = error_groups.get("BACKEND_VARIABLE_ERROR", [])
        for r in var_errors:
            md += f"- {r.skill_name}\n"

        md += """
**修复文件:** `cloudpss-toolkit/cloudpss_skills/builtin/contingency_analysis.py`

**修复代码:**
```python
# 在 _evaluate_contingency 方法签名中添加 base_model 参数
def _evaluate_contingency(
    self,
    ...
    config: Optional[Dict] = None,
    base_model = None,  # 新增参数
) -> Dict:

# 在调用处传递 base_model
result = self._evaluate_contingency(
    ...
    config,
    base_model,  # 新增
)
```

---

### 4. CONFIG_VALIDATION (配置验证失败)

**问题:** 示例配置不符合 schema 要求

**影响技能:**
"""
        config_errors = error_groups.get("CONFIG_VALIDATION", [])
        for r in config_errors:
            md += f"- {r.skill_name}\n"

        md += """
**修复文件:** `scripts/smart_config.py`

**修复方案:** 为每个技能生成完整的示例配置，包括所有必需字段。

---

## 🚀 PR 提交要求

### PR 标题格式
```
Fix: [错误类型] - 修复 [技能名称] 的 [问题描述]

示例:
Fix: FRONTEND_INDEX_ERROR - 修复 visualize 和 report_generator 的前端渲染错误
```

### PR 描述模板
```markdown
## 问题描述
[描述问题的现象和影响]

## 修复内容
- [ ] 修复文件1: 具体修改
- [ ] 修复文件2: 具体修改

## 测试验证
- [ ] 本地测试通过
- [ ] Playwright 自动化测试通过

## 影响范围
[列出受影响的技能]

## 破坏性变更
[如果有，列出破坏性变更]
```

### 必须包含的文件
1. **修复代码** - 实际的代码修改
2. **测试用例** - 证明修复有效的测试
3. **文档更新** - 如果有接口变更

---

## 📊 修复后预期结果

修复所有问题后，预期:
- 通过率: > 90%
- Critical 问题: 0
- High 优先级问题: 0

---

*文档生成时间: """ + datetime.now().isoformat() + """*
"""

        pr_path = Path("tests/e2e/PR_REQUIREMENTS.md")
        pr_path.write_text(md, encoding="utf-8")
        print(f"PR要求文档已生成: {pr_path}")


async def main():
    tester = SkillBatchTester()
    await tester.run_all_tests()
    report_data = tester.generate_reports()

    # 打印摘要
    print("\n" + "="*60)
    print("测试摘要")
    print("="*60)
    summary = report_data["summary"]
    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['success']} ({summary['success_rate']}%)")
    print(f"需要修复: {summary['critical_fixes'] + summary['high_fixes']} 个问题")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
