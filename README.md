# CloudPSS Sim Skill

Claude Code Skill - 通过自然语言交互进行电力系统仿真

## 快速开始

```bash
# 1. 先安装 cloudpss-toolkit（必须！）
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit.git
cd cloudpss-toolkit
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 2. 再使用 cloudpss-sim-skill
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill
python scripts/smart_config.py "帮我跑IEEE39潮流计算"
```

**⚠️ 注意**: `cloudpss-sim-skill` 依赖 `cloudpss-toolkit`，必须先安装 toolkit！

## 简介

`cloudpss-sim-skill` 是一个 Claude Code Skill，让你可以通过自然语言描述来运行 CloudPSS 电力系统仿真。

## 特性

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
pip install cloudpss>=4.5.28

# 可选：将 toolkit 加入 Python 路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
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

# 运行脚本
python scripts/smart_config.py "帮我跑IEEE39潮流计算"
```

## 使用示例

### 在 Claude Code 中

```
用户: 帮我跑个IEEE39的潮流计算，收敛精度1e-4
Claude: [自动生成配置并执行仿真]

用户: powerflow
Claude: [自动纠正为 power_flow 并执行]

用户: 我的配置报错了: model not found
Claude: [诊断错误并提供解决方案]
```

### 命令行

```bash
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

## 支持的技能

- `power_flow` - 潮流计算 (别名: pf, 潮流)
- `emt_simulation` - EMT暂态仿真 (别名: emt, 暂态)
- `n1_security` - N-1安全校核 (别名: n1, 安全)
- `batch_powerflow` - 批量潮流 (别名: batch, 批量)
- `param_scan` - 参数扫描 (别名: scan, 扫描)
- `waveform_export` - 波形导出 (别名: export, 导出)
- `visualize` - 结果可视化 (别名: viz, plot, 画图)
- `result_compare` - 结果对比 (别名: compare, 对比)

## 脚本说明

- `smart_config.py` - 智能配置生成器
- `fuzzy_matcher.py` - 模糊匹配和拼写纠错
- `friendly_validator.py` - 友好的配置验证和错误诊断
- `component_mapper.py` - 元件ID查询和推断
- `channel_helper.py` - 波形通道名称推断
- `interactive_wizard.py` - 交互式配置向导

## 依赖

| 依赖 | 版本 | 说明 | 安装 |
|------|------|------|------|
| **cloudpss-toolkit** | >= 0.2.0 | **必须** - 核心 API 封装 | [安装指南](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit/-/blob/main/README.md) |
| cloudpss | >= 4.5.28 | **必须** - CloudPSS 官方 SDK | `pip install cloudpss>=4.5.28` |
| pyyaml | >= 5.4 | 必须 - YAML 配置解析 | `pip install pyyaml>=5.4` |
| numpy | >= 1.20 | 可选 - 数值计算 | 随 toolkit 安装 |
| pandas | >= 1.3 | 可选 - 数据处理 | 随 toolkit 安装 |

**⚠️ 重要**: 必须先安装 `cloudpss-toolkit`，否则 skill 无法运行！

## 相关项目

- [cloudpss-toolkit](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit) - 底层 API 增强库

## 许可证

MIT License
