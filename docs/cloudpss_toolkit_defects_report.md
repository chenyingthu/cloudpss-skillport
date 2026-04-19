# CloudPSS Toolkit 缺陷报告

**报告日期**: 2026-04-19
**报告版本**: v1.0
**测试范围**: 50个内置技能
**测试工具**: Playwright E2E 自动化测试

---

## 执行摘要

通过对 CloudPSS Toolkit 的 48 个技能进行端到端自动化测试，发现以下主要问题：

| 问题类别 | 数量 | 严重程度 |
|---------|------|---------|
| get_default_config() 配置不完整 | 16 个技能 | 🔴 高 |
| Schema 与默认配置不匹配 | 4 个技能 | 🔴 高 |
| 模型依赖硬编码 | 4 个技能 | 🟡 中 |
| 输入验证不足 | 5 个技能 | 🟡 中 |

---

## 一、高严重度缺陷

### 1.1 get_default_config() 返回的配置不完整

**缺陷描述**: 多个技能的 `get_default_config()` 方法返回的配置缺少 Schema 中标记为 `required` 的字段，导致配置验证失败。

**受影响技能清单**:

| # | 技能名称 | 缺失字段 | Schema 要求 | 当前默认配置 |
|---|---------|---------|------------|-------------|
| 1 | `dudv_curve` | `buses` | 必需数组 | ❌ 缺失 |
| 2 | `param_scan` | `scan` | 必需对象 | ❌ 缺失 |
| 3 | `parameter_sensitivity` | `analysis` | 必需对象 | ❌ 不完整 |
| 4 | `maintenance_security` | `maintenance` | 必需对象 | ❌ 缺失 |
| 5 | `reactive_compensation_design` | `vsi_input` | 必需对象 | ❌ 缺失 |
| 6 | `result_compare` | `sources` | 必需数组 | ❌ 缺失 |
| 7 | `visualize` | `source`, `visualization` | 必需对象 | ❌ 缺失 |
| 8 | `waveform_export` | `source`, `export` | 必需对象 | ❌ 缺失 |
| 9 | `compare_visualization` | `sources` | 必需数组 | ❌ 缺失 |
| 10 | `comtrade_export` | `source`, `export` | 必需对象 | ❌ 缺失 |
| 11 | `auto_loop_breaker` | `algorithm`, `loop_node` | 推荐字段 | ⚠️ 不完整 |
| 12 | `model_parameter_extractor` | `extraction` | 推荐字段 | ⚠️ 不完整 |
| 13 | `report_generator` | `report` | 必需对象 | ❌ 缺失 |
| 14 | `renewable_integration` | 完整配置 | 必需对象 | ❌ 不完整 |
| 15 | `orthogonal_sensitivity` | `parameters`, `target` | 必需对象 | ❌ 缺失 |
| 16 | `component_catalog` | `filters`, `options` | 推荐字段 | ⚠️ 缺失 |

**错误示例** (`dudv_curve`):
```python
# 当前实现 (有缺陷)
def get_default_config(self) -> Dict[str, Any]:
    return {
        "skill": self.name,
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "", "source": "cloud"},
        "analysis": {"target_buses": []},  # ❌ 缺少 buses 字段
    }

# 期望实现
def get_default_config(self) -> Dict[str, Any]:
    return {
        "skill": self.name,
        "auth": {"token_file": ".cloudpss_token"},
        "model": {"rid": "", "source": "cloud"},
        "buses": ["Bus1", "Bus8", "Bus16"],  # ✅ 添加必需字段
        "analysis": {
            "voltage_range": [0.8, 1.2],
            "steps": 20,
            "reactive_power_range": [-100, 100]
        },
    }
```

**修复建议**:
1. 确保每个技能的 `get_default_config()` 返回的配置包含所有 `required` 字段
2. 添加单元测试验证 `validate(get_default_config())` 必须通过
3. 建立配置完整性检查机制

---

### 1.2 Schema 与默认配置字段名不匹配

**缺陷描述**: 某些技能的 Schema 定义和 `get_default_config()` 返回的字段名称不一致，导致配置无法通过验证。

**受影响技能**:

#### 1.2.1 `model_builder`

| 项目 | Schema 要求 | 默认配置提供 | 状态 |
|-----|------------|-------------|------|
| 主字段 | `workflow`, `base_model` | `model` | ❌ 不匹配 |
| workflow.name | enum: `["open_cloudpss_wind_lvrt_case"]` | ❌ 缺失 | ❌ 必需 |
| base_model.rid | string | ❌ 缺失 | ❌ 必需 |
| modifications | array | ❌ 缺失 | ⚠️ 推荐 |

