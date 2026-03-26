---
name: cloudpss-sim-v2
description: |
  CloudPSS电力系统仿真技能v2 - 配置驱动的智能仿真工作流。

  **必须立即调用此技能的场景**（只要涉及以下任一关键词）：
  - CloudPSS / cloudpss / 电力系统仿真 / 潮流计算 / power flow / load flow
  - EMT仿真 / 暂态仿真 / electromagnetic transient / 波形分析 / 波形提取
  - N-1安全校核 / N-1筛查 / N-1分析 / 安全评估 / 检修校核
  - 参数扫描 / param_scan / 批量仿真 / 批量潮流
  - IEEE39 / IEEE3 / IEEE9 / IEEE14 / IEEE标准测试系统
  - 结果可视化 / 画图 / 结果对比 / 拓扑检查 / 模型检查
  - "帮我跑个仿真" / "检查一下" / "画个图" / "对比结果"

  **该技能解决的核心问题**：
  - ✅ 从自然语言自动生成YAML配置（智能参数填充）
  - ✅ 自动推断元件ID和通道名称
  - ✅ 交互式配置向导（新手友好）
  - ✅ 模糊意图识别（"检查安全"→N-1校核）
  - ✅ 配置验证和错误提示优化

  **典型使用场景**：
  - "帮我跑个IEEE39的潮流计算，收敛精度1e-8" → 自动解析精度参数
  - "对IEEE3的负载进行参数扫描，P从10到50" → 自动识别负载元件
  - "画一下Bus7的电压波形" → 自动推断通道名Bus7_Va/Vb/Vc
  - "对比两个仿真结果" → 引导选择结果文件和对比通道

  **重要**：只要涉及电力系统仿真，无论请求多简单或多模糊（如"帮我跑个潮流"、"检查安全"、"画个图"），都必须使用此技能而非通用Python方案。该技能内置智能解析层，能将自然语言转换为精确的YAML配置。

compatibility: |
  Python >= 3.10, cloudpss >= 4.5.28, pyyaml, 项目内置的cloudpss_skills包, .cloudpss_token文件
---

# CloudPSS 电力系统仿真技能 v2

## 核心理念

本技能的核心目标是**消除YAML配置的学习成本**，让用户可以用自然语言描述需求，系统自动生成正确的配置并执行。

## 问题场景与解决方案

### 场景1：参数智能填充（解决 Issue #001）

**用户问题**："帮我检查一下IEEE39系统的N-1安全性，电压阈值设成10%"

**传统问题**：生成的配置仍使用默认值 `voltage_threshold: 0.05`

**解决方案**：
1. 使用 `scripts/smart_config.py` 解析用户输入
2. 提取数值和单位（10% → 0.1）
3. 自动填充到配置中

**处理流程**：
```python
# smart_config.py 逻辑
user_input = "电压阈值设成10%"
→ 提取 "10%" → 转换为 0.1
→ 设置 voltage_threshold: 0.1
```

### 场景2：元件ID自动推断（解决 Issue #002）

**用户问题**："对IEEE3模型的负载进行有功功率参数扫描"

**传统问题**：`component: ""` 需要用户手动填写

**解决方案**：
1. 使用 `scripts/component_mapper.py` 查询模型
2. 匹配"负载"→常见命名模式（Load_1, Load_Bus2等）
3. 列出候选元件供用户选择

**处理流程**：
```
1. 获取模型拓扑
2. 查找类型匹配的元件（Load, PQ Load等）
3. 返回候选列表：["Load_1", "Load_2", "Load_3"]
4. 用户确认或选择
```

### 场景3：模型列表解析（解决 Issue #003）

**用户问题**："对IEEE3、IEEE9、IEEE14、IEEE39这几个模型都跑一遍潮流"

**传统问题**：只识别出IEEE3和IEEE39，遗漏IEEE9和IEEE14

**解决方案**：
1. 使用正则表达式提取所有模型名称模式
2. 映射到标准RID格式
3. 询问用户确认未识别模型

**处理流程**：
```python
# 解析文本中的模型
models = extract_models("对IEEE3、IEEE9、IEEE14、IEEE39...")
→ ["IEEE3", "IEEE9", "IEEE14", "IEEE39"]
→ 映射到 ["model/holdme/IEEE3", "model/holdme/IEEE9", ...]
→ 对未缓存模型询问用户确认
```

### 场景4：通道名称推断（解决 Issue #004, #005）

**用户问题**："画一下Bus1的三相电压波形"

**传统问题**：`channels: []` 需要手动填写 Bus1_Va, Bus1_Vb, Bus1_Vc

**解决方案**：
1. 使用 `scripts/channel_helper.py` 建立命名模式库
2. 从"Bus1的三相电压"推断通道名
3. 支持通配符模式

**处理流程**：
```python
# channel_helper.py 逻辑
"Bus1的三相电压"
→ 识别节点名 "Bus1"
→ 识别类型 "三相电压"
→ 推断通道: ["Bus1_Va", "Bus1_Vb", "Bus1_Vc"]
→ 或通配符: ["Bus1_V*"]
```

