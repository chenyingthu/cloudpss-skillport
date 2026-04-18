# CloudPSS 技能修复 - PR 要求文档

## 📊 测试概况


- **总测试数:** 48 个技能
- **通过率:** 0.0%
- **需要修复:** 0 个问题
- **测试时间:** 2026-04-18T16:34:31.189622

## 🎯 修复优先级

| 优先级 | 数量 | 说明 |
|--------|------|------|
| 🔴 Critical | 0 | 阻塞性问题，必须立即修复 |
| 🟠 High | 0 | 重要功能问题，尽快修复 |
| 🟡 Medium | 48 | 一般问题，计划修复 |

---

## 🔴 Critical 优先级修复

暂无 Critical 优先级问题

---

## 🟠 High 优先级修复

暂无 High 优先级问题

---

## 📋 按错误类型分类

### UI_MISSING_ELEMENT
**影响技能:** 2 个

| 技能名称 | 类别 | 优先级 |
|----------|------|--------|
| short_circuit | 仿真执行 | MEDIUM |
| n1_security | N-1/N-2安全 | MEDIUM |

### UI_NAVIGATION
**影响技能:** 46 个

| 技能名称 | 类别 | 优先级 |
|----------|------|--------|
| power_flow | 仿真执行 | MEDIUM |
| emt_simulation | 仿真执行 | MEDIUM |
| emt_fault_study | 仿真执行 | MEDIUM |
| n2_security | N-1/N-2安全 | MEDIUM |
| emt_n1_screening | N-1/N-2安全 | MEDIUM |
| contingency_analysis | N-1/N-2安全 | MEDIUM |
| maintenance_security | N-1/N-2安全 | MEDIUM |
| batch_powerflow | 批量与扫描 | MEDIUM |
| param_scan | 批量与扫描 | MEDIUM |
| fault_clearing_scan | 批量与扫描 | MEDIUM |
| fault_severity_scan | 批量与扫描 | MEDIUM |
| batch_task_manager | 批量与扫描 | MEDIUM |
| config_batch_runner | 批量与扫描 | MEDIUM |
| orthogonal_sensitivity | 批量与扫描 | MEDIUM |
| voltage_stability | 稳定性分析 | MEDIUM |
| transient_stability | 稳定性分析 | MEDIUM |
| transient_stability_margin | 稳定性分析 | MEDIUM |
| small_signal_stability | 稳定性分析 | MEDIUM |
| frequency_response | 稳定性分析 | MEDIUM |
| vsi_weak_bus | 稳定性分析 | MEDIUM |
| dudv_curve | 稳定性分析 | MEDIUM |
| result_compare | 结果处理 | MEDIUM |
| visualize | 结果处理 | MEDIUM |
| waveform_export | 结果处理 | MEDIUM |
| hdf5_export | 结果处理 | MEDIUM |
| disturbance_severity | 结果处理 | MEDIUM |
| compare_visualization | 结果处理 | MEDIUM |
| comtrade_export | 结果处理 | MEDIUM |
| harmonic_analysis | 电能质量 | MEDIUM |
| power_quality_analysis | 电能质量 | MEDIUM |
| reactive_compensation_design | 电能质量 | MEDIUM |
| renewable_integration | 新能源 | MEDIUM |
| topology_check | 模型与拓扑 | MEDIUM |
| parameter_sensitivity | 模型与拓扑 | MEDIUM |
| auto_channel_setup | 模型与拓扑 | MEDIUM |
| auto_loop_breaker | 模型与拓扑 | MEDIUM |
| model_parameter_extractor | 模型与拓扑 | MEDIUM |
| model_builder | 模型与拓扑 | MEDIUM |
| model_validator | 模型与拓扑 | MEDIUM |
| component_catalog | 模型与拓扑 | MEDIUM |
| thevenin_equivalent | 模型与拓扑 | MEDIUM |
| model_hub | 模型与拓扑 | MEDIUM |
| loss_analysis | 分析报告 | MEDIUM |
| protection_coordination | 分析报告 | MEDIUM |
| report_generator | 分析报告 | MEDIUM |
| study_pipeline | 流程编排 | MEDIUM |

---

## 🔧 详细修复方案

### 1. FRONTEND_INDEX_ERROR (前端渲染错误)

**问题:** `list.index(x): x not in list`

**影响技能:**

**修复文件:** `web/components/task_create.py`

**修复代码:**
```python
# 在所有使用 list.index() 的地方添加 try-except
format_options = ["json", "csv", "yaml"]
current_format = output.get("format", "json")
try:
    format_index = format_options.index(current_format)
except ValueError:
    format_index = 0  # 使用默认值
```

---

### 2. BACKEND_EMPTY_RID (后端空RID)

**问题:** `Variable "$rid" got invalid value ""`

**影响技能:**

**修复文件:** `web/components/task_create.py`

**修复代码:**
```python
def _normalize_model_rid(config: dict, user: str = None) -> dict:
    model = config.get("model", {})
    rid = model.get("rid", "")

    # 如果 rid 为空，设置默认模型
    if not rid:
        model["rid"] = f"model/{user}/IEEE39"
        model["source"] = "cloud"
        config["model"] = model
```

---

### 3. BACKEND_VARIABLE_ERROR (后端变量未定义)

**问题:** `NameError: name 'base_model' is not defined`

**影响技能:**

**修复文件:** `cloudpss-toolkit/cloudpss_skills/builtin/contingency_analysis.py`

**修复代码:**
```python
# 在 _evaluate_contingency 方法签名中添加 base_model 参数
def _evaluate_contingency(
    self,
    ...
    config: Optional[Dict] = None,
    base_model = None,  # 新增参数
) -> Dict:

# 在调用处传递 base_model
result = self._evaluate_contingency(
    ...
    config,
    base_model,  # 新增
)
```

---

### 4. CONFIG_VALIDATION (配置验证失败)

**问题:** 示例配置不符合 schema 要求

**影响技能:**

**修复文件:** `scripts/smart_config.py`

**修复方案:** 为每个技能生成完整的示例配置，包括所有必需字段。

---

## 🚀 PR 提交要求

### PR 标题格式
```
Fix: [错误类型] - 修复 [技能名称] 的 [问题描述]

示例:
Fix: FRONTEND_INDEX_ERROR - 修复 visualize 和 report_generator 的前端渲染错误
```

### PR 描述模板
```markdown
## 问题描述
[描述问题的现象和影响]

## 修复内容
- [ ] 修复文件1: 具体修改
- [ ] 修复文件2: 具体修改

## 测试验证
- [ ] 本地测试通过
- [ ] Playwright 自动化测试通过

## 影响范围
[列出受影响的技能]

## 破坏性变更
[如果有，列出破坏性变更]
```

### 必须包含的文件
1. **修复代码** - 实际的代码修改
2. **测试用例** - 证明修复有效的测试
3. **文档更新** - 如果有接口变更

---

## 📊 修复后预期结果

修复所有问题后，预期:
- 通过率: > 90%
- Critical 问题: 0
- High 优先级问题: 0

---

*文档生成时间: 2026-04-18T16:34:31.191589*
