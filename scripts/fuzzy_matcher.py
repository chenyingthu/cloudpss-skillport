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

    # 所有有效技能名称
    VALID_SKILLS = [
        "power_flow",
        "emt_simulation",
        "batch_powerflow",
        "n1_security",
        "param_scan",
        "waveform_export",
        "visualize",
        "result_compare",
        "topology_check",
        "ieee3_prep"
    ]

    # 常见别名
    ALIASES = {
        # 潮流计算
        "pf": "power_flow",
        "powerflow": "power_flow",
        "loadflow": "power_flow",
        "潮流": "power_flow",

        # EMT仿真
        "emt": "emt_simulation",
        "emtp": "emt_simulation",
        "transient": "emt_simulation",
        "暂态": "emt_simulation",

        # N-1安全
        "n1": "n1_security",
        "n1security": "n1_security",
        "n-1": "n1_security",
        "security": "n1_security",
        "安全": "n1_security",

        # 参数扫描
        "scan": "param_scan",
        "ps": "param_scan",
        "扫描": "param_scan",

        # 批量潮流
        "batch": "batch_powerflow",
        "batchpf": "batch_powerflow",
        "批量": "batch_powerflow",

        # 波形导出
        "export": "waveform_export",
        "waveform": "waveform_export",
        "导出": "waveform_export",

        # 可视化
        "viz": "visualize",
        "plot": "visualize",
        "graph": "visualize",
        "画图": "visualize",

        # 结果对比
        "compare": "result_compare",
        "diff": "result_compare",
        "对比": "result_compare",

        # 拓扑检查
        "topology": "topology_check",
        "check": "topology_check",
        "检查": "topology_check"
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
            "仿真执行": ["power_flow", "emt_simulation", "batch_powerflow"],
            "安全分析": ["n1_security", "param_scan"],
            "后处理": ["waveform_export", "visualize", "result_compare"],
            "模型工具": ["topology_check", "ieee3_prep"]
        }

        for category, skills in categories.items():
            print(f"\n  {category}:")
            for skill in skills:
                aliases = [k for k, v in self.ALIASES.items() if v == skill and k != skill]
                alias_str = f" (别名: {', '.join(aliases)})" if aliases else ""
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
