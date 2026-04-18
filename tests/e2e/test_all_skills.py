"""
全面技能测试脚本 - 使用 Playwright 测试所有 CloudPSS 技能

测试流程:
1. 访问技能目录
2. 选中技能
3. 加载示例
4. 检查配置
5. 确认执行
6. 等待执行完成
7. 查阅执行结果
8. 分析结果是否正确
9. 记录执行状态

使用方法:
    python tests/e2e/test_all_skills.py [--headless] [--skills skill1,skill2]

依赖:
    pip install playwright pytest
    playwright install
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

# 所有技能列表（按类别分组）
SKILL_CATEGORIES = {
    "仿真执行": ["power_flow", "emt_simulation", "emt_fault_study", "short_circuit"],
    "N-1/N-2安全": ["n1_security", "n2_security", "emt_n1_screening", "contingency_analysis", "maintenance_security"],
    "批量与扫描": ["batch_powerflow", "param_scan", "fault_clearing_scan", "fault_severity_scan",
                  "batch_task_manager", "config_batch_runner", "orthogonal_sensitivity"],
    "稳定性分析": ["voltage_stability", "transient_stability", "transient_stability_margin",
                   "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve"],
    "结果处理": ["result_compare", "visualize", "waveform_export", "hdf5_export",
                "disturbance_severity", "compare_visualization", "comtrade_export"],
    "电能质量": ["harmonic_analysis", "power_quality_analysis", "reactive_compensation_design"],
    "新能源": ["renewable_integration"],
    "模型与拓扑": ["topology_check", "parameter_sensitivity", "auto_channel_setup", "auto_loop_breaker",
                   "model_parameter_extractor", "model_builder", "model_validator", "component_catalog",
                   "thevenin_equivalent", "model_hub"],
    "分析报告": ["loss_analysis", "protection_coordination", "report_generator"],
    "流程编排": ["study_pipeline"],
}

# 所有技能列表
ALL_SKILLS = [skill for skills in SKILL_CATEGORIES.values() for skill in skills]

# 技能中文名映射
SKILL_NAMES = {
    "power_flow": "潮流计算",
    "emt_simulation": "EMT暂态仿真",
    "emt_fault_study": "EMT故障研究",
    "short_circuit": "短路电流计算",
    "n1_security": "N-1安全校核",
    "n2_security": "N-2安全分析",
    "emt_n1_screening": "EMT N-1筛查",
    "contingency_analysis": "预想事故分析",
    "maintenance_security": "检修安全校核",
    "batch_powerflow": "批量潮流计算",
    "param_scan": "参数扫描分析",
    "fault_clearing_scan": "故障清除扫描",
    "fault_severity_scan": "故障严重度扫描",
    "batch_task_manager": "批量任务管理",
    "config_batch_runner": "配置批量运行",
    "orthogonal_sensitivity": "正交敏感性分析",
    "voltage_stability": "电压稳定分析",
    "transient_stability": "暂态稳定分析",
    "transient_stability_margin": "暂态稳定裕度",
    "small_signal_stability": "小信号稳定分析",
    "frequency_response": "频率响应分析",
    "vsi_weak_bus": "VSI弱母线分析",
    "dudv_curve": "DUDV曲线生成",
    "result_compare": "结果对比分析",
    "visualize": "结果可视化",
    "waveform_export": "波形数据导出",
    "hdf5_export": "HDF5数据导出",
    "disturbance_severity": "扰动严重度分析",
    "compare_visualization": "对比可视化",
    "comtrade_export": "COMTRADE导出",
    "harmonic_analysis": "谐波分析",
    "power_quality_analysis": "电能质量分析",
    "reactive_compensation_design": "无功补偿设计",
    "renewable_integration": "新能源接入分析",
    "topology_check": "拓扑检查",
    "parameter_sensitivity": "参数灵敏度分析",
    "auto_channel_setup": "自动量测配置",
    "auto_loop_breaker": "模型自动解环",
    "model_parameter_extractor": "模型参数提取",
    "model_builder": "模型构建",
    "model_validator": "模型验证",
    "component_catalog": "元件目录",
    "thevenin_equivalent": "戴维南等值",
    "model_hub": "算例中心",
    "loss_analysis": "网损分析",
    "protection_coordination": "保护整定",
    "report_generator": "报告生成",
    "study_pipeline": "流水线",
}


@dataclass
class TestResult:
    """单个技能的测试结果"""
    skill_name: str
    skill_display_name: str
    category: str
    status: str  # "success", "failed", "timeout", "error"
    duration: float
    error_message: Optional[str] = None
    has_output_files: bool = False
    execution_time: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TestReport:
    """完整的测试报告"""
    total_tests: int
    passed: int
    failed: int
    timeout: int
    total_duration: float
    results: List[TestResult]
    start_time: str
    end_time: str
    base_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "timeout": self.timeout,
            "total_duration": self.total_duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "base_url": self.base_url,
            "results": [asdict(r) for r in self.results],
        }


class SkillTester:
    """技能测试器"""

    def __init__(self, base_url: str = "http://127.0.0.1:8702", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.results: List[TestResult] = []
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await self.context.new_page()
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state("networkidle")
        # 等待页面初始化
        await asyncio.sleep(2)

    async def teardown(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

    async def navigate_to_skill(self, skill_name: str) -> bool:
        """导航到指定技能页面"""
        try:
            # 点击"创建任务"按钮确保在创建页面
            create_btn = await self.page.query_selector('button:has-text("创建任务")')
            if create_btn:
                await create_btn.click()
                await asyncio.sleep(1)

            # 获取技能中文名
            skill_display = SKILL_NAMES.get(skill_name, skill_name)
            # 使用简短名称匹配（前2-4个字符）
            skill_short = skill_display[:2] if len(skill_display) >= 2 else skill_display

            # 首先尝试在收藏的技能中点击
            # 收藏区的按钮直接显示简短名称
            fav_buttons = await self.page.query_selector_all('button')
            for btn in fav_buttons:
                text = await btn.text_content()
                if text and skill_short in text:
                    # 检查是否在收藏区域
                    parent = await btn.evaluate('''el => {
                        const container = el.closest('div');
                        if (!container) return '';
                        const prev = container.previousElementSibling;
                        return prev ? prev.textContent : '';
                    }''')
                    if parent and "收藏" in parent:
                        await btn.click()
                        await asyncio.sleep(2)
                        return True

            # 如果没有在收藏中，展开技能目录查找
            # 展开所有分类
            expand_buttons = await self.page.query_selector_all('summary, [data-testid="stExpander"]')
            for exp in expand_buttons:
                try:
                    await exp.click()
                    await asyncio.sleep(0.3)
                except:
                    pass

            # 在技能目录中查找按钮
            all_buttons = await self.page.query_selector_all('button')
            for btn in all_buttons:
                text = await btn.text_content()
                if text and skill_short in text:
                    # 检查是否在技能目录区域
                    parent = await btn.evaluate('''el => {
                        const container = el.closest('div');
                        if (!container) return '';
                        const prev = container.previousElementSibling;
                        return prev ? prev.textContent : '';
                    }''')
                    if parent and "技能目录" in parent:
                        await btn.click()
                        await asyncio.sleep(2)
                        return True

            # 最后尝试：直接通过JavaScript点击（兜底方案）
            clicked = await self.page.evaluate(f'''() => {{
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {{
                    if (btn.textContent.includes('{skill_short}')) {{
                        btn.click();
                        return true;
                    }}
                }}
                return false;
            }}''')

            if clicked:
                await asyncio.sleep(2)
                return True

            return False

        except Exception as e:
            print(f"导航到技能 {skill_name} 失败: {e}")
            return False

    async def load_example_and_run(self, skill_name: str) -> TestResult:
        """加载示例并执行技能"""
        start_time = time.time()
        category = self._get_category(skill_name)

        try:
            # 1. 导航到技能
            nav_success = await self.navigate_to_skill(skill_name)
            if not nav_success:
                return TestResult(
                    skill_name=skill_name,
                    skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                    category=category,
                    status="failed",
                    duration=time.time() - start_time,
                    error_message="无法导航到技能页面"
                )

            # 2. 点击加载示例
            load_btn = await self.page.wait_for_selector('button:has-text("加载示例")', timeout=5000)
            await load_btn.click()
            await asyncio.sleep(2)

            # 3. 检查配置验证状态
            alert_text = await self.page.evaluate('''() => {
                const alert = document.querySelector('[data-testid="stAlert"], [role="alert"]');
                return alert ? alert.textContent : '';
            }''')

            if "验证通过" not in alert_text:
                return TestResult(
                    skill_name=skill_name,
                    skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                    category=category,
                    status="failed",
                    duration=time.time() - start_time,
                    error_message=f"配置验证未通过: {alert_text}"
                )

            # 4. 点击确认执行
            exec_btn = await self.page.wait_for_selector('button:has-text("确认执行")', timeout=5000)
            await exec_btn.click()

            # 5. 等待执行完成
            # 根据技能类型设置不同的超时时间
            very_long_skills = ["n1_security", "n2_security", "contingency_analysis", "study_pipeline"]  # 需要300s
            long_running_skills = ["emt_simulation", "emt_n1_screening", "emt_fault_study",
                                   "transient_stability", "transient_stability_margin", "voltage_stability",
                                   "short_circuit", "fault_clearing_scan",
                                   "fault_severity_scan", "power_quality_analysis"]

            if skill_name in very_long_skills:
                max_wait = 300
            elif skill_name in long_running_skills:
                max_wait = 180
            else:
                max_wait = 90
            elapsed = 0
            check_interval = 2
            completed = False

            while elapsed < max_wait:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

                # 获取当前页面标题
                page_title = await self.page.title()
                heading = await self.page.query_selector('h1, h2, h3')
                heading_text = await heading.text_content() if heading else ""

                # 检查是否跳转到结果页面（通过检查最近任务列表中的任务名）
                # 或者检查页面是否包含"仿真结果"或"输出文件"
                page_content = await self.page.content()

                # 成功标志：页面包含这些关键词
                success_indicators = [
                    "仿真结果" in page_content,
                    "输出文件" in page_content,
                    "执行日志" in page_content,
                    "📋 示例:" in page_content and skill_name.replace('_', '') in heading_text.lower().replace('_', ''),
                ]

                if any(success_indicators):
                    completed = True
                    break

                # 检查失败状态
                if "执行失败" in page_content or "❌ 失败" in page_content:
                    error_match = await self.page.evaluate('''() => {
                        const alert = document.querySelector('[role="alert"]');
                        return alert ? alert.textContent : '';
                    }''')
                    return TestResult(
                        skill_name=skill_name,
                        skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                        category=category,
                        status="failed",
                        duration=time.time() - start_time,
                        error_message=f"执行失败: {error_match}"
                    )

                # 检查是否还在创建页面（说明执行按钮没生效）
                if "创建仿真任务" in heading_text and elapsed > 10:
                    # 尝试再次点击执行
                    exec_btn = await self.page.query_selector('button:has-text("确认执行")')
                    if exec_btn:
                        await exec_btn.click()

            if not completed:
                return TestResult(
                    skill_name=skill_name,
                    skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                    category=category,
                    status="timeout",
                    duration=time.time() - start_time,
                    error_message=f"执行超时 (>{max_wait}s)"
                )

            # 6. 分析结果
            await asyncio.sleep(2)

            # 检查是否有成功标记
            page_content = await self.page.content()
            has_success = any([
                "✅" in page_content,
                "完成" in page_content,
                "仿真结果" in page_content,
                "输出文件" in page_content
            ])

            # 检查输出文件
            output_files = await self.page.query_selector_all('text=results/')
            has_output = len(output_files) > 0

            # 获取执行耗时
            exec_time_el = await self.page.query_selector('text=/耗时|执行时间/')
            exec_time = await exec_time_el.text_content() if exec_time_el else None

            if has_success:
                return TestResult(
                    skill_name=skill_name,
                    skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                    category=category,
                    status="success",
                    duration=time.time() - start_time,
                    has_output_files=has_output,
                    execution_time=exec_time
                )
            else:
                return TestResult(
                    skill_name=skill_name,
                    skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                    category=category,
                    status="failed",
                    duration=time.time() - start_time,
                    error_message="未检测到成功标志"
                )

        except PlaywrightTimeout as e:
            return TestResult(
                skill_name=skill_name,
                skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                category=category,
                status="timeout",
                duration=time.time() - start_time,
                error_message=f"页面超时: {str(e)}"
            )
        except Exception as e:
            return TestResult(
                skill_name=skill_name,
                skill_display_name=SKILL_NAMES.get(skill_name, skill_name),
                category=category,
                status="error",
                duration=time.time() - start_time,
                error_message=f"异常: {str(e)}"
            )

    def _get_category(self, skill_name: str) -> str:
        """获取技能所属类别"""
        for cat, skills in SKILL_CATEGORIES.items():
            if skill_name in skills:
                return cat
        return "未知"

    async def test_skills(self, skill_list: Optional[List[str]] = None) -> TestReport:
        """测试指定技能列表"""
        skills_to_test = skill_list or ALL_SKILLS
        start_time = datetime.now().isoformat()
        test_start = time.time()

        print(f"开始测试 {len(skills_to_test)} 个技能...")

        for i, skill in enumerate(skills_to_test, 1):
            print(f"\n[{i}/{len(skills_to_test)}] 测试 {skill} ({SKILL_NAMES.get(skill, skill)})...")
            result = await self.load_example_and_run(skill)
            self.results.append(result)

            status_icon = "✅" if result.status == "success" else "❌" if result.status == "failed" else "⏱️"
            print(f"{status_icon} {result.status.upper()} - 耗时: {result.duration:.1f}s")
            if result.error_message:
                print(f"   错误: {result.error_message}")

        end_time = datetime.now().isoformat()
        total_duration = time.time() - test_start

        passed = sum(1 for r in self.results if r.status == "success")
        failed = sum(1 for r in self.results if r.status == "failed")
        timeout = sum(1 for r in self.results if r.status == "timeout")

        return TestReport(
            total_tests=len(skills_to_test),
            passed=passed,
            failed=failed,
            timeout=timeout,
            total_duration=total_duration,
            results=self.results,
            start_time=start_time,
            end_time=end_time,
            base_url=self.base_url
        )


def generate_report_html(report: TestReport, output_path: Path):
    """生成 HTML 格式的测试报告"""
    success_rate = (report.passed / report.total_tests * 100) if report.total_tests > 0 else 0

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CloudPSS 技能测试报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-box {{ padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-box.success {{ background: #e8f5e9; color: #2e7d32; }}
        .stat-box.failed {{ background: #ffebee; color: #c62828; }}
        .stat-box.timeout {{ background: #fff3e0; color: #ef6c00; }}
        .stat-box.total {{ background: #e3f2fd; color: #1565c0; }}
        .stat-number {{ font-size: 36px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: 600; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-success {{ color: #4CAF50; font-weight: 600; }}
        .status-failed {{ color: #f44336; font-weight: 600; }}
        .status-timeout {{ color: #ff9800; font-weight: 600; }}
        .status-error {{ color: #9c27b0; font-weight: 600; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); width: {success_rate}%; transition: width 0.3s; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
        .error-msg {{ color: #f44336; font-size: 12px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ CloudPSS 技能测试报告</h1>

        <div class="summary">
            <div class="stat-box total">
                <div class="stat-number">{report.total_tests}</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat-box success">
                <div class="stat-number">{report.passed}</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat-box failed">
                <div class="stat-number">{report.failed}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat-box timeout">
                <div class="stat-number">{report.timeout}</div>
                <div class="stat-label">超时</div>
            </div>
        </div>

        <div style="margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>成功率</span>
                <span>{success_rate:.1f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>

        <p><strong>测试时间:</strong> {report.start_time} ~ {report.end_time}</p>
        <p><strong>总耗时:</strong> {report.total_duration:.1f} 秒</p>
        <p><strong>测试地址:</strong> {report.base_url}</p>

        <h2>详细结果</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>技能名称</th>
                    <th>显示名称</th>
                    <th>类别</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>执行时间</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
    """

    for i, r in enumerate(report.results, 1):
        status_class = f"status-{r.status}"
        error_msg = r.error_message or "-"
        exec_time = r.execution_time or "-"
        html += f"""
                <tr>
                    <td>{i}</td>
                    <td><code>{r.skill_name}</code></td>
                    <td>{r.skill_display_name}</td>
                    <td>{r.category}</td>
                    <td class="{status_class}">{r.status.upper()}</td>
                    <td>{r.duration:.1f}s</td>
                    <td>{exec_time}</td>
                    <td class="error-msg" title="{error_msg}">{error_msg}</td>
                </tr>
        """

    html += f"""
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by CloudPSS Skill Tester</p>
        </div>
    </div>
</body>
</html>
    """

    output_path.write_text(html, encoding="utf-8")
    print(f"\nHTML 报告已生成: {output_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="CloudPSS 技能全面测试")
    parser.add_argument("--url", default="http://127.0.0.1:8702", help="前端地址")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    parser.add_argument("--skills", help="指定测试的技能，逗号分隔，如：power_flow,emt_simulation")
    parser.add_argument("--output", default="test_report", help="输出文件名（不含扩展名）")
    parser.add_argument("--category", help="按类别测试，如：仿真执行,稳定性分析")
    args = parser.parse_args()

    # 确定测试列表
    if args.skills:
        skills_to_test = [s.strip() for s in args.skills.split(",")]
    elif args.category:
        categories = [c.strip() for c in args.category.split(",")]
        skills_to_test = []
        for cat in categories:
            skills_to_test.extend(SKILL_CATEGORIES.get(cat, []))
    else:
        skills_to_test = None  # 测试所有

    # 运行测试
    tester = SkillTester(base_url=args.url, headless=args.headless)

    try:
        await tester.setup()
        report = await tester.test_skills(skills_to_test)

        # 生成报告
        output_dir = Path("tests/e2e/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON 报告
        json_path = output_dir / f"{args.output}.json"
        json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON 报告已生成: {json_path}")

        # HTML 报告
        html_path = output_dir / f"{args.output}.html"
        generate_report_html(report, html_path)

        # 打印摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"总测试数: {report.total_tests}")
        print(f"通过: {report.passed} ({report.passed/report.total_tests*100:.1f}%)")
        print(f"失败: {report.failed}")
        print(f"超时: {report.timeout}")
        print(f"总耗时: {report.total_duration:.1f}s")

        # 失败的技能
        if report.failed > 0 or report.timeout > 0:
            print("\n失败的技能:")
            for r in report.results:
                if r.status in ("failed", "timeout", "error"):
                    print(f"  - {r.skill_name}: {r.error_message}")

    finally:
        await tester.teardown()


if __name__ == "__main__":
    asyncio.run(main())