**详细说明**:
`model_builder` 的 Schema 要求使用 `workflow` + `base_model` 结构，但 `get_default_config()` 返回的是标准 `model` 字段。这导致前端无法直接使用默认配置。

**修复方案**:
```python
def get_default_config(self) -> Dict[str, Any]:
    return {
        "skill": self.name,
        "auth": {"token_file": ".cloudpss_token"},
        # ❌ 移除: "model": {"rid": "", "source": "cloud"}
        # ✅ 改为:
        "workflow": {
            "name": "open_cloudpss_wind_lvrt_case",
            "base_model_rid": "model/open-cloudpss/WTG_PMSG_01-avm-stdm-v2b5",
            "fault_component_key": "component_vrt_fault_1",
            "fault_mode": 1
        },
        "base_model": {
            "rid": "model/open-cloudpss/WTG_PMSG_01-avm-stdm-v2b5",
            "config_index": 0
        },
        "modifications": [],
        "output": {"save": False, "path": "./results/"}
    }
```

#### 1.2.2 `model_validator`

| 项目 | Schema 要求 | 默认配置提供 | 状态 |
|-----|------------|-------------|------|
| 主字段 | `models` (数组) | `model` (单数) | ❌ 不匹配 |

**详细说明**:
Schema 要求 `models` 数组支持批量验证，但默认配置返回单数 `model` 对象。

**修复方案**:
```python
def get_default_config(self) -> Dict[str, Any]:
    return {
        "skill": self.name,
        "auth": {"token_file": ".cloudpss_token"},
        # ❌ 移除: "model": {"rid": "", "source": "cloud"}
        # ✅ 改为:
        "models": [{"rid": "", "source": "cloud"}],
        "validation": {
            "phases": ["topology", "powerflow"],
            "timeout": 300
        },
        "output": {"format": "json", "path": "./results/"}
    }
```

---

## 二、中严重度缺陷

### 2.1 模型依赖硬编码

**缺陷描述**: 某些技能在执行时硬编码了特定模型的组件 key，导致在其他模型上运行时失败。

**受影响技能**:

| 技能 | 硬编码值 | 问题描述 |
|-----|---------|---------|
| `model_builder` | `component_vrt_fault_1` | 预设修改操作查找不存在的组件 |
| `auto_loop_breaker` | 特定控制环路结构 | 在不含控制环路的模型上无法工作 |

**错误信息**:
```
❌执行失败: 找不到匹配的组件: {'key': 'component_vrt_fault_1'}
```

**代码位置**:
- 文件: `cloudpss_skills/builtin/model_builder.py:441`
- 代码:
```python
preset_modification = {
    "action": "modify_component",
    "selector": {
        "key": workflow.get("fault_component_key", "component_vrt_fault_1")  # 硬编码
    },
    ...
}
```

**修复建议**:
```python
def _apply_open_cloudpss_wind_lvrt_case_workflow(self, config: Dict) -> Dict:
    resolved = deepcopy(config)
    workflow = resolved.setdefault("workflow", {})
    base_model = resolved.setdefault("base_model", {})
    base_model.setdefault(
        "rid",
        workflow.get("base_model_rid", "model/open-cloudpss/WTG_PMSG_01-avm-stdm-v2b5")
    )

    # ✅ 添加组件存在性检查
    fault_component_key = workflow.get("fault_component_key", "component_vrt_fault_1")
    if self._check_component_exists(base_model.get("rid"), fault_component_key):
        preset_modification = {
            "action": "modify_component",
            "selector": {"key": fault_component_key},
            "parameters": {...}
        }
        resolved["modifications"] = [preset_modification] + resolved.get("modifications", [])
    else:
        logger.warning(f"组件 {fault_component_key} 不存在，跳过预设修改")

    return resolved
```

---

### 2.2 输入验证不充分

**缺陷描述**: 某些技能在 `validate()` 阶段未能捕获所有配置错误，导致执行时才暴露问题。

**受影响技能**:

| 技能 | 验证缺失 | 后果 |
|-----|---------|------|
| `parameter_sensitivity` | 空 `component` 字符串 | 验证通过但执行失败 |
| `component_catalog` | 权限检查 | 执行时才发现权限不足 |
| `renewable_integration` | 输出路径格式 | 目录 vs 文件混淆 |
| `report_generator` | 空 `skills` 数组 | 生成空报告 |
| `study_pipeline` | pipeline 步骤有效性 | 无效步骤导致运行时错误 |

