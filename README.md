# CloudPSS Sim Skill

Claude Code Skill - 通过自然语言交互进行电力系统仿真

## 快速开始

```bash
# 1. 先安装 cloudpss-toolkit（必须！）
git clone https://github.com/chenyingthu/CloudPSS_skillhub.git
cd CloudPSS_skillhub
pip install -e .

# 2. 克隆本项目
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill

# 3. 配置 CloudPSS Token（必须！）
# 访问 https://www.cloudpss.net → 个人中心 → API Token
echo "你的token" > .cloudpss_token

# 4. 启动 Web 界面（可选）
streamlit run web/app.py --server.port=8502
# 然后浏览器访问 http://localhost:8502

# 5. 或使用命令行
python scripts/smart_config.py "帮我跑IEEE39潮流计算"
```

**⚠️ 注意**: `cloudpss-sim-skill` 依赖 `cloudpss-toolkit`，必须先安装 toolkit！

## 简介

`cloudpss-sim-skill` 是一个 Claude Code Skill，让你可以通过自然语言描述来运行 CloudPSS 电力系统仿真。

配合 `cloudpss-toolkit` 使用，支持 **50个即用型技能**，覆盖潮流计算、EMT暂态仿真、N-1/N-2安全校核、稳定性分析、参数扫描、对比可视化、COMTRADE导出、自动量测配置、正交敏感性分析、模型参数提取、网损分析、保护配合、报告生成、新能源接入分析、戴维南等值、流程编排等完整工作流。

## 特性

