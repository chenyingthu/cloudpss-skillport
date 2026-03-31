# CloudPSS Sim Skill

Claude Code Skill - 通过自然语言交互进行电力系统仿真

## 快速开始

```bash
# 1. 先安装 cloudpss-toolkit（必须！）
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit.git
cd cloudpss-toolkit
pip install -e .

# 2. 再使用 cloudpss-sim-skill
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill
python scripts/smart_config.py "帮我跑IEEE39潮流计算"
```

**⚠️ 注意**: `cloudpss-sim-skill` 依赖 `cloudpss-toolkit`，必须先安装 toolkit！

## 简介

`cloudpss-sim-skill` 是一个 Claude Code Skill，让你可以通过自然语言描述来运行 CloudPSS 电力系统仿真。

配合 `cloudpss-toolkit` 使用，支持 **37个即用型技能**，覆盖潮流计算、EMT暂态仿真、N-1安全校核、稳定性分析、参数扫描、对比可视化、COMTRADE导出、自动量测配置、正交敏感性分析、模型参数提取等完整工作流。

## 特性

- **37个即用型技能** - 覆盖电力系统仿真完整工作流
- **自然语言配置** - 用中文或英文描述你的仿真需求
- **智能拼写纠错** - 自动纠正技能名称和参数拼写
- **交互式向导** - 逐步引导完成复杂配置
- **智能错误诊断** - 友好的错误信息和解决方案
- **元件自动发现** - 自动推断模型中的元件ID
- **通道名称推断** - 智能识别波形通道名称

## 安装

### 依赖说明

**cloudpss-sim-skill 依赖 cloudpss-toolkit，必须先安装 toolkit！**

安装顺序：
1. 先安装 [cloudpss-toolkit](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit)
2. 再使用 cloudpss-sim-skill

---

### 步骤1: 安装 cloudpss-toolkit（必须）

```bash
# 克隆 toolkit
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit.git
cd cloudpss-toolkit

# 安装依赖
pip install -e .

# 或开发模式安装
pip install -e ".[dev]"
```

详细安装说明请参考 [cloudpss-toolkit README](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit/-/blob/main/README.md)

---

### 步骤2: 使用 cloudpss-sim-skill

#### 方式A: 通过 Claude Code 使用（推荐）

1. 将 `.skill` 文件下载到你的项目目录
2. 在 Claude Code 中直接描述需求即可触发

```bash
# 下载 skill 文件
curl -O https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill/-/raw/main/cloudpss-sim-v2.skill
```

#### 方式B: 命令行使用

```bash
# 克隆 skill 项目
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill

# 确保 toolkit 在 Python 路径中
export PYTHONPATH="${PYTHONPATH}:/path/to/cloudpss-toolkit"

# 列出所有37个技能
python -m cloudpss_skills list

# 运行脚本
python scripts/smart_config.py "帮我跑IEEE39潮流计算"
```

## 使用示例

### 在 Claude Code 中

```
用户: 帮我跑个IEEE39的潮流计算，收敛精度1e-4
Claude: [自动生成配置并执行仿真]

用户: VSI弱母线分析
Claude: [自动生成VSI配置并执行分析]

用户: 无功补偿设计
Claude: [生成无功补偿配置]

用户: powerflow
Claude: [自动纠正为 power_flow 并执行]

用户: 我的配置报错了: model not found
Claude: [诊断错误并提供解决方案]
```

### 命令行

```bash
# 通过 toolkit CLI 使用
python -m cloudpss_skills init power_flow --output pf.yaml
python -m cloudpss_skills run --config pf.yaml

# 生成配置
python scripts/smart_config.py "IEEE39潮流计算" --output config.yaml

# 验证配置
python scripts/friendly_validator.py -c config.yaml

# 查询元件
python scripts/component_mapper.py --model model/holdme/IEEE39 --type 负载

# 推断通道
python scripts/channel_helper.py -p "Bus7的三相电压"

# 启动交互向导
python scripts/interactive_wizard.py
```

## 支持的技能 (40个)

### 仿真执行类
| 技能 | 描述 | 别名 |
|------|------|------|
| `power_flow` | 牛顿-拉夫逊潮流计算 | pf, 潮流, load flow |
| `emt_simulation` | EMT暂态仿真 | emt, 暂态 |
| `emt_fault_study` | EMT故障研究 | fault_study |
| `short_circuit` | 短路电流计算 | short_circuit |

### N-1安全分析类
| 技能 | 描述 | 别名 |
|------|------|------|
| `n1_security` | N-1安全校核 | n1, 安全校核 |
| `emt_n1_screening` | EMT N-1安全筛查 | emt_n1 |
| `contingency_analysis` | 预想事故分析 | contingency |
| `maintenance_security` | 检修方式安全校核 | maintenance |

