# CloudPSS Sim Skill

Claude Code Skill - 通过自然语言交互进行电力系统仿真

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

### 方式1: 通过 Claude Code 使用（推荐）

1. 将 `.skill` 文件下载到你的项目目录
2. 在 Claude Code 中直接描述需求即可触发

```bash
# 下载 skill 文件
curl -O https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill/-/raw/main/cloudpss-sim-v2.skill
```

### 方式2: 命令行使用

```bash
# 安装依赖
pip install cloudpss-sim-skill

# 或直接运行脚本
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

- cloudpss-toolkit >= 0.2.0
- pyyaml >= 5.4

## 相关项目

- [cloudpss-toolkit](https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit) - 底层 API 增强库

## 许可证

MIT License