- **50个即用型技能** - 覆盖电力系统仿真完整工作流
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
1. 先安装 [cloudpss-toolkit](https://github.com/chenyingthu/CloudPSS_skillhub)
2. 再使用 cloudpss-sim-skill

---

### 步骤1: 安装 cloudpss-toolkit（必须）

```bash
# 克隆 toolkit
git clone https://github.com/chenyingthu/CloudPSS_skillhub.git
cd CloudPSS_skillhub

# 安装依赖
pip install -e .

# 或开发模式安装
pip install -e ".[dev]"
```

详细安装说明请参考 [cloudpss-toolkit README](https://github.com/chenyingthu/CloudPSS_skillhub/-/blob/main/README.md)

---

### 步骤2: 克隆并配置 cloudpss-sim-skill

```bash
# 克隆项目
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill

# 配置 CloudPSS Token（必须！）
# 访问 https://www.cloudpss.net → 个人中心 → API Token
echo "你的token" > .cloudpss_token

# 安装开发依赖（可选）
pip install -e ".[dev]"

# 安装 Playwright 用于 E2E 测试（可选）
pip install playwright pytest-playwright
playwright install chromium
```

---

### 步骤3: 使用方式

#### 方式A: Web 界面（推荐）

```bash
# 启动 Web 应用
streamlit run web/app.py --server.port=8502

# 浏览器访问 http://localhost:8502
```

#### 方式B: 命令行工具

#### 方式A: 通过 Claude Code 使用（推荐）

1. 将 `.skill` 文件下载到你的项目目录
2. 在 Claude Code 中直接描述需求即可触发

```bash
# 下载 skill 文件
curl -O https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill/-/raw/main/cloudpss-sim-v2.skill
```

#### 方式B: 命令行工具

```bash
# 列出所有50个技能
python -m cloudpss_skills list

# 初始化配置
python -m cloudpss_skills init power_flow --output pf.yaml

# 运行技能
python -m cloudpss_skills run --config pf.yaml

# 自然语言生成配置
python scripts/smart_config.py "帮我跑IEEE39潮流计算"

# 交互式向导
python scripts/interactive_wizard.py
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
python scripts/component_mapper.py --model model/chenying/IEEE39 --type 负载

# 推断通道
python scripts/channel_helper.py -p "Bus7的三相电压"

# 启动交互向导
python scripts/interactive_wizard.py
```

## 支持的技能 (50个)

### 仿真执行类
| 技能 | 描述 | 别名 |
|------|------|------|
| `power_flow` | 牛顿-拉夫逊潮流计算 | pf, 潮流, load flow |
| `emt_simulation` | EMT暂态仿真 | emt, 暂态 |
| `emt_fault_study` | EMT故障研究 | fault_study |
| `short_circuit` | 短路电流计算 | 短路 |

### N-1/N-2安全分析类
| 技能 | 描述 | 别名 |
|------|------|------|
| `n1_security` | N-1安全校核 | n1, 安全校核 |
| `n2_security` | N-2双重故障安全分析 | n2, 双重故障 |
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
| `transient_stability_margin` | 暂态稳定裕度/CCT计算 | CCT, 临界切除, 稳定裕度 |
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

### 新能源分析类
| 技能 | 描述 | 别名 |
|------|------|------|
| `renewable_integration` | 新能源接入分析(SCR/LVRT) | 新能源, SCR, LVRT, 风光 |

### 模型与拓扑类
| 技能 | 描述 | 别名 |
|------|------|------|
| `topology_check` | 拓扑检查 | topology |
| `parameter_sensitivity` | 参数灵敏度分析 | sensitivity |
| `auto_channel_setup` | 自动量测配置 | auto_channel |
| `auto_loop_breaker` | 模型自动解环 | loop_breaker |
| `model_parameter_extractor` | 模型参数提取器 | parameter_extractor |
| `model_builder` | 模型构建/修改 | 建模, 添加元件 |
| `model_validator` | 模型验证 | 验证模型, 模型检查 |
| `component_catalog` | 元件目录浏览 | 元件查询, 元件库 |
| `thevenin_equivalent` | 戴维南等值阻抗 | 戴维南, 等值阻抗 |
| `model_hub` | 算例中心管理 | 模型库, 跨服务器 |

### 分析与报告类
| 技能 | 描述 | 别名 |
|------|------|------|
| `loss_analysis` | 网损分析与优化 | loss, 网损 |
| `protection_coordination` | 保护整定与配合分析 | protection, 保护配合 |
| `report_generator` | 智能报告生成器 | report, 报告 |

### 流程编排类
| 技能 | 描述 | 别名 |
|------|------|------|
| `study_pipeline` | 多技能流程编排 | pipeline, 流水线, 串联 |

## 脚本说明

- `smart_config.py` - 智能配置生成器，支持50个技能的自然语言解析
- `fuzzy_matcher.py` - 模糊匹配和拼写纠错
- `friendly_validator.py` - 友好的配置验证和错误诊断
- `component_mapper.py` - 元件ID查询和推断
- `channel_helper.py` - 波形通道名称推断
- `interactive_wizard.py` - 交互式配置向导

## 依赖

| 依赖 | 版本 | 说明 | 安装 |
|------|------|------|------|
| **cloudpss-toolkit** | >= 0.2.0 | **必须** - 核心 API 封装和50个技能 | [安装指南](https://github.com/chenyingthu/CloudPSS_skillhub/-/blob/main/README.md) |
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
    model="model/chenying/IEEE39",
    tolerance=1e-6
)
print(f"收敛状态: {result.converged}")

# EMT仿真
emt = EmtSimulationSkill()
result = emt.run(
    model="model/chenying/IEEE3",
    duration=5.0
)
```

## 测试

本项目包含 122 个自动化测试，覆盖 48 个技能的自然语言配置生成、参数提取准确性、模拟执行和真实 API 集成。

```bash
# 单元测试 + 集成测试（无需网络）
cd tests/
pytest . -v

# 真实 API 集成测试（需要 token 和 --run-integration 标志）
pytest tests/ -v --run-integration
```

### 测试覆盖

| 类别 | 测试文件 | 测试数 | 覆盖范围 |
|------|---------|--------|---------|
| 配置 Schema 验证 | `test_config_schema_validity.py` | 1 | 所有 48 个 evals 通过 `skill.validate()` |
| 参数提取准确性 | `test_parameter_extraction.py` | 20 | 容差、时长、迭代次数、算法、扫描值、阈值 |
| 模拟执行 | `test_mocked_execution.py` | 20 | 20 个技能验证 config 到达 `skill.run()` |
| E2E 集成测试 | `test_e2e_scenarios.py` | 7 | 真实 CloudPSS API 执行（需 `--run-integration`） |
| 技能检测精度 | `test_skill_detection.py` | 25 | 相似技能区分、别名识别、组合关键词、假阳性预防 |
| 边界条件 | `test_boundary_conditions.py` | 46 | 空输入、极端值、Unicode、YAML 序列化、负值拒绝 |
| 配置评估 | `evals/evals.json` | 48 | 每个 eval prompt 的 skill 检测和参数提取 |

## 相关项目

- [cloudpss-toolkit](https://github.com/chenyingthu/CloudPSS_skillhub) - 底层 API 增强库（50+内置技能）

## 许可证

MIT License
