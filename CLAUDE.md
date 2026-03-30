# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CloudPSS Sim Skill v2.0** - A Claude Code skill for power system simulation using natural language. This project provides intelligent configuration generation and execution for CloudPSS power system simulations (潮流计算, EMT暂态仿真, N-1安全校核, etc.).

**Language**: Python 3.8+
**Key Dependency**: Requires `cloudpss-toolkit` to be installed separately (see below)

## Critical Setup Requirements

### 1. Install cloudpss-toolkit First (Required)

This project depends on `cloudpss-toolkit` which must be installed **before** using this skill:

```bash
# Clone and setup toolkit (must be done first)
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit.git
cd cloudpss-toolkit
pip install -e .

# Then use this skill project
cd /path/to/cloudpss-sim-skill
# Toolkit is installed as a package, no PYTHONPATH needed
```

### 2. Configure CloudPSS Token

```bash
# Get token from https://www.cloudpss.net → 个人中心 → API Token
echo "your_token_here" > /path/to/project/.cloudpss_token
```

## Common Development Commands

### CLI via cloudpss-toolkit

```bash
# List all 37 available skills
python -m cloudpss_skills list

# Initialize a skill configuration
python -m cloudpss_skills init power_flow --output configs/pf.yaml

# Run a skill with config
python -m cloudpss_skills run --config configs/power_flow_xxx.yaml
```

### Generate Configuration from Natural Language
```bash
python scripts/smart_config.py "帮我跑IEEE39潮流计算，收敛精度1e-8"
python scripts/smart_config.py "对IEEE3做EMT仿真5秒钟" --output configs/emt.yaml
python scripts/smart_config.py "VSI弱母线分析" --output configs/vsi.yaml
python scripts/smart_config.py "无功补偿设计" --output configs/compensation.yaml
```

### Validate Configuration
```bash
python scripts/friendly_validator.py -c configs/power_flow_xxx.yaml
```

### Query Model Components
```bash
python scripts/component_mapper.py --model model/holdme/IEEE39 --type Load
python scripts/component_mapper.py --model model/holdme/IEEE3 --type Generator
```

### Infer Channel Names
```bash
python scripts/channel_helper.py -p "Bus7的三相电压"
python scripts/channel_helper.py --node Bus1 --type three_phase_voltage
```

### Interactive Configuration Wizard
```bash
python scripts/interactive_wizard.py
```

### Spell Correction / Fuzzy Matching
```bash
python scripts/fuzzy_matcher.py "n1security"  # Suggests: n1_security
python scripts/fuzzy_matcher.py "powerflow"   # Suggests: power_flow
python scripts/fuzzy_matcher.py "vsi"         # Suggests: vsi_weak_bus
```

### Run Examples from cloudpss-toolkit
```bash
# Basic examples
python /path/to/cloudpss-toolkit/examples/simulation/run_powerflow.py
python /path/to/cloudpss-toolkit/examples/simulation/run_emt_simulation.py

# Analysis examples
python /path/to/cloudpss-toolkit/examples/analysis/powerflow_n1_screening_example.py
python /path/to/cloudpss-toolkit/examples/analysis/emt_fault_study_example.py
```

## Architecture

### Configuration-Driven Workflow

The skill follows a **YAML configuration → execution** pattern:

1. **Natural Language Input** → `smart_config.py` parses parameters
2. **Component Discovery** → `component_mapper.py` queries model topology
3. **Channel Inference** → `channel_helper.py` infers waveform channel names
4. **YAML Generation** → Config saved to `configs/`
5. **Validation** → `friendly_validator.py` checks schema
6. **Execution** → `cloudpss_skills run` executes via cloudpss-toolkit

### Key Scripts and Responsibilities

