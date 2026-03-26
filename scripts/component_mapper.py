#!/usr/bin/env python3
"""
元件映射器

查询模型拓扑并列出可用元件，自动推断元件ID。
解决 Issue #002: 元件ID自动推断缺失
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ComponentMapper:
    """元件映射器"""

    # 常见元件类型映射
    COMPONENT_TYPES = {
        "负载": ["Load", "PQ Load", "Constant Impedance Load", "ZIP Load"],
        "发电机": ["Generator", "Synchronous Generator", "Wind Generator", "PV Generator"],
        "变压器": ["Transformer", "Two Winding Transformer", "Three Winding Transformer"],
        "线路": ["Line", "Transmission Line", "Cable", "Transmission Line (RL)"],
        "母线": ["Bus", "Bus Bar", "Infinite Bus"],
        "断路器": ["Breaker", "Switch"],
        "故障": ["Fault", "Three Phase Fault"]
    }

    # 常见元件命名模式
    NAMING_PATTERNS = {
        "负载": ["Load_{id}", "Load_{bus}", "PQ_{id}", "Load{id}"],
        "发电机": ["Gen_{id}", "Generator_{id}", "G{id}", "SG_{id}"],
        "变压器": ["T_{id}", "Transformer_{id}", "Trf_{id}"],
        "线路": ["Line_{id}", "Line_{from}_{to}", "L_{id}"],
        "母线": ["Bus_{id}", "Bus{id}", "B_{id}"],
        "断路器": ["Breaker_{id}", "Switch_{id}", "CB_{id}"]
    }

    def __init__(self, token_file: str = ".cloudpss_token"):
        self.token_file = token_file
        self.token = self._load_token()

    def _load_token(self) -> str:
        """加载Token"""
        try:
            with open(self.token_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"❌ Token文件不存在: {self.token_file}")
            print("请创建Token文件: echo 'your_token' > .cloudpss_token")
            sys.exit(1)

    def get_model_components(self, model_rid: str) -> List[Dict]:
        """获取模型的所有元件"""
        try:
            from cloudpss import Model, setToken
            setToken(self.token)

            print(f"🔍 正在获取模型 {model_rid} 的元件信息...")
            model = Model.fetch(model_rid)
            components = model.getAllComponents()

            result = []
            for comp_id, comp in components.items():
                comp_info = {
                    "id": comp_id,
                    "name": getattr(comp, "name", comp_id),
                    "definition": getattr(comp, "definition", ""),
                    "type": self._infer_type(getattr(comp, "definition", ""))
                }
                result.append(comp_info)

            return result

        except Exception as e:
            print(f"❌ 获取元件失败: {e}")
            return []

    def _infer_type(self, definition: str) -> str:
        """从定义推断元件类型"""
        definition_lower = definition.lower()

        type_keywords = {
            "负载": ["load", "pq", "zip"],
            "发电机": ["generator", "gen", "sg"],
            "变压器": ["transformer", "trf"],
            "线路": ["line", "cable", "transmission"],
            "母线": ["bus", "infinite"],
            "断路器": ["breaker", "switch"]
        }

        for type_name, keywords in type_keywords.items():
            if any(kw in definition_lower for kw in keywords):
                return type_name

        return "其他"

    def find_components_by_type(self, model_rid: str, comp_type: str) -> List[Dict]:
        """按类型查找元件"""
        all_components = self.get_model_components(model_rid)

        # 检查是否直接匹配类型名
        matched = [c for c in all_components if c["type"] == comp_type]

        # 如果没有直接匹配，尝试关键词匹配
        if not matched:
            type_keywords = self.COMPONENT_TYPES.get(comp_type, [comp_type])
            matched = [
                c for c in all_components
                if any(kw.lower() in c["definition"].lower() for kw in type_keywords)
            ]

        return matched

    def find_component_by_name(self, model_rid: str, name_pattern: str) -> List[Dict]:
        """按名称模式查找元件"""
        all_components = self.get_model_components(model_rid)

        matched = []
        name_lower = name_pattern.lower()

        for comp in all_components:
            if (name_lower in comp["id"].lower() or
                name_lower in comp["name"].lower()):
                matched.append(comp)

        return matched

    def suggest_components(self, model_rid: str, description: str) -> Dict[str, List[Dict]]:
        """根据描述推荐元件"""
        suggestions = {}

        # 1. 检查是否提到特定类型
        for type_name in self.COMPONENT_TYPES.keys():
            if type_name in description:
                components = self.find_components_by_type(model_rid, type_name)
                if components:
                    suggestions[type_name] = components

        # 2. 如果没有类型匹配，尝试数字匹配（如Bus1, Load2）
        if not suggestions:
            import re
            matches = re.findall(r'(\w+?)(\d+)', description)
            for prefix, num in matches:
                pattern = f"{prefix}{num}"
                components = self.find_component_by_name(model_rid, pattern)
                if components:
                    suggestions[f"匹配 '{pattern}'"] = components

        # 3. 如果仍然没有，返回常见元件类型示例
        if not suggestions:
            print("💡 未找到匹配元件，以下是可用元件类型：")
            all_components = self.get_model_components(model_rid)
            type_count = {}
            for comp in all_components:
                t = comp["type"]
                type_count[t] = type_count.get(t, 0) + 1

            for t, count in sorted(type_count.items(), key=lambda x: -x[1]):
                suggestions[t] = [f"（共 {count} 个）"]

        return suggestions

    def print_component_list(self, components: List[Dict], title: str = "元件列表"):
        """打印元件列表"""
        print(f"\n📋 {title}")
        print("-" * 80)
        print(f"{'序号':<6}{'元件ID':<25}{'名称':<25}{'类型':<15}")
        print("-" * 80)

        for i, comp in enumerate(components[:20], 1):  # 最多显示20个
            print(f"{i:<6}{comp['id']:<25}{comp['name'][:24]:<25}{comp['type']:<15}")

        if len(components) > 20:
            print(f"\n... 还有 {len(components) - 20} 个元件")

        print("-" * 80)

    def generate_naming_guide(self) -> str:
        """生成元件命名指南"""
        guide = """