### 场景5：模糊意图识别

**用户问题**："帮我跑个仿真"

**传统问题**：过于模糊，不知道具体要做什么

**解决方案**：
1. 主动询问澄清
2. 提供选项让用户选择

**处理流程**：
```
用户: "帮我跑个仿真"
→ 询问: "您想做哪种类型的仿真？"
   1. 潮流计算（稳态分析）
   2. EMT暂态仿真（波形分析）
   3. N-1安全校核
   4. 参数扫描
→ 根据选择进入相应流程
```

### 场景6：拼写纠错（解决 Issue #006）

**用户问题**："帮我生成n1security的配置"

**传统问题**：直接报错 "Unknown skill: n1security"

**解决方案**：
1. 使用模糊匹配找到最接近的技能名
2. 提示用户正确拼写

**处理流程**：
```
输入: "n1security"
→ 模糊匹配: "n1_security"
→ 提示: "您是不是想输入 'n1_security'？"
→ 自动使用正确名称继续
```

### 场景7：交互式配置向导（解决 Issue #008）

**用户问题**：新手用户不知道如何配置 param_scan

**解决方案**：
使用 `scripts/interactive_wizard.py` 提供交互式配置

**处理流程**：
```
启动向导 → 逐步询问:
1. 选择技能类型 → param_scan
2. 选择模型 → IEEE3 / IEEE39 / 其他
3. 选择目标元件 → 列出可用元件
4. 选择参数 → P / Q / Vset
5. 输入参数值范围 → [10, 20, 30, 40, 50]
6. 生成配置 → 保存到 configs/param_scan_xxx.yaml
```

## 完整工作流程

```
用户请求
    ↓
[意图识别] ──模糊？──→ [主动询问澄清]
    ↓                    ↓
[参数智能提取] ←───────┘
    ↓
[模型/元件/通道推断]
    ↓
[生成YAML配置]
    ↓
[验证配置] ──错误？──→ [友好错误提示 + 修复建议]
    ↓                      ↓
[执行仿真] ←─────────────┘
    ↓
[监控进度]
    ↓
[结果展示]
    ↓
[后处理选项] → 可视化 / 导出 / 对比
```

## 核心脚本使用指南

### 1. smart_config.py - 智能配置生成

**用途**：从自然语言提取参数并生成配置

**用法**：
```bash
python cloudpss-sim-v2/scripts/smart_config.py \
    --skill power_flow \
    --prompt "帮我跑IEEE39潮流，收敛精度1e-8，最大迭代50次" \
    --output configs/my_pf.yaml
```

**支持的智能提取**：
- 数值+单位："10%" → 0.1, "5秒" → 5.0
- 布尔值："启用" → true, "禁用" → false
- 枚举值："牛顿法" → newton_raphson

### 2. component_mapper.py - 元件映射

**用途**：查询模型并列出可用元件

**用法**：
```bash
# 列出模型中的所有负载
python cloudpss-sim-v2/scripts/component_mapper.py \
    --model model/holdme/IEEE3 \
    --type Load

# 输出示例：
# 找到以下负载元件:
# 1. Load_1 (Bus1负载)
# 2. Load_2 (Bus2负载)
# 3. Load_3 (Bus3负载)
```

### 3. channel_helper.py - 通道助手

**用途**：推断通道名称模式

**用法**：
```bash
# 获取Bus1的通道建议
python cloudpss-sim-v2/scripts/channel_helper.py \
    --node Bus1 \
    --type three_phase_voltage

# 输出示例：
# 三相电压通道: Bus1_Va, Bus1_Vb, Bus1_Vc
# 或通配符: Bus1_V*
```

### 4. interactive_wizard.py - 交互式向导

**用途**：引导新手用户完成配置

**用法**：
```bash
python cloudpss-sim-v2/scripts/interactive_wizard.py

# 交互式提示:
# ? 选择技能类型: [使用方向键]
#   > power_flow
#     emt_simulation
#     n1_security
#     param_scan
#
# ? 选择模型: IEEE39
# ? 输出格式: json
# ? 是否添加时间戳: Yes
#
# 配置已生成: configs/power_flow_20260325_143022.yaml
```

### 5. fuzzy_matcher.py - 模糊匹配

**用途**：纠正拼写错误和识别别名

**用法**：
```bash
python cloudpss-sim-v2/scripts/fuzzy_matcher.py "n1security"
# 输出: 您是不是想输入 'n1_security'？
```

## 配置文件生成模板

### 模板1：简洁风格（专家用户）

```yaml
skill: power_flow
model:
  rid: model/holdme/IEEE39
```

### 模板2：完整风格（详细配置）

```yaml
skill: power_flow
auth:
  token_file: .cloudpss_token
model:
  rid: model/holdme/IEEE39
  source: cloud
algorithm:
  type: newton_raphson
  tolerance: 1.0e-6
  max_iterations: 100
output:
  format: json
  path: ./results/
  prefix: power_flow
  timestamp: true
```

### 模板3：智能生成（自然语言驱动）