| Script | Purpose |
|--------|---------|
| `smart_config.py` | Natural language → YAML config. Extracts: algorithm type, tolerance, iterations, output format |
| `component_mapper.py` | Query CloudPSS models for component IDs by type (Load, Generator, Bus, etc.) |
| `channel_helper.py` | Infer waveform channel names from descriptions like "Bus7的三相电压" → `["Bus7_Va", "Bus7_Vb", "Bus7_Vc"]` |
| `fuzzy_matcher.py` | Spell correction: "pf" → "power_flow", "emt" → "emt_simulation", "vsi" → "vsi_weak_bus" |
| `friendly_validator.py` | Schema validation with human-friendly error messages |
| `interactive_wizard.py` | Step-by-step CLI for complex configurations |
| `generate_config.py` | Basic config template generator |

### Supported Simulation Types (37 Skills)

#### 仿真执行类
- `power_flow` - 牛顿-拉夫逊潮流计算 (aliases: pf, 潮流, load flow)
- `emt_simulation` - EMT暂态仿真 (aliases: emt, 暂态, transient)
- `emt_fault_study` - EMT故障研究 (aliases: fault_study, 故障研究)
- `short_circuit` - 短路电流计算 (aliases: short_circuit, 短路)

#### N-1安全分析类
- `n1_security` - N-1安全校核 (aliases: n1, 安全校核, 检修)
- `emt_n1_screening` - EMT N-1安全筛查 (aliases: emt_n1, emt安全筛查)
- `contingency_analysis` - 预想事故分析 (aliases: contingency, 预想事故)
- `maintenance_security` - 检修方式安全校核 (aliases: maintenance, 检修安全)

#### 批量与扫描类
- `batch_powerflow` - 批量潮流计算 (aliases: batch, 批量)
- `param_scan` - 参数扫描分析 (aliases: scan, 扫描, 参数扫描)
- `fault_clearing_scan` - 故障清除时间扫描 (aliases: fault_clearing, 故障清除)
- `fault_severity_scan` - 故障严重度扫描 (aliases: severity_scan, 严重度)
- `batch_task_manager` - 批处理任务管理 (aliases: batch_manager, 批处理)
- `config_batch_runner` - 配置批量运行器 (aliases: config_batch, 配置批量) - 多配置场景批量运行
- `orthogonal_sensitivity` - 正交敏感性分析 (aliases: orthogonal, DOE) - 基于正交表的敏感性分析

#### 稳定性分析类
- `voltage_stability` - 电压稳定分析 (aliases: voltage_stab, 电压稳定)
- `transient_stability` - 暂态稳定分析 (aliases: transient_stab, 暂态稳定)
- `small_signal_stability` - 小信号稳定分析 (aliases: small_signal, 小信号)
- `frequency_response` - 频率响应分析 (aliases: frequency, 频率响应)
- `vsi_weak_bus` - VSI弱母线分析 (aliases: vsi, weak_bus, 弱母线)
- `dudv_curve` - DUDV曲线生成 (aliases: dudv, 电压特性曲线)

#### 结果处理类
- `result_compare` - 结果对比分析 (aliases: compare, 对比)
- `visualize` - 结果可视化 (aliases: viz, plot, 画图)
- `waveform_export` - 波形数据导出 (aliases: export, 波形导出)
- `hdf5_export` - HDF5数据导出 (aliases: hdf5, HDF5导出)
- `disturbance_severity` - 扰动严重度分析 (aliases: disturbance, 扰动分析)
- `compare_visualization` - 对比可视化 (aliases: compare_viz, 对比可视化) - 生成多场景对比图表
- `comtrade_export` - COMTRADE导出 (aliases: comtrade, COMTRADE) - 导出标准COMTRADE格式

#### 电能质量类
- `harmonic_analysis` - 谐波分析 (aliases: harmonic, 谐波)
- `power_quality_analysis` - 电能质量分析 (aliases: quality, 电能质量)
- `reactive_compensation_design` - 无功补偿设计 (aliases: compensation, 无功补偿)

