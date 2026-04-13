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


class ScientificFloat(float):
    """自定义浮点数类，YAML输出时保留科学计数法"""
    def __repr__(self):
        if self == 0:
            return "0.0"
        exp = int(f"{self:.0e}".split('e')[1])
        if abs(exp) >= 4:
            return f"{self:.0e}"
        return str(float(self))


def sci_float_representer(dumper, data):
    """YAML浮点数representer，科学计数法格式"""
    if data == 0:
        return dumper.represent_float(data)
    exp = int(f"{data:.0e}".split('e')[1])
    if abs(exp) >= 4:
        return dumper.represent_scalar('tag:yaml.org,2002:float', f"{data:.0e}")
    return dumper.represent_float(data)


yaml.add_representer(float, sci_float_representer)


class SmartConfigGenerator:
    """智能配置生成器"""

    # 技能关键词映射 - 48个技能
    SKILL_KEYWORDS = {
        # 仿真执行类
        "power_flow": ["潮流计算", "潮流计算", "power flow", "load flow", "稳态", "pf仿真", "潮流"],
        "emt_simulation": ["EMT", "暂态", "transient", "emtp", "电磁暂态"],
        "emt_fault_study": ["故障研究", "fault study", "短路研究", "故障分析"],
        "short_circuit": ["短路", "short circuit", "短路计算", "短路电流"],

        # N-1安全分析类
        "n1_security": ["N-1", "安全校核", "N-1筛查", "安全评估", "n1安全"],
        "n2_security": ["N-2", "双重故障", "n2安全", "双元件停运", "n2安全校核"],
        "emt_n1_screening": ["EMT N-1", "暂态N-1", "emt_n1", "暂态安全筛查"],
        "contingency_analysis": ["预想事故", "contingency", "事故分析", "故障集分析"],
        "maintenance_security": ["检修安全", "检修安全校核", "maintenance", "检修方式", "计划检修", "检修校核", "停运"],

        # 批量与扫描类
        "batch_powerflow": ["批量跑", "批量潮流", "批量运行", "多模型", "batch powerflow", "批量.*潮流"],
        "param_scan": ["参数扫描", "param scan", "敏感性", "扫描", "参数分析"],
        "fault_clearing_scan": ["故障清除", "fault clearing", "清除时间", "故障切除"],
        "fault_severity_scan": ["故障严重度", "fault severity", "严重度扫描", "故障程度"],
        "batch_task_manager": ["批处理", "batch task", "任务管理", "批量任务"],
        "config_batch_runner": ["配置批量", "config batch", "多配置运行", "配置运行器", "多个配置场景"],
        "orthogonal_sensitivity": ["正交敏感", "orthogonal", "正交分析", "DOE", "实验设计"],

        # 稳定性分析类
        "voltage_stability": ["电压稳定", "voltage stability", "电压稳定性", "静态电压稳定"],
        "transient_stability": ["暂态稳定", "transient stability", "暂态稳定性", "大扰动稳定"],
        "transient_stability_margin": ["CCT", "临界切除", "稳定裕度", "切除时间", "stability margin", "临界切除时间"],
        "small_signal_stability": ["小信号", "small signal", "小干扰", "特征值分析"],
        "frequency_response": ["频率响应", "frequency response", "频率特性", "调频"],
        "vsi_weak_bus": ["VSI", "弱母线", "weak bus", "电压稳定指标", "vsi分析"],
        "dudv_curve": ["DUDV", "电压特性", "dudv曲线", "无功电压特性"],

        # 结果处理类
        "result_compare": ["对比", "compare", "比较结果", "结果对比"],
        "visualize": ["可视化", "画图", "plot", "绘图", "我要看"],
        "waveform_export": ["波形导出", "export", "提取波形", "波形提取", "提取", "提取.*波形", "波形"],
        "hdf5_export": ["HDF5", "hdf5导出", "hdf5 export", "二进制导出"],
        "disturbance_severity": ["扰动严重度", "disturbance", "扰动分析", "故障严重度分析"],
        "compare_visualization": ["对比可视化", "compare visualization", "多场景对比", "对比图表"],
        "comtrade_export": ["COMTRADE", "comtrade导出", "标准格式导出", "暂态数据导出"],

        # 电能质量类
        "harmonic_analysis": ["谐波", "harmonic", "谐波分析", "THD"],
        "power_quality_analysis": ["电能质量", "power quality", "电能质量分析", "供电质量"],
        "reactive_compensation_design": ["无功补偿", "reactive compensation", "补偿设计", "电容器配置"],

        # 新能源分析类
        "renewable_integration": ["新能源", "SCR", "LVRT", "可再生能源", "风光", "renewable", "新能源接入", "风光接入"],

        # 模型与拓扑类
        "topology_check": ["拓扑", "topology", "检查模型", "拓扑分析"],
        "parameter_sensitivity": ["灵敏度", "sensitivity", "参数灵敏度", "灵敏度分析"],
        "auto_channel_setup": ["自动通道", "auto channel", "量测配置", "自动量测", "通道设置", "量测通道", "配置.*通道"],
        "auto_loop_breaker": ["解环", "loop breaker", "消除环路", "控制环路", "自动解环"],
        "model_parameter_extractor": ["参数提取", "parameter extractor", "模型参数", "提取参数", "参数导出"],
        "model_builder": ["建模", "构建模型", "添加元件", "修改模型", "删除元件", "model builder", "新建模型", "添加新负载", "添加新元件", "添加新"],
        "model_validator": ["验证模型", "模型验证", "model validator", "模型校验", "校验模型", "验证算例", "模型有效性"],
        "component_catalog": ["元件目录", "组件列表", "元件查询", "component catalog", "元件库", "元件列表", "所有变压器", "所有发电机", "所有负载", "列出元件", "有哪些发电机", "有哪些负载", "有哪些变压器", "列出所有", "查询.*元件"],
        "thevenin_equivalent": ["戴维南", "等值阻抗", "Thevenin", "阻抗等值", "短路容量"],
        "model_hub": ["算例中心", "模型库", "model hub", "跨服务器", "算例管理", "克隆", "同步算例", "算例同步"],

        # 分析与报告类
        "loss_analysis": ["网损", "损耗", "loss", "功率损耗", "网损分析"],
        "protection_coordination": ["保护配合", "protection coordination", "继电保护", "保护整定", "保护校验"],
        "report_generator": ["报告", "report", "生成报告", "报告生成", "导出报告", "分析报告"],

        # 流程编排类
        "study_pipeline": ["流水线", "pipeline", "流程编排", "串联执行", "study pipeline", "研究流程"]
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
        "IEEE39": "model/chenying/IEEE39",
        "IEEE3": "model/chenying/IEEE3",
        "IEEE9": "model/chenying/IEEE9",
        "IEEE14": "model/chenying/IEEE14",
        "IEEE118": "model/chenying/IEEE118"
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

        # 特殊模式优先检测（元操作：帮助、验证、向导等）
        special_patterns = [
            ("model_validator", [r"验证.*模型", r"模型.*验证"]),
            ("model_builder", [r"添加.*新.*", r"新建.*", r"建模"]),
            ("waveform_export", [r"提取.*波形", r"提取.*仿真.*波形", r"波形导出"]),
            ("visualize", [r"我要看", r"可视化.*结果"]),
            ("auto_channel_setup", [r"量测通道", r"配置.*通道"]),
            ("component_catalog", [r"查询.*元件", r"有哪些.*", r"列出所有.*元件", r"列出.*元件"]),
            ("config_batch_runner", [r"多个配置"]),
            ("maintenance_security", [r"检修.*校核", r"检修.*停运"]),
            ("report_generator", [r"生成.*报告", r"报告生成", r"分析.*报告"]),
            ("topology_check", [r"拓扑检查", r"检查.*拓扑"]),
            ("emt_n1_screening", [r"emt.*n-1", r"暂态.*n-1"]),
        ]
        for skill, patterns in special_patterns:
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return skill

        # 组合模式检测：多个关键词同时出现时优先匹配
        combined_patterns = [
            ("batch_powerflow", r"批量.*潮流"),
            ("batch_powerflow", r"批量跑.*"),
            ("batch_powerflow", r"多模型.*"),
        ]
        for skill, pattern in combined_patterns:
            if re.search(pattern, prompt_lower):
                return skill

        scores = {}
        for skill, keywords in self.SKILL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in prompt_lower)
            if score > 0:
                # Bonus: longer keyword matches are more specific
                max_kw_len = max((len(kw) for kw in keywords if kw.lower() in prompt_lower), default=0)
                scores[skill] = (score, max_kw_len)

        if not scores:
            return "power_flow"  # 默认

        return max(scores, key=lambda s: scores[s])

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
        return "model/chenying/IEEE39"

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
                    value = float(match.group(1))
                    if value > 0:
                        return value
                    # Reject negative/zero tolerance, fall through to default
                    continue
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
            rf'{threshold_type}[\s]*阈值[\s]*设成?[:为]?\s*([\d.%]+)',
            rf'{threshold_type}[\s]*阈值[\s]*[:为]?\s*([\d.%]+)',
            rf'阈值[\s]*设成?[:为]?\s*([\d.%]+)',
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
        prompt_lower = prompt.lower()

        # 检测帮助/元操作请求
        if any(kw in prompt_lower for kw in ["怎么使用", "如何使用", "help", "使用方法", "使用指南"]):
            return self._generate_help_config(prompt)
        if any(kw in prompt_lower for kw in ["验证这个配置", "配置文件", "config.yaml"]):
            return self._generate_validate_config(prompt)
        if any(kw in prompt_lower for kw in ["配置报错了", "报错", "错误", "model not found", "错误信息"]):
            return self._generate_error_help_config(prompt)
        if any(kw in prompt_lower for kw in ["创建一个新的.*配置", "配置一个", "帮我配置"]):
            # Only trigger wizard for generic "create/configure" requests, not specific skills
            if not any(sk in prompt_lower for sk in ["n-1", "n-2", "潮流", "emt", "暂态", "短路", "扫描", "安全校核", "vsi", "网损", "保护", "谐波", "拓扑", "添加新", "添加.*元件"]):
                return self._generate_wizard_config(prompt)
        if any(kw in prompt_lower for kw in ["是什么", "介绍一下", "解释"]):
            return self._generate_explain_config(prompt)

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

        elif skill == "emt_fault_study":
            fault_loc = self.extract_fault_location(prompt)
            fault_type = "single_phase" if "单相" in prompt else "three_phase"
            config["fault"] = {
                "location": fault_loc,
                "type": fault_type,
                "start_time": 0.1,
                "duration": 0.05
            }
            config["simulation"] = {
                "duration": 5.0,
                "step_size": 0.0001
            }

        elif skill == "short_circuit":
            fault_loc = self.extract_fault_location(prompt)
            fault_type = "three_phase" if "三相" in prompt else "single_phase"
            config["fault"] = {
                "bus": fault_loc,
                "type": fault_type
            }

        elif skill == "n1_security":
            config["analysis"] = {
                "branches": [],
                "check_voltage": True,
                "check_thermal": True,
                "voltage_threshold": self.extract_threshold(prompt, "voltage"),
                "thermal_threshold": self.extract_threshold(prompt, "thermal")
            }

        elif skill == "study_pipeline":
            config["pipeline"] = [
                {
                    "name": "步骤1",
                    "skill": "power_flow",
                    "config": {}
                }
            ]
            config["continue_on_failure"] = False
            config["max_workers"] = 4

        elif skill == "n2_security":
            config["analysis"] = {
                "branches": [],
                "check_voltage": True,
                "check_thermal": True,
                "voltage_min": 0.95,
                "voltage_max": 1.05,
                "thermal_limit": 1.0,
                "max_combinations": 100,
                "include_critical_pairs": True
            }

        elif skill == "transient_stability_margin":
            fault_location = self.extract_fault_location(prompt)
            config["fault_scenarios"] = [
                {
                    "location": fault_location,
                    "type": "three_phase",
                    "duration": 0.1
                }
            ]
            config["analysis"] = {
                "compute_cct": True,
                "compute_margin": True,
                "margin_baseline": 0.5,
                "max_iterations": 20,
                "cct_tolerance": 0.001
            }

        elif skill == "renewable_integration":
            renewable_type = self.extract_renewable_type(prompt)
            config["renewable"] = {
                "type": renewable_type,
                "bus": self.extract_bus_name(prompt)
            }
            config["analysis"] = {
                "scr": {"enabled": True, "threshold": 3.0},
                "voltage_variation": {"enabled": True, "tolerance": 0.05},
                "harmonic_injection": {"enabled": True, "limits": {"thd": 0.05}},
                "lvrt_compliance": {"enabled": True, "standard": "gb"},
                "stability_impact": {"enabled": True}
            }

        elif skill == "vsi_weak_bus":
            config["analysis"] = {
                "voltage_threshold": self.extract_threshold(prompt, "voltage")
            }

        elif skill == "model_builder":
            config["base_model"] = {"rid": self.extract_model(prompt)}
            config["modifications"] = []
            config.pop("model", None)
            config["output"] = {
                "save": True,
                "path": "./results/"
            }

        elif skill == "model_validator":
            config["models"] = [{"rid": self.extract_model(prompt)}]
            config.pop("model", None)
            config["validation"] = {
                "phases": ["topology", "powerflow"],
                "timeout": 300,
                "powerflow_tolerance": 1e-6,
                "emt_duration": 1.0
            }

        elif skill == "component_catalog":
            config.pop("model", None)
            config["filters"] = {}
            config["options"] = {
                "page_size": 1000,
                "include_details": True
            }

        elif skill == "thevenin_equivalent":
            config["pcc"] = {
                "bus": self.extract_bus_name(prompt)
            }
            config["equivalent"] = {
                "system_base_mva": 100.0
            }

        elif skill == "model_hub":
            config.pop("model", None)
            config["action"] = self.extract_model_hub_action(prompt)
            if any(kw in prompt.lower() for kw in ["server", "服务器"]):
                config["server"] = {}

        elif skill == "param_scan":
            component = self.extract_component_name(prompt)
            # Default component when prompt mentions generic type like "负载" without specific name
            if not component:
                if "负载" in prompt or "load" in prompt.lower():
                    component = "Load_1"
                elif "发电" in prompt or "generator" in prompt.lower():
                    component = "Generator_1"
            config["scan"] = {
                "component": component,
                "parameter": self.extract_parameter_name(prompt),
                "values": self.extract_scan_values(prompt),
                "simulation_type": "power_flow"
            }

        elif skill == "result_compare":
            config["sources"] = [
                {"job_id": "placeholder-job-1", "label": "场景1"},
                {"job_id": "placeholder-job-2", "label": "场景2"}
            ]
            config["comparison"] = {
                "channels": self.extract_channels_from_prompt(prompt)
            }

        elif skill == "visualize":
            config["source"] = {"data_file": "results/xxx.json"}
            config["visualization"] = {
                "plot_type": "bar",
                "channels": self.extract_channels_from_prompt(prompt)
            }

        elif skill == "reactive_compensation_design":
            config["vsi_input"] = {
                "target_buses": ["Bus1"]
            }

        elif skill == "waveform_export":
            config["source"] = {"job_id": "placeholder-job-xxx"}
            config["export"] = {
                "channels": self.extract_channels_from_prompt(prompt),
                "plots": []
            }

        elif skill == "auto_channel_setup":
            config["measurements"] = {
                "voltage": {"enabled": True},
                "current": {"enabled": True},
                "power": {"enabled": True},
                "frequency": {"enabled": False}
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

        elif skill == "config_batch_runner":
            config["configs"] = {"mode": "all"}

        elif skill == "compare_visualization":
            config["sources"] = [
                {"job_id": "placeholder-job-1", "label": "基态"},
                {"job_id": "placeholder-job-2", "label": "故障态"}
            ]

        elif skill == "comtrade_export":
            config["source"] = {"job_id": "placeholder-job-xxx"}

        elif skill == "orthogonal_sensitivity":
            config["parameters"] = [
                {"name": "P", "levels": [0.8, 1.0, 1.2]}
            ]
            config["target"] = {"metric": "voltage"}

        elif skill == "model_parameter_extractor":
            config["extraction"] = {
                "component_types": ["load", "generator"]
            }

        elif skill == "maintenance_security":
            component = self.extract_component_name(prompt)
            config["maintenance"] = {
                "branch_id": component if component else "placeholder-branch",
                "check_voltage": True,
                "check_thermal": True
            }

        elif skill == "report_generator":
            config["report"] = {
                "title": "仿真分析报告",
                "skills": ["power_flow"],
                "format": "docx"
            }

        elif skill == "loss_analysis":
            config["analysis"] = {
                "target_branches": []
            }

        elif skill == "protection_coordination":
            config["analysis"] = {
                "voltage_level": self.extract_voltage_level(prompt)
            }

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

        return models if models else ["model/chenying/IEEE39"]

    def extract_fault_location(self, prompt: str) -> str:
        """提取故障位置"""
        # 匹配 Bus数字 模式
        match = re.search(r'Bus\s*(\d+)', prompt, re.IGNORECASE)
        if match:
            return f"Bus{match.group(1)}"
        # 匹配母线关键词
        match = re.search(r'母线\s*(\S+)', prompt)
        if match:
            return match.group(1)
        return "bus8"  # 默认

    def extract_renewable_type(self, prompt: str) -> str:
        """提取新能源类型"""
        if any(kw in prompt for kw in ["风电", "wind", "风机"]):
            return "wind"
        if any(kw in prompt for kw in ["光伏", "pv", "solar"]):
            return "pv"
        return "pv"  # 默认

    def extract_bus_name(self, prompt: str) -> str:
        """提取母线名称"""
        match = re.search(r'Bus\s*(\d+)', prompt, re.IGNORECASE)
        if match:
            return f"Bus{match.group(1)}"
        match = re.search(r'母线[\s_]*(\S+)', prompt)
        if match:
            return match.group(1)
        return "bus8"  # 默认

    def extract_model_hub_action(self, prompt: str) -> str:
        """提取model_hub操作类型"""
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in ["克隆", "clone", "同步", "sync"]):
            return "clone"
        if any(kw in prompt_lower for kw in ["列出", "list", "查看", "查询"]):
            return "list_models"
        if any(kw in prompt_lower for kw in ["状态", "status", "信息"]):
            return "status"
        if any(kw in prompt_lower for kw in ["初始化", "init", "注册"]):
            return "init"
        if any(kw in prompt_lower for kw in ["推送", "push", "上传"]):
            return "push"
        if any(kw in prompt_lower for kw in ["拉取", "pull", "下载"]):
            return "pull"
        return "status"  # 默认

    def extract_component_name(self, prompt: str) -> str:
        """提取元件名称"""
        # 匹配 Load_xxx, Gen_xxx 等模式
        match = re.search(r'(Load_\w+|Gen_\w+|Generator_\w+|Bus\d+)', prompt, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def extract_parameter_name(self, prompt: str) -> str:
        """提取参数名称"""
        param_map = {
            "有功": "P", "p": "P", "P": "P",
            "无功": "Q", "q": "Q", "Q": "Q",
            "电压": "Vset", "vset": "Vset",
        }
        for cn, en in param_map.items():
            if cn in prompt:
                return en
        return "P"

    def extract_scan_values(self, prompt: str) -> list:
        """提取扫描值列表"""
        # 匹配百分比模式：从10%到100%，步长10%
        pct_match = re.search(r'从\s*(\d+)%\s*到\s*(\d+)%.*?步长\s*(\d+)%', prompt)
        if pct_match:
            start = int(pct_match.group(1)) / 100
            end = int(pct_match.group(2)) / 100
            step = int(pct_match.group(3)) / 100
            vals = []
            v = start
            while v <= end + 0.001:
                vals.append(round(v, 4))
                v += step
            return vals

        # 匹配数字列表
        match = re.search(r'从\s*(\d+)\s*到\s*(\d+)', prompt)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            step_match = re.search(r'每隔\s*(\d+)', prompt)
            step = int(step_match.group(1)) if step_match else 1
            return list(range(start, end + 1, step))

        return [10, 20, 30, 40, 50]  # 默认

    def extract_channels_from_prompt(self, prompt: str) -> list:
        """从提示中提取通道名称"""
        channels = []
        # 三相电压模式: BusX_Va, BusX_Vb, BusX_Vc
        bus_match = re.search(r'Bus(\d+).*电压', prompt, re.IGNORECASE)
        if bus_match:
            bus_num = bus_match.group(1)
            if "三相" in prompt:
                channels = [f"Bus{bus_num}_Va", f"Bus{bus_num}_Vb", f"Bus{bus_num}_Vc"]
            else:
                channels = [f"Bus{bus_num}_Va"]
        # 线路电流模式: LineX-Y_Ia, LineX-Y_Ib, LineX-Y_Ic
        line_match = re.search(r'Line(\d+-\d+).*电流', prompt, re.IGNORECASE)
        if line_match:
            line_id = line_match.group(1)
            channels = [f"Line{line_id}_Ia", f"Line{line_id}_Ib", f"Line{line_id}_Ic"]
        return channels

    def extract_voltage_level(self, prompt: str) -> str:
        """提取电压等级"""
        match = re.search(r'(\d+kV)', prompt)
        if match:
            return match.group(1)
        return "110kV"  # 默认

    def _generate_help_config(self, prompt: str) -> Dict[str, Any]:
        """生成帮助配置"""
        help_text = "可用技能列表：\n"
        help_text += "- power_flow: 潮流计算\n"
        help_text += "- emt_simulation: EMT暂态仿真\n"
        help_text += "- n1_security: N-1安全校核\n"
        help_text += "- param_scan: 参数扫描\n"
        help_text += "- short_circuit: 短路计算\n"
        help_text += "- vsi_weak_bus: VSI弱母线分析\n"
        help_text += "- waveform_export: 波形导出\n"
        help_text += "- visualize: 结果可视化\n"
        help_text += "- component_catalog: 元件查询\n"
        help_text += "- model_builder: 模型构建\n"
        help_text += "- report_generator: 报告生成\n"
        help_text += "\n使用方法: 描述您的需求，如'帮我跑IEEE39潮流计算'"
        return {"help": help_text, "available_skills": ["power_flow", "emt_simulation", "n1_security", "param_scan", "visualize", "component_catalog"]}

    def _generate_validate_config(self, prompt: str) -> Dict[str, Any]:
        """生成验证配置"""
        return {"action": "validate", "message": "正在验证配置...", "config_file": "config.yaml"}

    def _generate_error_help_config(self, prompt: str) -> Dict[str, Any]:
        """生成错误帮助配置"""
        return {
            "action": "error_diagnosis",
            "message": "模型未找到错误解决步骤：",
            "steps": [
                "1. 检查模型RID是否正确",
                "2. 确认有权限访问该模型",
                "3. 使用已知模型: model/holdme/IEEE39 或 model/holdme/IEEE3"
            ]
        }

    def _generate_wizard_config(self, prompt: str) -> Dict[str, Any]:
        """生成向导配置"""
        return {
            "action": "wizard",
            "message": "启动交互式配置向导",
            "步骤": [
                "1. 选择技能类型",
                "2. 选择模型",
                "3. 设置参数",
                "4. 生成配置"
            ]
        }

    def _generate_explain_config(self, prompt: str) -> Dict[str, Any]:
        """生成解释配置"""
        prompt_lower = prompt.lower()
        if "emt" in prompt_lower or "暂态" in prompt_lower:
            return {
                "action": "explain",
                "skill": "emt_simulation",
                "description": "EMT（Electromagnetic Transient）暂态仿真 - 用于分析电力系统中的电磁暂态过程，如短路、开关操作等",
                "key_parameters": ["duration: 仿真时长(秒)", "step_size: 积分步长(秒)"]
            }
        return {"action": "explain", "description": "请指定需要了解的具体技能"}

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
