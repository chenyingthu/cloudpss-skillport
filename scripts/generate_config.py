#!/usr/bin/env python3
"""
生成CloudPSS技能配置文件

根据用户输入自动生成标准YAML配置
"""

import sys
import yaml
from datetime import datetime
from pathlib import Path

# 技能默认配置模板
DEFAULT_CONFIGS = {
    "power_flow": {
        "skill": "power_flow",
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "model/holdme/IEEE39", "source": "cloud"},
        "algorithm": {
            "type": "newton_raphson",
            "tolerance": 1e-6,
            "max_iterations": 100
        },
        "output": {
            "format": "json",
            "path": "./results/",
            "prefix": "power_flow",
            "timestamp": True
        }
    },
    "emt_simulation": {
        "skill": "emt_simulation",
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "model/holdme/IEEE3", "source": "cloud"},
        "simulation": {
            "duration": 5.0,
            "step_size": 0.0001,
            "timeout": 300
        },
        "output": {
            "format": "csv",
            "path": "./results/",
            "prefix": "emt_output",
            "timestamp": True
        }
    },
    "batch_powerflow": {
        "skill": "batch_powerflow",
        "auth": {"token_file": ".cloudpss_token"},
        "models": [
            {"rid": "model/holdme/IEEE39", "name": "IEEE39", "source": "cloud"}
        ],
        "output": {
            "format": "json",
            "path": "./results/",
            "prefix": "batch_pf",
            "timestamp": True
        }
    },
    "n1_security": {
        "skill": "n1_security",
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "model/holdme/IEEE39", "source": "cloud"},
        "analysis": {
            "branches": [],
            "check_voltage": True,
            "check_thermal": True,
            "voltage_threshold": 0.05,
            "thermal_threshold": 1.0
        },
        "output": {
            "format": "json",
            "path": "./results/",
            "prefix": "n1_security",
            "timestamp": True
        }
    },
    "param_scan": {
        "skill": "param_scan",
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "model/holdme/IEEE3", "source": "cloud"},
        "scan": {
            "component": "",
            "parameter": "",
            "values": [],
            "simulation_type": "power_flow"
        },
        "output": {
            "format": "json",
            "path": "./results/",
            "prefix": "param_scan",
            "timestamp": True
        }
    }
}

def generate_config(skill_name, model_rid=None, custom_params=None, output_dir="configs"):
    """
    生成技能配置文件

    Args:
        skill_name: 技能名称（power_flow, emt_simulation等）
        model_rid: 自定义模型RID
        custom_params: 自定义参数字典
        output_dir: 输出目录

    Returns:
        生成的配置文件路径
    """
    if skill_name not in DEFAULT_CONFIGS:
        raise ValueError(f"未知技能: {skill_name}。可用: {list(DEFAULT_CONFIGS.keys())}")

    # 获取默认配置
    config = DEFAULT_CONFIGS[skill_name].copy()

    # 更新模型
    if model_rid:
        if "model" in config:
            config["model"]["rid"] = model_rid
        elif "models" in config:
            config["models"][0]["rid"] = model_rid

    # 应用自定义参数
    if custom_params:
        config.update(custom_params)

    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{skill_name}_{timestamp}.yaml"
    filepath = output_path / filename

    # 写入YAML
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    return str(filepath)

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python generate_config.py <skill_name> [model_rid] [output_dir]")
        print(f"可用技能: {', '.join(DEFAULT_CONFIGS.keys())}")
        sys.exit(1)

    skill_name = sys.argv[1]
    model_rid = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "configs"

    try:
        filepath = generate_config(skill_name, model_rid, output_dir=output_dir)
        print(f"配置已生成: {filepath}")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