```bash
# 用户只需要说：
# "帮我跑个IEEE39潮流，收敛精度高点，结果存成CSV"

# 系统自动生成：
skill: power_flow
model:
  rid: model/holdme/IEEE39
algorithm:
  tolerance: 1.0e-8  # "精度高点" → 提高精度
output:
  format: csv        # "存成CSV" → 修改格式
```

## 错误处理与友好提示

### 错误1：Token无效

**旧提示**：`Authentication failed: Invalid token`

**新提示**：
```
❌ 认证失败

可能原因：
1. Token已过期（CloudPSS Token有效期为30天）
2. Token文件格式错误

解决步骤：
1. 访问 https://www.cloudpss.net
2. 登录 → 个人中心 → API Token
3. 生成新Token
4. 保存到项目根目录：echo "新token" > .cloudpss_token
```

### 错误2：模型不存在

**旧提示**：`Model not found: model/xxx`

**新提示**：
```
❌ 模型未找到: model/unknown/XXX

可用模型（已验证）：
✅ model/holdme/IEEE39 - 39节点系统，适合潮流计算
✅ model/holdme/IEEE3  - 3节点系统，适合EMT仿真

请检查：
1. 模型RID是否正确（格式: model/owner/name）
2. 您是否有权限访问该模型
3. 使用以下命令查看可用模型：
   python -m cloudpss_skills list-models
```

### 错误3：元件不存在

**旧提示**：`Component not found: Load_XXX`

**新提示**：
```
❌ 元件未找到: Load_XXX

该模型中的可用负载元件：
1. Load_1 (Bus1负载)
2. Load_2 (Bus2负载)
3. Load_3 (Bus3负载)

提示：
- 使用通配符: Load_* 匹配所有负载
- 查看完整元件列表：
  python cloudpss-sim-v2/scripts/component_mapper.py --model model/holdme/IEEE3
```

### 错误4：配置验证失败

**旧提示**：`Schema validation failed: properties.tolerance.type`

**新提示**：
```
❌ 配置验证失败

问题：tolerance 值类型错误
当前值: "1e-6" (字符串)
正确值: 1e-6 (数字，不加引号)

修复示例：
algorithm:
  tolerance: 1.0e-6  # 正确 ✓
  # tolerance: "1.0e-6"  # 错误 ✗

完整配置示例见：
cloudpss_skills/templates/power_flow.yaml
```

## 典型用户交互示例

### 示例1：完整参数指定

**用户**："帮我跑个IEEE39的潮流计算，用牛顿法，收敛精度1e-8，最大迭代50次，结果存成CSV"

**Claude处理**：
1. 识别技能：power_flow
2. 识别模型：IEEE39 → model/holdme/IEEE39
3. 提取参数：
   - "牛顿法" → algorithm.type: newton_raphson
   - "1e-8" → algorithm.tolerance: 1.0e-8
   - "50次" → algorithm.max_iterations: 50
   - "CSV" → output.format: csv
4. 生成配置
5. 执行并返回结果

### 示例2：模糊请求澄清

**用户**："帮我检查一下安全"

**Claude处理**：
```
"检查安全"可能指以下操作：

1. 🔒 N-1安全校核（检查支路停运后的系统稳定性）
2. 🔍 拓扑检查（验证模型连接完整性）
3. ⚡ 电压稳定性分析（检查电压越限情况）

请选择（输入数字1-3）：
```

### 示例3：元件选择引导

**用户**："对IEEE3的负载进行参数扫描"

**Claude处理**：
```
正在获取IEEE3模型的负载元件...

找到以下负载元件：
1. Load_1 (Bus1负载, 当前P=100MW)
2. Load_2 (Bus2负载, 当前P=150MW)
3. Load_3 (Bus3负载, 当前P=120MW)

请选择要扫描的负载（输入数字1-3）：
```

### 示例4：通道选择引导

**用户**："画一下Bus7的电压"

**Claude处理**：
```
"Bus7的电压"可以指：

1. 三相电压（Va, Vb, Vc）
2. A相电压（Va）
3. 正序电压（V1）

请选择（输入1-3，或输入'all'选择全部）：
```

## 进阶功能

### 批量工作流

支持多技能串联执行：

```yaml
# workflow.yaml
workflow:
  name: 完整分析流程
  steps:
    - name: 潮流计算
      skill: power_flow
      model: model/holdme/IEEE39

    - name: N-1校核
      skill: n1_security
      model: model/holdme/IEEE39
      depends_on: [潮流计算]

    - name: 结果可视化
      skill: visualize
      input: ${n1_security.output}
```

### 配置模板收藏

用户可以保存常用配置为模板：

```bash
# 保存当前配置为模板
python -m cloudpss_skills save-template my_pf_config

# 使用模板
python -m cloudpss_skills run --template my_pf_config
```

## 最佳实践

1. **首次使用**：运行向导 `python scripts/interactive_wizard.py`
2. **快速生成**：使用智能配置 `python scripts/smart_config.py`
3. **查看示例**：参考 `cloudpss_skills/templates/` 中的模板
4. **故障排查**：使用 `--verbose` 查看详细日志
5. **结果管理**：使用 `timestamp: true` 避免结果覆盖
