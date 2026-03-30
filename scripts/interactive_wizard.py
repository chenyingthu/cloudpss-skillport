#!/usr/bin/env python3
"""
交互式配置向导

引导用户逐步完成配置生成。
解决 Issue #008: 缺少配置向导
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List


class InteractiveWizard:
    """交互式配置向导"""

    # 技能信息 - 37个技能
    SKILLS = {
        # ========== 仿真执行类 ==========
        "power_flow": {
            "name": "潮流计算",
            "description": "计算系统稳态潮流分布",
            "difficulty": "简单",
            "time": "约5-10秒"
        },
        "emt_simulation": {
            "name": "EMT暂态仿真",
            "description": "电磁暂态过程仿真",
            "difficulty": "中等",
            "time": "约30-120秒"
        },
        "emt_fault_study": {
            "name": "EMT故障研究",
            "description": "EMT故障场景仿真分析",
            "difficulty": "中等",
            "time": "约60-180秒"
        },
        "short_circuit": {
            "name": "短路电流计算",
            "description": "计算系统短路电流",
            "difficulty": "简单",
            "time": "约5-10秒"
        },

        # ========== N-1安全分析类 ==========
        "n1_security": {
            "name": "N-1安全校核",
            "description": "停运支路检查系统稳定性",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "emt_n1_screening": {
            "name": "EMT N-1安全筛查",
            "description": "EMT暂态N-1安全分析",
            "difficulty": "较难",
            "time": "约10-30分钟"
        },
        "contingency_analysis": {
            "name": "预想事故分析",
            "description": "多故障场景分析",
            "difficulty": "中等",
            "time": "约5-15分钟"
        },
        "maintenance_security": {
            "name": "检修方式安全校核",
            "description": "检修期间系统安全分析",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },

        # ========== 批量与扫描类 ==========
        "batch_powerflow": {
            "name": "批量潮流计算",
            "description": "对多个模型批量运行潮流",
            "difficulty": "中等",
            "time": "取决于模型数量"
        },
        "param_scan": {
            "name": "参数扫描",
            "description": "批量改变参数运行多次仿真",
            "difficulty": "较难",
            "time": "取决于参数点数量"
        },
        "fault_clearing_scan": {
            "name": "故障清除时间扫描",
            "description": "扫描故障清除时间影响",
            "difficulty": "较难",
            "time": "约10-30分钟"
        },
        "fault_severity_scan": {
            "name": "故障严重度扫描",
            "description": "扫描不同故障严重程度",
            "difficulty": "较难",
            "time": "约10-30分钟"
        },
        "batch_task_manager": {
            "name": "批处理任务管理",
            "description": "管理和执行批量任务",
            "difficulty": "中等",
            "time": "取决于任务数量"
        },
        "config_batch_runner": {
            "name": "配置批量运行器",
            "description": "对同一模型批量运行多个配置场景",
            "difficulty": "中等",
            "time": "取决于配置数量"
        },
        "orthogonal_sensitivity": {
            "name": "正交敏感性分析",
            "description": "基于正交表的参数敏感性分析",
            "difficulty": "较难",
            "time": "约10-30分钟"
        },

        # ========== 稳定性分析类 ==========
        "voltage_stability": {
            "name": "电压稳定分析",
            "description": "分析系统电压稳定性",
            "difficulty": "较难",
            "time": "约5-10分钟"
        },
        "transient_stability": {
            "name": "暂态稳定分析",
            "description": "分析大扰动后系统稳定性",
            "difficulty": "较难",
            "time": "约10-20分钟"
        },
        "small_signal_stability": {
            "name": "小信号稳定分析",
            "description": "特征值分析小干扰稳定性",
            "difficulty": "较难",
            "time": "约5-10分钟"
        },
        "frequency_response": {
            "name": "频率响应分析",
            "description": "分析系统频率响应特性",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "vsi_weak_bus": {
            "name": "VSI弱母线分析",
            "description": "识别系统中薄弱母线",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "dudv_curve": {
            "name": "DUDV曲线生成",
            "description": "生成电压特性曲线",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },

        # ========== 结果处理类 ==========
        "result_compare": {
            "name": "结果对比",
            "description": "对比两次仿真结果",
            "difficulty": "简单",
            "time": "立即"
        },
        "visualize": {
            "name": "可视化",
            "description": "绘制波形和结果图表",
            "difficulty": "简单",
            "time": "立即"
        },
        "waveform_export": {
            "name": "波形导出",
            "description": "从仿真结果导出波形数据",
            "difficulty": "简单",
            "time": "立即"
        },
        "hdf5_export": {
            "name": "HDF5导出",
            "description": "导出为HDF5格式数据",
            "difficulty": "简单",
            "time": "立即"
        },
        "disturbance_severity": {
            "name": "扰动严重度分析",
            "description": "分析扰动严重程度",
            "difficulty": "中等",
            "time": "约1-2分钟"
        },
        "compare_visualization": {
            "name": "对比可视化",
            "description": "生成多场景仿真结果的对比图表",
            "difficulty": "简单",
            "time": "立即"
        },
        "comtrade_export": {
            "name": "COMTRADE导出",
            "description": "将EMT仿真结果导出为COMTRADE标准格式",
            "difficulty": "简单",
            "time": "立即"
        },

        # ========== 电能质量类 ==========
        "harmonic_analysis": {
            "name": "谐波分析",
            "description": "分析系统谐波含量",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "power_quality_analysis": {
            "name": "电能质量分析",
            "description": "综合电能质量评估",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "reactive_compensation_design": {
            "name": "无功补偿设计",
            "description": "设计无功补偿方案",
            "difficulty": "较难",
            "time": "约5-10分钟"
        },

        # ========== 模型与拓扑类 ==========
        "ieee3_prep": {
            "name": "IEEE3模型准备",
            "description": "准备IEEE3模型的EMT仿真",
            "difficulty": "简单",
            "time": "立即"
        },
        "topology_check": {
            "name": "拓扑检查",
            "description": "验证模型拓扑完整性",
            "difficulty": "简单",
            "time": "立即"
        },
        "parameter_sensitivity": {
            "name": "参数灵敏度分析",
            "description": "分析参数变化影响",
            "difficulty": "中等",
            "time": "约5-10分钟"
        },
        "auto_channel_setup": {
            "name": "自动量测配置",
            "description": "自动批量配置EMT仿真输出通道",
            "difficulty": "简单",
            "time": "立即"
        },
        "auto_loop_breaker": {
            "name": "模型自动解环",
            "description": "检测并自动消除模型中的控制环路",
            "difficulty": "中等",
            "time": "约1-2分钟"
        },
        "model_parameter_extractor": {
            "name": "模型参数提取器",
            "description": "提取电力系统模型中的元件参数",
            "difficulty": "简单",
            "time": "立即"
        }
    }

    # 默认模型
    DEFAULT_MODELS = {
        "1": ("model/holdme/IEEE39", "IEEE39 (39节点，适合潮流和N-1)"),
        "2": ("model/holdme/IEEE3", "IEEE3 (3节点，适合EMT)"),
        "3": ("model/holdme/IEEE9", "IEEE9 (9节点)"),
        "4": ("custom", "自定义模型")
    }

    def __init__(self):
        self.config = {}
        self.answers = {}

    def print_header(self):
        """打印向导标题"""
        print("\n" + "=" * 70)
        print("   CloudPSS 技能配置向导")
        print("   本向导将帮助您生成仿真配置文件")
        print("=" * 70 + "\n")

    def ask(self, question: str, options: List[tuple] = None, default: str = None) -> str:
        """提问并获取回答"""
        print(f"\n❓ {question}")

        if options:
            print("\n选项:")
            for key, desc in options:
                marker = " (默认)" if key == default else ""
                print(f"  [{key}] {desc}{marker}")
            print()

        while True:
            if default:
                prompt = f"请输入选择 (默认: {default}): "
            else:
                prompt = "请输入: "

            answer = input(prompt).strip()

            if not answer and default:
                return default

            if not answer:
                print("⚠️  请输入有效选择")
                continue

            if options:
                valid_keys = [opt[0] for opt in options]
                if answer not in valid_keys:
                    print(f"⚠️  无效选择，请从 {valid_keys} 中选择")
                    continue

            return answer

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """询问是/否"""
        default_str = "Y/n" if default else "y/N"
        answer = input(f"\n❓ {question} [{default_str}]: ").strip().lower()

        if not answer:
            return default

        return answer in ['y', 'yes', '是', '1']

    def ask_number(self, question: str, default: float = None, min_val: float = None, max_val: float = None) -> float:
        """询问数字"""
        while True:
            if default is not None:
                prompt = f"\n❓ {question} (默认: {default}): "
            else:
                prompt = f"\n❓ {question}: "

            answer = input(prompt).strip()

            if not answer and default is not None:
                return default

            try:
                value = float(answer)

                if min_val is not None and value < min_val:
                    print(f"⚠️  值不能小于 {min_val}")
                    continue

                if max_val is not None and value > max_val:
                    print(f"⚠️  值不能大于 {max_val}")
                    continue

                return value

            except ValueError:
                print("⚠️  请输入有效数字")

    def run(self):
        """运行向导"""
        self.print_header()

        print("🎓 本向导将引导您完成配置生成。")
        print("对于每个问题，您可以选择默认选项或直接输入。\n")

        # Step 1: 选择技能
        self.step_select_skill()

        # Step 2: 选择模型
        self.step_select_model()

        # Step 3: 技能特定配置
        skill = self.answers.get("skill")
        if skill == "power_flow":
            self.step_power_flow_config()
        elif skill == "emt_simulation":
            self.step_emt_config()
        elif skill == "n1_security":
            self.step_n1_config()
        elif skill == "param_scan":
            self.step_param_scan_config()
        elif skill == "batch_powerflow":
            self.step_batch_config()

        # Step 4: 输出配置
        self.step_output_config()

        # Step 5: 保存配置
        self.step_save_config()

    def step_select_skill(self):
        """步骤1: 选择技能"""
        print("\n" + "-" * 70)
        print("步骤 1/5: 选择技能类型")
        print("-" * 70)

        options = []
        for i, (key, info) in enumerate(self.SKILLS.items(), 1):
            options.append((str(i), f"{info['name']} - {info['description']} ({info['difficulty']}, {info['time']})"))

        answer = self.ask("您想执行哪种类型的仿真？", options, "1")

        skill_key = list(self.SKILLS.keys())[int(answer) - 1]
        self.answers["skill"] = skill_key

        print(f"\n✅ 已选择: {self.SKILLS[skill_key]['name']}")

    def step_select_model(self):
        """步骤2: 选择模型"""
        print("\n" + "-" * 70)
        print("步骤 2/5: 选择仿真模型")
        print("-" * 70)

        options = [
            ("1", "IEEE39 (39节点，适合潮流和N-1校核)"),
            ("2", "IEEE3 (3节点，适合EMT暂态仿真)"),
            ("3", "IEEE9 (9节点系统)"),
            ("4", "自定义模型")
        ]

        answer = self.ask("请选择模型:", options, "1")

        if answer == "4":
            custom_model = input("\n请输入模型RID (格式: model/owner/name): ").strip()
            self.answers["model_rid"] = custom_model
        else:
            rid, desc = self.DEFAULT_MODELS[answer]
            self.answers["model_rid"] = rid
            print(f"\n✅ 已选择: {desc}")

    def step_power_flow_config(self):
        """潮流计算特定配置"""
        print("\n" + "-" * 70)
        print("步骤 3/5: 潮流计算配置")
        print("-" * 70)

        # 算法选择
        algo_options = [
            ("1", "Newton-Raphson (牛顿法，推荐)"),
            ("2", "Fast Decoupled (快速分解法)")
        ]
        algo = self.ask("选择求解算法:", algo_options, "1")
        self.answers["algorithm"] = "newton_raphson" if algo == "1" else "fast_decoupled"

        # 收敛精度
        tolerance = self.ask_number(
            "收敛精度 (例如: 1e-6=0.000001，越小越精确)",
            default=1e-6
        )
        self.answers["tolerance"] = tolerance

        # 最大迭代
        max_iter = self.ask_number(
            "最大迭代次数",
            default=100,
            min_val=10,
            max_val=500
        )
        self.answers["max_iterations"] = int(max_iter)

        print("\n✅ 潮流计算配置完成")

    def step_emt_config(self):
        """EMT仿真特定配置"""
        print("\n" + "-" * 70)
        print("步骤 3/5: EMT暂态仿真配置")
        print("-" * 70)

        # 仿真时长
        duration = self.ask_number(
            "仿真时长 (秒)",
            default=5.0,
            min_val=0.1,
            max_val=100.0
        )
        self.answers["duration"] = duration

        # 积分步长
        step_size = self.ask_number(
            "积分步长 (秒，越小精度越高但越慢)",
            default=0.0001,
            min_val=0.00001,
            max_val=0.001
        )
        self.answers["step_size"] = step_size

        # 超时时间
        timeout = self.ask_number(
            "最大等待时间 (秒)",
            default=300,
            min_val=60,
            max_val=600
        )
        self.answers["timeout"] = int(timeout)

        print("\n✅ EMT仿真配置完成")

    def step_n1_config(self):
        """N-1校核特定配置"""
        print("\n" + "-" * 70)
        print("步骤 3/5: N-1安全校核配置")
        print("-" * 70)

        # 检查项目
        self.answers["check_voltage"] = self.ask_yes_no("检查电压越限？", True)
        self.answers["check_thermal"] = self.ask_yes_no("检查热稳定？", True)

        # 电压阈值
        if self.answers["check_voltage"]:
            threshold = self.ask_number(
                "电压越限阈值 (%，例如: 5表示±5%)",
                default=5.0,
                min_val=1.0,
                max_val=20.0
            )
            self.answers["voltage_threshold"] = threshold / 100

        print("\n✅ N-1校核配置完成")

    def step_param_scan_config(self):
        """参数扫描特定配置"""
        print("\n" + "-" * 70)
        print("步骤 3/5: 参数扫描配置")
        print("-" * 70)

        print("\n⚠️  参数扫描需要指定：")
        print("  1. 目标元件（如：Load_1）")
        print("  2. 目标参数（如：P、Q、Vset）")
        print("  3. 参数值范围（如：[10, 20, 30]）")

        # 元件
        component = input("\n请输入元件ID (如: Load_1): ").strip()
        self.answers["component"] = component

        # 参数
        param_options = [
            ("1", "P (有功功率)"),
            ("2", "Q (无功功率)"),
            ("3", "Vset (电压设定值)")
        ]
        param = self.ask("选择要扫描的参数:", param_options, "1")
        param_map = {"1": "P", "2": "Q", "3": "Vset"}
        self.answers["parameter"] = param_map[param]

        # 值范围
        values_str = input("\n请输入参数值范围 (用逗号分隔，如: 10,20,30,40,50): ").strip()
        values = [float(v.strip()) for v in values_str.split(",")]
        self.answers["values"] = values

        # 仿真类型
        sim_options = [
            ("1", "潮流计算 (较快)"),
            ("2", "EMT仿真 (较慢)")
        ]
        sim_type = self.ask("选择仿真类型:", sim_options, "1")
        self.answers["simulation_type"] = "power_flow" if sim_type == "1" else "emt"

        print("\n✅ 参数扫描配置完成")

    def step_batch_config(self):
        """批量潮流配置"""
        print("\n" + "-" * 70)
        print("步骤 3/5: 批量潮流配置")
        print("-" * 70)

        print("\n📋 默认将对以下模型运行潮流：")
        print("  - IEEE39")
        print("  - IEEE3")

        if self.ask_yes_no("添加更多模型？"):
            custom_models = input("请输入其他模型RID（用逗号分隔）: ").strip()
            self.answers["additional_models"] = custom_models

        print("\n✅ 批量潮流配置完成")

    def step_output_config(self):
        """步骤4: 输出配置"""
        print("\n" + "-" * 70)
        print("步骤 4/5: 输出配置")
        print("-" * 70)

        # 输出格式
        format_options = [
            ("1", "JSON (结构化数据)"),
            ("2", "CSV (表格数据)"),
            ("3", "YAML (可读配置)")
        ]
        fmt = self.ask("选择输出格式:", format_options, "1")
        format_map = {"1": "json", "2": "csv", "3": "yaml"}
        self.answers["output_format"] = format_map[fmt]

        # 输出目录
        output_dir = input("\n输出目录 (默认: ./results/): ").strip()
        if not output_dir:
            output_dir = "./results/"
        self.answers["output_path"] = output_dir

        # 时间戳
        self.answers["use_timestamp"] = self.ask_yes_no("在文件名中添加时间戳？", True)

        print("\n✅ 输出配置完成")

    def step_save_config(self):
        """步骤5: 保存配置"""
        print("\n" + "-" * 70)
        print("步骤 5/5: 生成配置文件")
        print("-" * 70)

        # 构建配置字典
        config = self._build_config()

        # 显示预览
        print("\n📋 配置预览:")
        print("-" * 70)
        yaml_str = yaml.dump(config, allow_unicode=True, sort_keys=False)
        print(yaml_str)
        print("-" * 70)

        # 保存
        if self.ask_yes_no("保存此配置？", True):
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            skill_name = self.answers.get("skill", "config")
            filename = f"configs/{skill_name}_{timestamp}.yaml"

            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(yaml_str)

            print(f"\n✅ 配置已保存: {filename}")
            print(f"\n🚀 运行命令:")
            print(f"  python -m cloudpss_skills run --config {filename}")

            if self.ask_yes_no("立即运行？"):
                print("\n正在运行...")
                import subprocess
                subprocess.run([
                    sys.executable, "-m", "cloudpss_skills",
                    "run", "--config", filename
                ])

    def _build_config(self) -> Dict:
        """构建配置字典"""
        skill = self.answers.get("skill")

        config = {
            "skill": skill,
            "auth": {"token_file": ".cloudpss_token"},
            "model": {
                "rid": self.answers.get("model_rid", "model/holdme/IEEE39"),
                "source": "cloud"
            },
            "output": {
                "format": self.answers.get("output_format", "json"),
                "path": self.answers.get("output_path", "./results/"),
                "prefix": skill,
                "timestamp": self.answers.get("use_timestamp", True)
            }
        }

        # 技能特定配置
        if skill == "power_flow":
            config["algorithm"] = {
                "type": self.answers.get("algorithm", "newton_raphson"),
                "tolerance": self.answers.get("tolerance", 1e-6),
                "max_iterations": self.answers.get("max_iterations", 100)
            }

        elif skill == "emt_simulation":
            config["simulation"] = {
                "duration": self.answers.get("duration", 5.0),
                "step_size": self.answers.get("step_size", 0.0001),
                "timeout": self.answers.get("timeout", 300)
            }

        elif skill == "n1_security":
            config["analysis"] = {
                "branches": [],
                "check_voltage": self.answers.get("check_voltage", True),
                "check_thermal": self.answers.get("check_thermal", True),
                "voltage_threshold": self.answers.get("voltage_threshold", 0.05),
                "thermal_threshold": 1.0
            }

        elif skill == "param_scan":
            config["scan"] = {
                "component": self.answers.get("component", ""),
                "parameter": self.answers.get("parameter", "P"),
                "values": self.answers.get("values", []),
                "simulation_type": self.answers.get("simulation_type", "power_flow")
            }

        elif skill == "batch_powerflow":
            models = [
                {"rid": "model/holdme/IEEE39", "name": "IEEE39", "source": "cloud"},
                {"rid": "model/holdme/IEEE3", "name": "IEEE3", "source": "cloud"}
            ]

            if "additional_models" in self.answers:
                for i, rid in enumerate(self.answers["additional_models"].split(","), 3):
                    rid = rid.strip()
                    models.append({"rid": rid, "name": f"Model{i}", "source": "cloud"})

            config["models"] = models
            del config["model"]  # 批量使用 models

        return config


def main():
    """命令行入口"""
    print("CloudPSS 技能配置向导 v2.0")
    print("=" * 70)

    wizard = InteractiveWizard()
    wizard.run()

    print("\n" + "=" * 70)
    print("向导结束。如需重新运行，请输入:")
    print("  python cloudpss-sim-v2/scripts/interactive_wizard.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
