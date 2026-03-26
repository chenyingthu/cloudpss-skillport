#!/usr/bin/env python3
"""
通道名称助手

推断波形通道名称模式，解决通道选择问题。
解决 Issue #004: 通道名称推断缺失
解决 Issue #005: 结果对比通道选择不清晰
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json


class ChannelHelper:
    """通道名称助手"""

    # 常见信号类型
    SIGNAL_TYPES = {
        "电压": {
            "single_phase": ["{bus}_V", "{bus}_Voltage", "V_{bus}"],
            "three_phase": ["{bus}_Va", "{bus}_Vb", "{bus}_Vc"],
            "line_voltage": ["{bus}_Vab", "{bus}_Vbc", "{bus}_Vca"],
            "positive_sequence": ["{bus}_V1", "{bus}_Vpos"],
            "magnitude": ["{bus}_Vm", "{bus}_Vmag", "V_{bus}_mag"]
        },
        "电流": {
            "single_phase": ["{branch}_I", "{branch}_Current"],
            "three_phase": ["{branch}_Ia", "{branch}_Ib", "{branch}_Ic"],
            "positive_sequence": ["{branch}_I1", "{branch}_Ipos"]
        },
        "功率": {
            "active": ["{bus}_P", "{bus}_ActivePower", "P_{bus}"],
            "reactive": ["{bus}_Q", "{bus}_ReactivePower", "Q_{bus}"],
            "apparent": ["{bus}_S", "{bus}_ApparentPower"]
        },
        "频率": {
            "base": ["{bus}_f", "{bus}_freq", "Frequency_{bus}"]
        },
        "转速": {
            "base": ["{gen}_omega", "{gen}_speed", "Speed_{gen}"]
        },
        "功角": {
            "base": ["{gen}_delta", "{gen}_angle", "Angle_{gen}"]
        }
    }

    # 相位缩写
    PHASES = {
        "三相": ["Va", "Vb", "Vc"],
        "A相": ["Va"],
        "B相": ["Vb"],
        "C相": ["Vc"],
        "AB相": ["Vab"],
        "BC相": ["Vbc"],
        "CA相": ["Vca"],
        "正序": ["V1"],
        "负序": ["V2"],
        "零序": ["V0"]
    }

    # 常见节点命名模式
    BUS_PATTERNS = [
        r"Bus(\d+)",
        r"BUS(\d+)",
        r"bus(\d+)",
        r"B(\d+)",
        r"Node(\d+)",
        r"NODE(\d+)"
    ]

    def __init__(self):
        pass

    def infer_channels(self, description: str) -> Dict[str, any]:
        """
        从描述中推断通道名称

        示例：
        - "Bus1的三相电压" → ["Bus1_Va", "Bus1_Vb", "Bus1_Vc"]
        - "Line2的电流" → ["Line2_Ia", "Line2_Ib", "Line2_Ic"]
        """
        result = {
            "node": None,
            "signal_type": None,
            "phase": None,
            "channels": [],
            "wildcard": None,
            "alternatives": []
        }

        # 1. 提取节点名（Bus1, Bus2等）
        node = self._extract_node(description)
        result["node"] = node

        # 2. 提取信号类型（电压、电流、功率等）
        signal_type = self._extract_signal_type(description)
        result["signal_type"] = signal_type

        # 3. 提取相位信息（三相、A相、正序等）
        phase = self._extract_phase(description)
        result["phase"] = phase

        # 4. 生成通道名
        channels = self._generate_channels(node, signal_type, phase)
        result["channels"] = channels

        # 5. 生成通配符模式
        wildcard = self._generate_wildcard(node, signal_type, phase)
        result["wildcard"] = wildcard

        # 6. 生成备选方案
        alternatives = self._generate_alternatives(node, signal_type, phase)
        result["alternatives"] = alternatives

        return result

    def _extract_node(self, description: str) -> Optional[str]:
        """提取节点名"""
        import re

        # 匹配 "Bus1", "Bus 1", "bus1" 等
        patterns = [
            r'(?:Bus|BUS|bus)[\s_]*(\d+)',
            r'(?:Node|NODE|node)[\s_]*(\d+)',
            r'(?:Line|LINE|line)[\s_]*(\d+)',
            r'(?:Gen|GEN|gen|Generator)[\s_]*(\d+)',
            r'(?:Load|LOAD|load)[\s_]*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # 返回完整匹配
                full_match = re.search(r'(\w+)[\s_]*' + match.group(1), description, re.IGNORECASE)
                if full_match:
                    return full_match.group(0).replace(' ', '_')
                return match.group(0).replace(' ', '_')

        return None

    def _extract_signal_type(self, description: str) -> Optional[str]:
        """提取信号类型"""
        desc_lower = description.lower()

        signal_keywords = {
            "电压": ["电压", "voltage", "volt", "v", "电位"],
            "电流": ["电流", "current", "amp", "i"],
            "功率": ["功率", "power", "p", "q", "s"],
            "有功": ["有功", "active", "p"],
            "无功": ["无功", "reactive", "q"],
            "频率": ["频率", "frequency", "freq", "f"],
            "转速": ["转速", "speed", "omega", "ω"],
            "功角": ["功角", "angle", "delta", "δ"]
        }

        for signal_type, keywords in signal_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return signal_type

        return None

    def _extract_phase(self, description: str) -> Optional[str]:
        """提取相位信息"""
        desc_lower = description.lower()

        phase_keywords = {
            "三相": ["三相", "three phase", "3-phase", "abc", "all phases"],
            "A相": ["a相", "phase a", "va", "ia"],
            "B相": ["b相", "phase b", "vb", "ib"],
            "C相": ["c相", "phase c", "vc", "ic"],
            "正序": ["正序", "positive", "sequence", "v1"],
            "负序": ["负序", "negative", "v2"],
            "零序": ["零序", "zero", "v0"],
            "线电压": ["线电压", "line voltage", "vab", "vll"]
        }

        for phase, keywords in phase_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return phase

        # 如果没有指定相位，默认返回三相（对于EMT仿真）
        return "三相"

    def _generate_channels(self, node: str, signal_type: str, phase: str) -> List[str]:
        """生成通道名列表"""
        if not node or not signal_type:
            return []

        channels = []

        # 根据信号类型和相位生成
        if signal_type in ["电压", "volt", "v"]:
            if phase in ["三相", "three phase"]:
                channels = [f"{node}_Va", f"{node}_Vb", f"{node}_Vc"]
            elif phase == "A相":
                channels = [f"{node}_Va"]
            elif phase == "B相":
                channels = [f"{node}_Vb"]
            elif phase == "C相":
                channels = [f"{node}_Vc"]
            elif phase == "正序":
                channels = [f"{node}_V1"]
            elif phase == "线电压":
                channels = [f"{node}_Vab", f"{node}_Vbc", f"{node}_Vca"]
            else:
                # 默认三相
                channels = [f"{node}_Va", f"{node}_Vb", f"{node}_Vc"]

        elif signal_type in ["电流", "current", "i"]:
            if phase in ["三相", "three phase"]:
                channels = [f"{node}_Ia", f"{node}_Ib", f"{node}_Ic"]
            elif phase == "A相":
                channels = [f"{node}_Ia"]
            elif phase == "B相":
                channels = [f"{node}_Ib"]
            elif phase == "C相":
                channels = [f"{node}_Ic"]
            else:
                channels = [f"{node}_Ia", f"{node}_Ib", f"{node}_Ic"]

        elif signal_type in ["有功", "active", "p"]:
            channels = [f"{node}_P"]

        elif signal_type in ["无功", "reactive", "q"]:
            channels = [f"{node}_Q"]

        elif signal_type in ["功率", "power"]:
            channels = [f"{node}_P", f"{node}_Q", f"{node}_S"]

        elif signal_type in ["频率", "frequency", "f"]:
            channels = [f"{node}_f"]

        return channels

    def _generate_wildcard(self, node: str, signal_type: str, phase: str) -> Optional[str]:
        """生成通配符模式"""
        if not node:
            return None

        if signal_type in ["电压", "volt", "v"]:
            if phase in ["三相", "three phase"]:
                return f"{node}_V*"
            elif phase == "A相":
                return f"{node}_Va"
            elif phase == "B相":
                return f"{node}_Vb"
            elif phase == "C相":
                return f"{node}_Vc"

        elif signal_type in ["电流", "current", "i"]:
            return f"{node}_I*"

        return None

    def _generate_alternatives(self, node: str, signal_type: str, phase: str) -> List[str]:
        """生成备选命名格式"""
        if not node or not signal_type:
            return []

        alternatives = []
        base_num = node.replace("Bus", "").replace("BUS", "").replace("bus", "")

        if signal_type in ["电压", "volt", "v"]:
            alternatives = [
                f"V_{node}",
                f"Voltage_{node}",
                f"Bus{base_num}_Voltage"
            ]
        elif signal_type in ["电流", "current", "i"]:
            alternatives = [
                f"I_{node}",
                f"Current_{node}",
                f"Line_{base_num}_Current"
            ]

        return alternatives

    def get_channel_suggestions(self, node: str = None, signal_type: str = None) -> Dict:
        """获取通道选择建议"""
        suggestions = {
            "常用组合": [
                {"name": "三相电压", "channels": [f"{node}_Va", f"{node}_Vb", f"{node}_Vc"], "wildcard": f"{node}_V*"},
                {"name": "三相电流", "channels": [f"{node}_Ia", f"{node}_Ib", f"{node}_Ic"], "wildcard": f"{node}_I*"},
                {"name": "有功无功", "channels": [f"{node}_P", f"{node}_Q"], "wildcard": None}
            ],
            "相位选项": {
                "全部三相": [f"{node}_Va", f"{node}_Vb", f"{node}_Vc"],
                "仅A相": [f"{node}_Va"],
                "仅B相": [f"{node}_Vb"],
                "仅C相": [f"{node}_Vc"],
                "正序": [f"{node}_V1"]
            }
        }
        return suggestions

    def print_channel_guide(self, node: str):
        """打印通道选择指南"""
        print(f"\n📖 {node} 的通道选择指南")
        print("-" * 60)

        print("\n电压通道：")
        print(f"  三相: {node}_Va, {node}_Vb, {node}_Vc")
        print(f"  通配符: {node}_V*")
        print(f"  正序: {node}_V1")
        print(f"  线电压: {node}_Vab, {node}_Vbc, {node}_Vca")

        print("\n电流通道：")
        print(f"  三相: {node}_Ia, {node}_Ib, {node}_Ic")
        print(f"  通配符: {node}_I*")

        print("\n功率通道：")
        print(f"  有功: {node}_P")
        print(f"  无功: {node}_Q")
        print(f"  视在: {node}_S")

        print("\n其他通道：")
        print(f"  频率: {node}_f")
        print(f"  转速: {node}_omega")
        print(f"  功角: {node}_delta")

        print("-" * 60)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='通道名称助手')
    parser.add_argument('--parse', '-p', help='解析描述（如：Bus1的三相电压）')
    parser.add_argument('--node', '-n', help='节点名（如：Bus7）')
    parser.add_argument('--type', '-t', choices=['电压', '电流', '功率', '频率'], help='信号类型')
    parser.add_argument('--phase', choices=['三相', 'A相', 'B相', 'C相', '正序'], help='相位')
    parser.add_argument('--guide', '-g', metavar='NODE', help='显示节点通道指南')

    args = parser.parse_args()

    helper = ChannelHelper()

    if args.parse:
        # 解析描述
        result = helper.infer_channels(args.parse)
        print(f"\n🔍 解析: '{args.parse}'")
        print("-" * 60)
        print(f"节点: {result['node']}")
        print(f"信号类型: {result['signal_type']}")
        print(f"相位: {result['phase']}")
        print(f"\n建议通道: {result['channels']}")
        if result['wildcard']:
            print(f"通配符: {result['wildcard']}")
        if result['alternatives']:
            print(f"备选格式: {result['alternatives']}")
        print("-" * 60)

    elif args.guide:
        # 显示指南
        helper.print_channel_guide(args.guide)

    elif args.node and args.type:
        # 根据参数生成
        phase = args.phase or "三相"
        result = helper.infer_channels(f"{args.node}的{phase}{args.type}")
        print(f"\n📋 {args.node} 的{phase}{args.type}通道：")
        print(f"  通道: {result['channels']}")
        if result['wildcard']:
            print(f"  通配符: {result['wildcard']}")

    else:
        # 示例
        print("\n💡 使用示例:")
        print("  python channel_helper.py -p 'Bus1的三相电压'")
        print("  python channel_helper.py -n Bus7 -t 电压 --phase A相")
        print("  python channel_helper.py -g Bus7")
        print()

        # 运行示例
        examples = [
            "Bus1的三相电压",
            "Bus7的A相电流",
            "Line2的有功功率",
            "Gen1的转速"
        ]

        print("示例解析:")
        for ex in examples:
            result = helper.infer_channels(ex)
            print(f"  '{ex}' → {result['channels']}")


if __name__ == "__main__":
    main()