#### 模型与拓扑类
- `ieee3_prep` - IEEE3模型准备 (aliases: prep, 模型准备)
- `topology_check` - 拓扑检查 (aliases: topology, 拓扑)
- `parameter_sensitivity` - 参数灵敏度分析 (aliases: sensitivity, 灵敏度)
- `auto_channel_setup` - 自动量测配置 (aliases: auto_channel, 自动通道) - 批量添加EMT输出通道
- `auto_loop_breaker` - 模型自动解环 (aliases: loop_breaker, 解环) - 消除控制环路
- `model_parameter_extractor` - 模型参数提取器 (aliases: parameter_extractor, 参数提取) - 提取元件参数

### Configuration Structure

All configs follow this schema (`references/config-reference.md`):

```yaml
skill: <skill_name>
auth:
  token_file: .cloudpss_token
model:
  rid: model/holdme/IEEE39  # or model/holdme/IEEE3
  source: cloud
# Skill-specific config...
output:
  format: json  # or csv, yaml
  path: ./results/
  timestamp: true
```

### Default Models

- **IEEE39**: `model/holdme/IEEE39` - 39-bus system for power flow, N-1, VSI, stability analysis
- **IEEE3**: `model/holdme/IEEE3` - 3-bus system for EMT transient simulation

### Python API (from cloudpss-toolkit)

```python
from cloudpss_skills import PowerFlowSkill, EmtSimulationSkill

# Power flow
skill = PowerFlowSkill()
result = skill.run(
    model="model/holdme/IEEE39",
    tolerance=1e-6,
    max_iterations=100
)
print(f"收敛状态: {result.converged}")

# EMT simulation
emt_skill = EmtSimulationSkill()
result = emt_skill.run(
    model="model/holdme/IEEE3",
    duration=5.0,
    step_size=0.0001
)
```

## Testing

Tests in cloudpss-toolkit (`../cloudpss-toolkit/tests/`):

```bash
# Unit tests (no network)
pytest tests/ -q

# Integration tests (requires token)
pytest --run-integration -m "integration and not slow_emt"

# Specific tests
pytest tests/test_powerflow_result.py
pytest tests/test_emt_result.py
```

Local evals are assertion-based (`evals/evals.json`):

```bash
# Validate configuration generation
python scripts/smart_config.py "帮我跑IEEE39潮流" --output configs/test.yaml
cat configs/test.yaml  # Verify skill: power_flow, model: IEEE39
```

## Project Structure

```
cloudpss-sim-skill/
├── scripts/              # Python utilities for config generation
│   ├── smart_config.py      # Natural language config generator
│   ├── component_mapper.py  # Model component discovery
│   ├── channel_helper.py    # Waveform channel inference
│   ├── fuzzy_matcher.py     # Spell correction
│   ├── friendly_validator.py # Config validation
│   ├── interactive_wizard.py # Interactive CLI
│   └── generate_config.py   # Basic template generator
├── configs/              # Generated YAML configurations (gitignored)
├── evals/                # Evaluation test definitions
├── references/           # Documentation
│   ├── usage-guide.md
│   └── config-reference.md
├── cloudpss-sim-v2.skill # Claude Code skill definition
├── SKILL.md              # Detailed skill documentation
├── pyproject.toml        # Python project config
└── README.md             # User-facing documentation
```

## Important Notes

- **Token File**: `.cloudpss_token` is gitignored; users must create this file
- **Results Directory**: Simulation outputs go to `results/` (gitignored)
- **External Dependency**: This skill does NOT work without cloudpss-toolkit - always verify toolkit is accessible via PYTHONPATH
- **Skill File**: `cloudpss-sim-v2.skill` is the Claude Code skill manifest that defines triggers and capabilities
- **New Skills**: cloudpss-toolkit now has 37 skills - when adding support for new skills in smart_config.py, refer to the toolkit's builtin skills in `../cloudpss-toolkit/cloudpss_skills/builtin/`
