#!/usr/bin/env python3
"""
模糊匹配器

提供拼写纠错和别名识别功能。
解决 Issue #006: CLI拼写错误提示缺失
"""

import sys
import difflib
from typing import List, Tuple, Optional


class FuzzyMatcher:
    """模糊匹配器"""

    # 所有有效技能名称 (37个)
    VALID_SKILLS = [
        # 仿真执行类
        "power_flow",
        "emt_simulation",
        "emt_fault_study",
        "short_circuit",
        # N-1安全分析类
        "n1_security",
        "emt_n1_screening",
        "contingency_analysis",
        "maintenance_security",
        # 批量与扫描类
        "batch_powerflow",
        "param_scan",
        "fault_clearing_scan",
        "fault_severity_scan",
        "batch_task_manager",
        "config_batch_runner",
        "orthogonal_sensitivity",
        # 稳定性分析类
        "voltage_stability",
        "transient_stability",
        "small_signal_stability",
        "frequency_response",
        "vsi_weak_bus",
        "dudv_curve",
        # 结果处理类
        "result_compare",
        "visualize",
        "waveform_export",
        "hdf5_export",
        "disturbance_severity",
        "compare_visualization",
        "comtrade_export",
        # 电能质量类
        "harmonic_analysis",
        "power_quality_analysis",
        "reactive_compensation_design",
        # 模型与拓扑类
        "ieee3_prep",
        "topology_check",
        "parameter_sensitivity",
        "auto_channel_setup",
        "auto_loop_breaker",
        "model_parameter_extractor"
    ]

    # 常见别名 - 30个技能
    ALIASES = {
        # ========== 仿真执行类 ==========
        # 潮流计算
        "pf": "power_flow",
        "powerflow": "power_flow",
        "loadflow": "power_flow",
        "潮流": "power_flow",
        "潮流计算": "power_flow",

        # EMT仿真
        "emt": "emt_simulation",
        "emtp": "emt_simulation",
        "transient": "emt_simulation",
        "暂态": "emt_simulation",
        "暂态仿真": "emt_simulation",

        # 故障研究
        "fault_study": "emt_fault_study",
        "故障研究": "emt_fault_study",
        "fault": "emt_fault_study",

        # 短路计算
        "short": "short_circuit",
        "短路": "short_circuit",
        "短路电流": "short_circuit",
        "短路计算": "short_circuit",

        # ========== N-1安全分析类 ==========
        # N-1安全
        "n1": "n1_security",
        "n1security": "n1_security",
        "n-1": "n1_security",
        "security": "n1_security",
        "安全": "n1_security",
        "安全校核": "n1_security",
        "n1安全": "n1_security",

        # EMT N-1筛查
        "emt_n1": "emt_n1_screening",
        "emt_n1_screening": "emt_n1_screening",
        "暂态n1": "emt_n1_screening",
        "emt安全筛查": "emt_n1_screening",

        # 预想事故
        "contingency": "contingency_analysis",
        "预想事故": "contingency_analysis",
        "事故分析": "contingency_analysis",

        # 检修安全
        "maintenance": "maintenance_security",
        "检修安全": "maintenance_security",
        "检修": "maintenance_security",
        "检修方式": "maintenance_security",

        # ========== 批量与扫描类 ==========
        # 批量潮流
        "batch": "batch_powerflow",
        "batchpf": "batch_powerflow",
        "批量": "batch_powerflow",
        "批量潮流": "batch_powerflow",

        # 参数扫描
        "scan": "param_scan",
        "ps": "param_scan",
        "扫描": "param_scan",
        "参数扫描": "param_scan",

        # 故障清除扫描
        "fault_clearing": "fault_clearing_scan",
        "清除扫描": "fault_clearing_scan",
        "故障清除": "fault_clearing_scan",

        # 故障严重度
        "severity_scan": "fault_severity_scan",
        "严重度扫描": "fault_severity_scan",
        "fault_severity": "fault_severity_scan",

        # 批处理任务管理
        "batch_manager": "batch_task_manager",
        "批处理": "batch_task_manager",
        "任务管理": "batch_task_manager",

        # 配置批量运行器
        "config_batch": "config_batch_runner",
        "config_batch_runner": "config_batch_runner",
        "配置批量": "config_batch_runner",
        "多配置运行": "config_batch_runner",
        "配置运行器": "config_batch_runner",

        # 正交敏感性分析
        "orthogonal": "orthogonal_sensitivity",
        "orthogonal_sensitivity": "orthogonal_sensitivity",
        "正交敏感": "orthogonal_sensitivity",
        "正交分析": "orthogonal_sensitivity",
        "DOE": "orthogonal_sensitivity",
        "实验设计": "orthogonal_sensitivity",

        # ========== 稳定性分析类 ==========
        # 电压稳定
        "voltage_stab": "voltage_stability",
        "电压稳定": "voltage_stability",
        "电压稳定性": "voltage_stability",

        # 暂态稳定
        "transient_stab": "transient_stability",
        "暂态稳定": "transient_stability",
        "暂态稳定性": "transient_stability",

        # 小信号稳定
        "small_signal": "small_signal_stability",
        "小信号": "small_signal_stability",
        "小干扰": "small_signal_stability",

        # 频率响应
        "frequency": "frequency_response",
        "频率响应": "frequency_response",
        "频率特性": "frequency_response",

        # VSI弱母线
        "vsi": "vsi_weak_bus",
        "weak_bus": "vsi_weak_bus",
        "弱母线": "vsi_weak_bus",
        "vsi分析": "vsi_weak_bus",
        "vsi_weak": "vsi_weak_bus",

        # DUDV曲线
        "dudv": "dudv_curve",
        "电压特性": "dudv_curve",
        "dudv曲线": "dudv_curve",

        # ========== 结果处理类 ==========
        # 波形导出
        "export": "waveform_export",
        "waveform": "waveform_export",
        "导出": "waveform_export",
        "波形导出": "waveform_export",

        # 可视化
        "viz": "visualize",
        "plot": "visualize",
        "graph": "visualize",
        "画图": "visualize",
        "可视化": "visualize",
        "绘图": "visualize",

        # 结果对比
        "compare": "result_compare",
        "diff": "result_compare",
        "对比": "result_compare",
        "结果对比": "result_compare",

        # HDF5导出
        "hdf5": "hdf5_export",
        "hdf5导出": "hdf5_export",

        # 扰动严重度
        "disturbance": "disturbance_severity",
        "扰动": "disturbance_severity",
        "扰动分析": "disturbance_severity",
        "扰动严重度": "disturbance_severity",

        # ========== 电能质量类 ==========
        # 谐波分析
        "harmonic": "harmonic_analysis",
        "谐波": "harmonic_analysis",
        "谐波分析": "harmonic_analysis",
        "thd": "harmonic_analysis",

        # 电能质量
        "quality": "power_quality_analysis",
        "电能质量": "power_quality_analysis",
        "供电质量": "power_quality_analysis",
        "power_quality": "power_quality_analysis",

        # 无功补偿设计
        "compensation": "reactive_compensation_design",
        "无功补偿": "reactive_compensation_design",
        "补偿设计": "reactive_compensation_design",
        "reactive": "reactive_compensation_design",

        # ========== 模型与拓扑类 ==========
        # 拓扑检查
        "topology": "topology_check",
        "check": "topology_check",
        "检查": "topology_check",
        "拓扑检查": "topology_check",

        # IEEE3准备
        "prep": "ieee3_prep",
        "准备": "ieee3_prep",
        "预处理": "ieee3_prep",
        "模型准备": "ieee3_prep",

        # 参数灵敏度
        "sensitivity": "parameter_sensitivity",
        "灵敏度": "parameter_sensitivity",
        "参数灵敏度": "parameter_sensitivity",
        "灵敏度分析": "parameter_sensitivity",

        # 自动量测配置
        "auto_channel": "auto_channel_setup",
        "auto_channel_setup": "auto_channel_setup",
        "自动通道": "auto_channel_setup",
        "自动量测": "auto_channel_setup",
        "量测配置": "auto_channel_setup",
        "通道设置": "auto_channel_setup",

        # 模型自动解环
        "loop_breaker": "auto_loop_breaker",
        "auto_loop_breaker": "auto_loop_breaker",
        "解环": "auto_loop_breaker",
        "消除环路": "auto_loop_breaker",
        "控制环路": "auto_loop_breaker",
        "自动解环": "auto_loop_breaker",

        # 模型参数提取器
        "parameter_extractor": "model_parameter_extractor",
        "model_parameter_extractor": "model_parameter_extractor",
        "参数提取": "model_parameter_extractor",
        "模型参数": "model_parameter_extractor",
        "提取参数": "model_parameter_extractor",
        "参数导出": "model_parameter_extractor",

        # ========== 结果处理类 (新增) ==========
        # 对比可视化
        "compare_viz": "compare_visualization",
        "compare_visualization": "compare_visualization",
        "对比可视化": "compare_visualization",
        "多场景对比": "compare_visualization",
        "对比图表": "compare_visualization",

        # COMTRADE导出
        "comtrade": "comtrade_export",
        "comtrade_export": "comtrade_export",
        "COMTRADE": "comtrade_export",
        "comtrade导出": "comtrade_export",
        "标准格式导出": "comtrade_export"
    }

    def __init__(self):
        self.all_names = self.VALID_SKILLS + list(self.ALIASES.keys())

    def find_match(self, input_str: str, threshold: float = 0.6) -> Tuple[Optional[str], float, str]:
        """
        查找最佳匹配

        返回: (匹配的技能名, 相似度, 提示信息)
        """
        input_lower = input_str.lower().strip()

        # 1. 直接匹配
        if input_lower in self.VALID_SKILLS:
            return input_lower, 1.0, "精确匹配"

        # 2. 别名匹配
        if input_lower in self.ALIASES:
            canonical = self.ALIASES[input_lower]
            return canonical, 1.0, f"别名 '{input_lower}' → '{canonical}'"

        # 3. 模糊匹配
        matches = difflib.get_close_matches(input_lower, self.VALID_SKILLS, n=3, cutoff=threshold)

        if matches:
            best_match = matches[0]
            similarity = difflib.SequenceMatcher(None, input_lower, best_match).ratio()

            if similarity >= threshold:
                return best_match, similarity, f"您是不是想输入 '{best_match}'？"

        # 4. 尝试删除空格和连字符后匹配
        normalized = input_lower.replace(" ", "").replace("-", "").replace("_", "")
        for skill in self.VALID_SKILLS:
            skill_normalized = skill.replace(" ", "").replace("-", "").replace("_", "")
            if normalized == skill_normalized:
                return skill, 0.95, f"自动纠正 '{input_str}' → '{skill}'"

        # 无匹配
        return None, 0.0, "未找到匹配"

    def get_suggestions(self, input_str: str, max_suggestions: int = 3) -> List[Tuple[str, float, str]]:
        """获取多个建议"""
        input_lower = input_str.lower().strip()

        suggestions = []

        # 获取相似匹配
        matches = difflib.get_close_matches(input_lower, self.VALID_SKILLS, n=max_suggestions, cutoff=0.4)

        for match in matches:
            similarity = difflib.SequenceMatcher(None, input_lower, match).ratio()
            suggestions.append((match, similarity, f"相似度: {similarity:.1%}"))

        return suggestions

    def print_error_help(self, input_str: str):
        """打印错误帮助信息"""
        print(f"\n❌ 未知技能: '{input_str}'")

        match, similarity, message = self.find_match(input_str)

        if match:
            print(f"\n💡 {message}")
            print(f"\n自动使用: '{match}'")
            return match
        else:
            print("\n💡 您是不是想输入:")
            suggestions = self.get_suggestions(input_str)
            for i, (suggested, sim, _) in enumerate(suggestions, 1):
                print(f"  {i}. {suggested}")

            print("\n📋 所有可用技能:")
            self.print_all_skills()

            return None

    def print_all_skills(self):
        """打印所有技能"""
        categories = {
            "仿真执行类": ["power_flow", "emt_simulation", "emt_fault_study", "short_circuit"],
            "N-1安全分析类": ["n1_security", "emt_n1_screening", "contingency_analysis", "maintenance_security"],
            "批量与扫描类": ["batch_powerflow", "param_scan", "fault_clearing_scan", "fault_severity_scan", "batch_task_manager", "config_batch_runner", "orthogonal_sensitivity"],
            "稳定性分析类": ["voltage_stability", "transient_stability", "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve"],
            "结果处理类": ["result_compare", "visualize", "waveform_export", "hdf5_export", "disturbance_severity", "compare_visualization", "comtrade_export"],
            "电能质量类": ["harmonic_analysis", "power_quality_analysis", "reactive_compensation_design"],
            "模型与拓扑类": ["ieee3_prep", "topology_check", "parameter_sensitivity", "auto_channel_setup", "auto_loop_breaker", "model_parameter_extractor"]
        }

        for category, skills in categories.items():
            print(f"\n  {category}:")
            for skill in skills:
                aliases = [k for k, v in self.ALIASES.items() if v == skill and k != skill]
                alias_str = f" (别名: {', '.join(aliases[:5])}{'...' if len(aliases) > 5 else ''})" if aliases else ""
                print(f"    - {skill}{alias_str}")

    def auto_correct(self, input_str: str, interactive: bool = True) -> Optional[str]:
        """自动纠正或询问用户"""
        match, similarity, message = self.find_match(input_str)

        if not match:
            self.print_error_help(input_str)
            return None

        if similarity >= 0.9:
            # 高置信度，自动纠正
            if similarity < 1.0:
                print(f"💡 自动纠正: '{input_str}' → '{match}'")
            return match

        if interactive and similarity >= 0.6:
            # 中等置信度，询问用户
            print(f"\n❓ 您输入的是 '{input_str}'")
            print(f"   您是不是想输入 '{match}'？")
            answer = input("   是/否 [Y/n]: ").strip().lower()

            if answer in ['', 'y', 'yes', '是']:
                return match
            else:
                # 显示其他建议
                print("\n其他可能的选项:")
                suggestions = self.get_suggestions(input_str)
                for i, (suggested, _, _) in enumerate(suggestions[:3], 1):
                    print(f"  {i}. {suggested}")

                choice = input("\n请选择 (输入数字或技能名，直接回车取消): ").strip()

                if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                    return suggestions[int(choice) - 1][0]
                elif choice in self.VALID_SKILLS:
                    return choice

                return None

        return match


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='模糊匹配器')
    parser.add_argument('input', help='输入的技能名')
    parser.add_argument('--auto', '-a', action='store_true', help='自动纠正（不询问）')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有技能')

    args = parser.parse_args()

    matcher = FuzzyMatcher()

    if args.list:
        print("\n📋 所有可用技能:")
        matcher.print_all_skills()
        print()
        return

    match, similarity, message = matcher.find_match(args.input)

    print(f"\n输入: '{args.input}'")
    print(f"匹配: {match if match else '无'}")
    print(f"相似度: {similarity:.1%}")
    print(f"消息: {message}")

    if not match:
        print("\n建议:")
        suggestions = matcher.get_suggestions(args.input)
        for suggested, sim, _ in suggestions:
            print(f"  - {suggested} (相似度: {sim:.1%})")

    # 如果找到匹配且不是精确匹配，显示自动纠正
    if match and similarity < 1.0 and args.auto:
        print(f"\n✅ 自动纠正为: {match}")
        return match


if __name__ == "__main__":
    main()