**修复建议**:
增强各技能的 `validate()` 方法：
```python
def validate(self, config: Dict[str, Any]) -> ValidationResult:
    result = super().validate(config)

    # 添加特定验证
    model = config.get("model", {})
    if not model.get("rid", "").strip():
        result.add_error("必须提供 model.rid")

    # 对于 parameter_sensitivity
    analysis = config.get("analysis", {})
    target_params = analysis.get("target_parameters", [])
    for param in target_params:
        if not param.get("component", "").strip():
            result.add_error("target_parameters[].component 不能为空")

    return result
```

---

### 2.3 输出路径处理不一致

**缺陷描述**: 不同技能对 `output.path` 的处理不一致，有些要求文件路径，有些要求目录路径。

| 技能 | 期望路径类型 | 示例 |
|-----|------------|------|
| `renewable_integration` | 文件路径 | `./results/renewable_result.json` |
| `waveform_export` | 目录路径 | `./results/` |
| `hdf5_export` | 目录路径 | `./results/` |
| `report_generator` | 文件路径 | `./report.docx` |

**修复建议**:
1. 统一约定：所有技能的 `output.path` 都是目录，文件名由技能自动生成
2. 或者在 Schema 中明确标注 `path` 的类型（`directory` vs `file`）
3. 技能内部自动处理路径拼接

---

## 三、测试覆盖率建议

建议 toolkit 添加以下测试用例：

```python
class TestSkillConfigIntegrity:
    """测试技能配置完整性"""

    def test_default_config_passes_validation(self):
        """每个技能的默认配置必须通过自身的 validate()"""
        for skill_name, skill_class in get_all_skills().items():
            skill = skill_class()
            default_config = skill.get_default_config()
            result = skill.validate(default_config)
            assert result.is_valid, f"{skill_name}: 默认配置验证失败 - {result.errors}"

    def test_schema_matches_default_config(self):
        """Schema 中的 required 字段必须在默认配置中存在"""
        for skill_name, skill_class in get_all_skills().items():
            skill = skill_class()
            schema = skill.config_schema
            default = skill.get_default_config()

            required = schema.get("required", [])
            for field in required:
                assert field in default, f"{skill_name}: 默认配置缺少 required 字段 '{field}'"
```

---

## 四、修复优先级建议

| 优先级 | 缺陷 | 影响范围 | 预估工作量 |
|-------|------|---------|-----------|
| 🔴 P0 | 修复 get_default_config() 不完整 | 16个技能 | 2天 |
| 🔴 P0 | 修复 Schema 字段名不匹配 | 2个技能 | 0.5天 |
| 🟡 P1 | 添加组件存在性检查 | 2个技能 | 1天 |
| 🟡 P1 | 增强 validate() 检查 | 5个技能 | 1天 |
| 🟢 P2 | 统一输出路径处理 | 全部技能 | 2天 |
| 🟢 P2 | 添加配置完整性单元测试 | 全部技能 | 1天 |

---

## 五、当前测试状态（修复后）

| 类别 | 技能数 | 状态 |
|-----|-------|------|
| 完全正常（配置+执行） | 38 | ✅ |
| 需要 toolkit 修复配置 | 10 | ⚠️ 等待修复 |
| 总计 | 48 | - |

**通过率**: 79.2% (38/48)

---

## 附录：前端临时修复方案

在 toolkit 修复之前，前端已添加 `_enhance_config_for_skill()` 函数作为临时解决方案：

```python
def _enhance_config_for_skill(config: dict, skill_name: str, user: str) -> dict:
    """Enhance config with complete parameters for skills that fail validation."""
    # 为每个有问题的技能补全配置
    if skill_name == "dudv_curve":
        config["buses"] = ["Bus1", "Bus8", "Bus16"]
        # ...
    elif skill_name == "model_builder":
        config["workflow"] = {"name": "open_cloudpss_wind_lvrt_case"}
        config["base_model"] = {"rid": "model/open-cloudpss/WTG_PMSG_01-avm-stdm-v2b5"}
        # ...
```

**注意**: 这是临时方案，建议在 toolkit 修复后移除。

---

## 联系方式

如有问题，请联系：
- **测试团队**: Claude Code 自动化测试
- **报告生成时间**: 2026-04-19
- **相关项目**: cloudpss-sim-skill

---

*End of Report*