📖 元件命名模式指南

常见元件ID格式：
- 负载: Load_1, Load_2, Load_Bus1, PQ_1
- 发电机: Gen_1, Generator_2, G1, SG_1
- 变压器: T_1, Transformer_1, Trf_1
- 线路: Line_1, Line_Bus1_Bus2, L_1
- 母线: Bus_1, Bus1, B_1
- 断路器: Breaker_1, Switch_1, CB_1

查询方法：
1. 使用完整ID: Load_1
2. 使用部分匹配: Load_* 匹配所有负载
3. 使用Bus关联: Bus1 查找Bus1上的所有元件
"""
        return guide


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='元件映射器')
    parser.add_argument('--model', '-m', required=True, help='模型RID')
    parser.add_argument('--type', '-t', help='按类型筛选（如：负载、发电机）')
    parser.add_argument('--name', '-n', help='按名称搜索')
    parser.add_argument('--suggest', '-s', help='根据描述推荐')
    parser.add_argument('--token', default='.cloudpss_token', help='Token文件')

    args = parser.parse_args()

    mapper = ComponentMapper(args.token)

    if args.type:
        # 按类型查找
        components = mapper.find_components_by_type(args.model, args.type)
        mapper.print_component_list(components, f"类型 '{args.type}' 的元件")

    elif args.name:
        # 按名称搜索
        components = mapper.find_component_by_name(args.model, args.name)
        mapper.print_component_list(components, f"名称匹配 '{args.name}' 的元件")

    elif args.suggest:
        # 智能推荐
        suggestions = mapper.suggest_components(args.model, args.suggest)
        print(f"\n💡 根据描述 '{args.suggest}' 推荐的元件：")
        for type_name, components in suggestions.items():
            if isinstance(components[0], dict):
                mapper.print_component_list(components, type_name)
            else:
                print(f"\n{type_name}: {components[0]}")

    else:
        # 显示所有元件
        components = mapper.get_model_components(args.model)
        mapper.print_component_list(components, "所有元件")

        # 按类型统计
        print("\n📊 元件类型统计：")
        type_count = {}
        for comp in components:
            t = comp["type"]
            type_count[t] = type_count.get(t, 0) + 1

        for t, count in sorted(type_count.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}个")

        print(mapper.generate_naming_guide())


if __name__ == "__main__":
    main()
