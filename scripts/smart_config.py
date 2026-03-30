#!/usr/bin/env python3
"""
智能配置生成器

从自然语言描述中提取参数并生成YAML配置。
解决 Issue #001: 配置参数智能填充
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml


class SmartConfigGenerator:
    """智能配置生成器"""

    # 技能关键词映射 - 37个技能
    SKILL_KEYWORDS = {
        # 仿真执行类
        "power_flow": ["潮流", "power flow", "load flow", "稳态", "pf", "潮流计算"],
        "emt_simulation": ["EMT", "暂态", "transient", "波形", "emtp", "电磁暂态"],
        "emt_fault_study": ["故障研究", "fault study", "短路研究", "故障分析"],
        "short_circuit": ["短路", "short circuit", "短路计算", "短路电流"],

        # N-1安全分析类
        "n1_security": ["N-1", "安全校核", "N-1筛查", "安全评估", "检修", "n1安全"],
        "emt_n1_screening": ["EMT N-1", "暂态N-1", "emt_n1", "暂态安全筛查"],
        "contingency_analysis": ["预想事故", "contingency", "事故分析", "故障集分析"],
        "maintenance_security": ["检修安全", "maintenance", "检修方式", "计划检修"],

        # 批量与扫描类
        "batch_powerflow": ["批量", "batch", "批量潮流", "多模型"],
        "param_scan": ["参数扫描", "param scan", "敏感性", "扫描", "参数分析"],
        "fault_clearing_scan": ["故障清除", "fault clearing", "清除时间", "故障切除"],
        "fault_severity_scan": ["故障严重度", "fault severity", "严重度扫描", "故障程度"],
        "batch_task_manager": ["批处理", "batch task", "任务管理", "批量任务"],
        "config_batch_runner": ["配置批量", "config batch", "多配置运行", "配置运行器"],
        "orthogonal_sensitivity": ["正交敏感", "orthogonal", "正交分析", "DOE", "实验设计"],

        # 稳定性分析类
        "voltage_stability": ["电压稳定", "voltage stability", "电压稳定性", "静态电压稳定"],
        "transient_stability": ["暂态稳定", "transient stability", "暂态稳定性", "大扰动稳定"],
        "small_signal_stability": ["小信号", "small signal", "小干扰", "特征值分析"],
        "frequency_response": ["频率响应", "frequency response", "频率特性", "调频"],
        "vsi_weak_bus": ["VSI", "弱母线", "weak bus", "电压稳定指标", "vsi分析"],
        "dudv_curve": ["DUDV", "电压特性", "dudv曲线", "无功电压特性"],

        # 结果处理类
        "result_compare": ["对比", "compare", "比较结果", "结果对比"],
        "visualize": ["可视化", "画图", "plot", "绘图"],
        "waveform_export": ["波形导出", "export", "提取波形", "波形提取"],
        "hdf5_export": ["HDF5", "hdf5导出", "hdf5 export", "二进制导出"],
        "disturbance_severity": ["扰动严重度", "disturbance", "扰动分析", "故障严重度分析"],
        "compare_visualization": ["对比可视化", "compare visualization", "多场景对比", "对比图表"],
        "comtrade_export": ["COMTRADE", "comtrade导出", "标准格式导出", "暂态数据导出"],

        # 电能质量类
        "harmonic_analysis": ["谐波", "harmonic", "谐波分析", "THD"],
        "power_quality_analysis": ["电能质量", "power quality", "电能质量分析", "供电质量"],
        "reactive_compensation_design": ["无功补偿", "reactive compensation", "补偿设计", "电容器配置"],

        # 模型与拓扑类
        "ieee3_prep": ["准备", "prep", "预处理", "模型准备"],
        "topology_check": ["拓扑", "topology", "检查模型", "拓扑分析"],
        "parameter_sensitivity": ["灵敏度", "sensitivity", "参数灵敏度", "灵敏度分析"],
        "auto_channel_setup": ["自动通道", "auto channel", "量测配置", "自动量测", "通道设置"],
        "auto_loop_breaker": ["解环", "loop breaker", "消除环路", "控制环路", "自动解环"],
        "model_parameter_extractor": ["参数提取", "parameter extractor", "模型参数", "提取参数", "参数导出"]
    }

    # 算法类型映射
    ALGORITHM_MAP = {
        "牛顿": "newton_raphson",
        "牛顿法": "newton_raphson",
        "newton": "newton_raphson",
        "快速分解": "fast_decoupled",
        "fast": "fast_decoupled"
    }

    # 输出格式映射
    FORMAT_MAP = {
        "json": "json",
        "csv": "csv",
        "yaml": "yaml",
        "png": "png",
        "图片": "png",
        "表格": "csv"
    }

    # 模型映射
    MODEL_MAP = {
        "IEEE39": "model/holdme/IEEE39",
        "IEEE3": "model/holdme/IEEE3",
        "IEEE9": "model/holdme/IEEE9",
        "IEEE14": "model/holdme/IEEE14",
        "IEEE118": "model/holdme/IEEE118"
    }

    def __init__(self):
        self.config = {}
        self._check_toolkit_available()

    def _check_toolkit_available(self):
        """检查 cloudpss-toolkit 是否已安装"""
        try:
            import cloudpss_skills
            # 获取 toolkit 版本信息（如果可用）
            version = getattr(cloudpss_skills, '__version__', 'unknown')
            # 检查关键技能是否可用
            from cloudpss_skills import PowerFlowSkill
            return True
        except ImportError:
            print("⚠️  警告: 未检测到 cloudpss-toolkit")
            print("    请先安装 toolkit:")
            print("    git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit.git")
            print("    cd cloudpss-toolkit && pip install -e .")
            return False

    def detect_skill(self, prompt: str) -> str:
        """从用户输入中检测技能类型"""
        prompt_lower = prompt.lower()

        scores = {}
        for skill, keywords in self.SKILL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in prompt_lower)
            if score > 0:
                scores[skill] = score

        if not scores:
            return "power_flow"  # 默认

        return max(scores, key=scores.get)

    def extract_model(self, prompt: str) -> str:
        """提取模型名称"""
        # 匹配 IEEE数字 模式
        patterns = [
            r'IEEE\s*(\d+)',
            r'ieee\s*(\d+)',
            r'IEEE(\d+)',
            r'ieee(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                ieee_num = match.group(1)
                key = f"IEEE{ieee_num}"
                if key in self.MODEL_MAP:
                    return self.MODEL_MAP[key]

        # 默认模型
        return "model/holdme/IEEE39"

    def extract_tolerance(self, prompt: str) -> float:
        """提取收敛精度"""
        # 匹配模式：1e-6, 1e-8, 1.0e-6, 0.000001
        patterns = [
            r'收敛精度[\s]*[:为]?\s*([\d.eE-]+)',
            r'精度[\s]*[:为]?\s*([\d.eE-]+)',
            r'tolerance[\s]*[:=]?\s*([\d.eE-]+)',
            r'([\d.eE-]+)\s*[的]?收敛'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        # 匹配"高精度"等模糊描述
        if "高精度" in prompt or "高一点" in prompt:
            return 1.0e-8
        if "低精度" in prompt or "粗略" in prompt:
            return 1.0e-4

        return 1.0e-6  # 默认

    def extract_iterations(self, prompt: str) -> int:
        """提取最大迭代次数"""
        patterns = [
            r'最大迭代[\s]*[:为]?\s*(\d+)',
            r'迭代[\s]*[:为]?\s*(\d+)\s*次',
            r'(\d+)\s*次迭代',
            r'iteration[\s]*[:=]?\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 100  # 默认

    def extract_algorithm(self, prompt: str) -> str:
        """提取算法类型"""
        for cn_name, en_name in self.ALGORITHM_MAP.items():
            if cn_name in prompt:
                return en_name
        return "newton_raphson"  # 默认

    def extract_format(self, prompt: str) -> str:
        """提取输出格式"""
        for fmt_keyword, fmt_value in self.FORMAT_MAP.items():
            if fmt_keyword in prompt:
                return fmt_value
        return "json"  # 默认

    def extract_duration(self, prompt: str) -> float:
        """提取EMT仿真时长"""
        patterns = [
            r'仿真[\s]*([\d.]+)\s*秒',
            r'仿真[\s]*([\d.]+)\s*s',
            r'时长[\s]*[:为]?\s*([\d.]+)',
            r'duration[\s]*[:=]?\s*([\d.]+)',
            r'([\d.]+)\s*秒[\s]*仿真'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return 5.0  # 默认5秒

    def extract_step_size(self, prompt: str) -> float:
        """提取积分步长"""
        patterns = [
            r'步长[\s]*[:为]?\s*([\d.eE-]+)',
            r'step[\s]*[:=]?\s*([\d.eE-]+)',
            r'([\d.eE-]+)\s*[的]?步长'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return 0.0001  # 默认0.0001s

    def extract_threshold(self, prompt: str, threshold_type: str = "voltage") -> float:
        """提取阈值（支持百分比）"""
        # 匹配模式：10%, 0.1, 5%
        patterns = [
            rf'{threshold_type}[\s]*阈值[\s]*[:为]?\s*([\d.%]+)',
            rf'阈值[\s]*[:为]?\s*([\d.%]+)',
            rf'threshold[\s]*[:=]?\s*([\d.%]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                if '%' in value_str:
                    # 百分比转换为小数
                    return float(value_str.replace('%', '')) / 100
                else:
                    return float(value_str)

        # 默认值
        defaults = {
            "voltage": 0.05,
            "thermal": 1.0
        }
        return defaults.get(threshold_type, 0.05)

    def generate_config(self, prompt: str, skill: str = None) -> Dict[str, Any]:
        """生成配置"""
        # 检测技能
        if not skill:
            skill = self.detect_skill(prompt)

        # 基础配置
        config = {
            "skill": skill,
            "auth": {"token_file": ".cloudpss_token"},
            "model": {
                "rid": self.extract_model(prompt),
                "source": "cloud"
            },
            "output": {
                "format": self.extract_format(prompt),
                "path": "./results/",
                "prefix": skill,
                "timestamp": True
            }
        }

        # 技能特定配置
        if skill == "power_flow":
            config["algorithm"] = {
                "type": self.extract_algorithm(prompt),
                "tolerance": self.extract_tolerance(prompt),
                "max_iterations": self.extract_iterations(prompt)
            }

        elif skill == "emt_simulation":
            config["simulation"] = {
                "duration": self.extract_duration(prompt),
                "step_size": self.extract_step_size(prompt),
                "timeout": 300
            }

        elif skill == "n1_security":
            config["analysis"] = {
                "branches": [],
                "check_voltage": True,
                "check_thermal": True,
                "voltage_threshold": self.extract_threshold(prompt, "voltage"),
                "thermal_threshold": self.extract_threshold(prompt, "thermal")
            }

        elif skill == "batch_powerflow":
            # 解析多个模型
            models = self.extract_multiple_models(prompt)
            if len(models) > 1:
                config["models"] = [
                    {"rid": m, "name": m.split("/")[-1], "source": "cloud"}
                    for m in models
                ]
                del config["model"]  # 删除单模型配置

        return config

    def extract_multiple_models(self, prompt: str) -> List[str]:
        """提取多个模型（用于batch_powerflow）"""
        models = []
        # 匹配所有 IEEE数字
        matches = re.findall(r'IEEE\s*(\d+)', prompt, re.IGNORECASE)
        for num in matches:
            key = f"IEEE{num}"
            if key in self.MODEL_MAP:
                models.append(self.MODEL_MAP[key])

        return models if models else ["model/holdme/IEEE39"]

    def save_config(self, config: Dict[str, Any], output_path: str = None) -> str:
        """保存配置到文件"""
        if not output_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            skill_name = config.get("skill", "config")
            output_path = f"configs/{skill_name}_{timestamp}.yaml"

        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        return output_path


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='智能配置生成器')
    parser.add_argument('--prompt', '-p', required=True, help='用户描述')
    parser.add_argument('--skill', '-s', help='指定技能（可选，自动检测）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--preview', action='store_true', help='仅预览不保存')

    args = parser.parse_args()

    generator = SmartConfigGenerator()

    print(f"📝 输入: {args.prompt}")
    print()

    # 生成配置
    config = generator.generate_config(args.prompt, args.skill)

    print(f"🔍 检测到技能: {config['skill']}")
    print(f"🎯 模型: {config['model']['rid']}")
    print()

    # 显示配置
    print("📋 生成的配置:")
    print("-" * 50)
    yaml_str = yaml.dump(config, allow_unicode=True, sort_keys=False)
    print(yaml_str)
    print("-" * 50)

    if not args.preview:
        # 保存配置
        output_path = generator.save_config(config, args.output)
        print(f"\n✅ 配置已保存: {output_path}")
        print(f"\n运行命令:")
        print(f"  python -m cloudpss_skills run --config {output_path}")


if __name__ == "__main__":
    main()