### 批量与扫描类
| 技能 | 描述 | 别名 |
|------|------|------|
| `batch_powerflow` | 批量潮流计算 | batch, 批量 |
| `param_scan` | 参数扫描分析 | scan, 扫描 |
| `fault_clearing_scan` | 故障清除时间扫描 | fault_clearing |
| `fault_severity_scan` | 故障严重度扫描 | severity_scan |
| `batch_task_manager` | 批处理任务管理 | batch_manager |
| `config_batch_runner` | 配置批量运行器 | config_batch |
| `orthogonal_sensitivity` | 正交敏感性分析 | orthogonal |

### 稳定性分析类
| 技能 | 描述 | 别名 |
|------|------|------|
| `voltage_stability` | 电压稳定分析 | voltage_stab |
| `transient_stability` | 暂态稳定分析 | transient_stab |
| `small_signal_stability` | 小信号稳定分析 | small_signal |
| `frequency_response` | 频率响应分析 | frequency |
| `vsi_weak_bus` | VSI弱母线分析 | vsi, weak_bus |
| `dudv_curve` | DUDV曲线生成 | dudv |

### 结果处理类
| 技能 | 描述 | 别名 |
|------|------|------|
| `result_compare` | 结果对比分析 | compare, 对比 |
| `visualize` | 结果可视化 | viz, plot, 画图 |
| `waveform_export` | 波形数据导出 | export |
| `hdf5_export` | HDF5数据导出 | hdf5 |
| `disturbance_severity` | 扰动严重度分析 | disturbance |
| `compare_visualization` | 对比可视化 | compare_viz |
| `comtrade_export` | COMTRADE导出 | comtrade |

### 电能质量类
| 技能 | 描述 | 别名 |
|------|------|------|
| `harmonic_analysis` | 谐波分析 | harmonic |
| `power_quality_analysis` | 电能质量分析 | quality |
| `reactive_compensation_design` | 无功补偿设计 | compensation |

### 模型与拓扑类
| 技能 | 描述 | 别名 |
|------|------|------|
| `ieee3_prep` | IEEE3模型准备 | prep |
| `topology_check` | 拓扑检查 | topology |
| `parameter_sensitivity` | 参数灵敏度分析 | sensitivity |
| `auto_channel_setup` | 自动量测配置 | auto_channel |
| `auto_loop_breaker` | 模型自动解环 | loop_breaker |
| `model_parameter_extractor` | 模型参数提取器 | parameter_extractor |

### 分析与报告类
| 技能 | 描述 | 别名 |
|------|------|------|
| `loss_analysis` | 网损分析与优化 | loss, 网损, 损耗 |
| `protection_coordination` | 保护整定与配合分析 | protection, 保护配合, 继电保护 |
| `report_generator` | 智能报告生成器 | report, 报告, 生成报告 |

## 脚本说明

- `smart_config.py` - 智能配置生成器，支持40个技能的自然语言解析
- `fuzzy_matcher.py` - 模糊匹配和拼写纠错
- `friendly_validator.py` - 友好的配置验证和错误诊断
- `component_mapper.py` - 元件ID查询和推断
- `channel_helper.py` - 波形通道名称推断
- `interactive_wizard.py` - 交互式配置向导

## 依赖

| 依赖 | 版本 | 说明 | 安装 |
|------|------|------|------|
| **cloudpss-toolkit** | >= 0.2.0 | **必须** - 核心 API 封装和40个技能 | [安装指南](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit/-/blob/main/README.md) |
| cloudpss | >= 4.5.28 | **必须** - CloudPSS 官方 SDK | `pip install cloudpss>=4.5.28` |
| pyyaml | >= 5.4 | 必须 - YAML 配置解析 | `pip install pyyaml>=5.4` |
| numpy | >= 1.20 | 可选 - 数值计算 | 随 toolkit 安装 |
| pandas | >= 1.3 | 可选 - 数据处理 | 随 toolkit 安装 |

**⚠️ 重要**: 必须先安装 `cloudpss-toolkit`，否则 skill 无法运行！

## Python API 使用

```python
from cloudpss_skills import PowerFlowSkill, EmtSimulationSkill

# 潮流计算
skill = PowerFlowSkill()
result = skill.run(
    model="model/holdme/IEEE39",
    tolerance=1e-6
)
print(f"收敛状态: {result.converged}")

# EMT仿真
emt = EmtSimulationSkill()
result = emt.run(
    model="model/holdme/IEEE3",
    duration=5.0
)
```

## 相关项目

- [cloudpss-toolkit](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit) - 底层 API 增强库（30个内置技能）

## 许可证

MIT License
