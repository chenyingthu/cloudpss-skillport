# Issue: 技能 Config Schema 不符合 SKILL_DEVELOPMENT_STANDARD.md 标准

## 概述

根据《SKILL_DEVELOPMENT_STANDARD.md》(v1.0.0) 标准文档审查，`cloudpss-toolkit` 内置的 48 个技能中有 **17 个技能** 的 `config_schema` 存在 **required 字段声明不规范** 的问题。

---

## 问题详情

### P0: 缺少 `skill` 字段在 required 中 (10 个技能)

标准文档 2.1.1 节明确规定：
> 顶层结构必须包含：`required: ["skill", "model"]`

以下技能的 schema 缺少 `"skill"` 在 required 列表中：

| 技能名称 | 文件路径 | 当前 required | 应修正为 |
|----------|----------|---------------|----------|
| `vsi_weak_bus` | `builtin/vsi_weak_bus.py` | `["model"]` | `["skill", "model"]` |
| `reactive_compensation_design` | `builtin/reactive_compensation_design.py` | `["model"]` | `["skill", "model"]` |
| `batch_task_manager` | `builtin/batch_task_manager.py` | `["model"]` | `["skill", "model"]` |
| `dudv_curve` | `builtin/dudv_curve.py` | `["model"]` | `["skill", "model"]` |
| `hdf5_export` | `builtin/hdf5_export.py` | `[]` | `["skill", "source"]` |
| `protection_coordination` | `builtin/protection_coordination.py` | `["model"]` | `["skill", "model"]` |
| `loss_analysis` | `builtin/loss_analysis.py` | `["model"]` | `["skill", "model"]` |
| `report_generator` | `builtin/report_generator.py` | `[]` | `["skill"]` (后处理技能) |
| `component_catalog` | `builtin/component_catalog.py` | `[]` | `["skill"]` (查询类技能) |
| `model_validator` | `builtin/model_validator.py` | `[]` | `["skill", "model"]` |

**影响**：
- 违反标准文档 2.1.1 节的强制性要求
- JSON Schema 验证时无法保证 `skill` 字段存在
- 可能导致技能路由失败

---

### P1: 缺少 `model` 字段在 required 中 (7 个技能)

以下技能缺少 `"model"` 在 required 列表中：

| 技能名称 | 文件路径 | 当前 required | 建议修正 |
|----------|----------|---------------|----------|
| `dudv_curve` | `builtin/dudv_curve.py` | `["skill"]` | `["skill", "model"]` |
| `batch_task_manager` | `builtin/batch_task_manager.py` | `["skill"]` | `["skill", "model"]` |
| `hdf5_export` | `builtin/hdf5_export.py` | `["skill"]` | **例外：后处理技能** |
| `report_generator` | `builtin/report_generator.py` | `["skill"]` | **例外：后处理技能** |
| `component_catalog` | `builtin/component_catalog.py` | `[]` | **例外：查询类技能** |
| `model_validator` | `builtin/model_validator.py` | `["skill"]` | `["skill", "model"]` |
| `model_hub` | `builtin/model_hub.py` | `["skill"]` | `["skill"]` (跨模型操作) |

---

## 需要架构决策的事项

### 后处理技能例外条款

以下技能是**后处理/结果导出类技能**，它们不需要 `model` 字段，因为操作对象是已有的仿真结果（通过 `job_id` 或文件路径）：

| 技能 | 输入来源 | 建议 |
|------|----------|------|
| `waveform_export` | `source.job_id` | ✅ 合理设计，建议添加例外条款 |
| `result_compare` | `source.tasks` | ✅ 合理设计，建议添加例外条款 |
| `visualize` | `source.task_ids` | ✅ 合理设计，建议添加例外条款 |
| `compare_visualization` | `source.task_ids` | ✅ 合理设计，建议添加例外条款 |
| `comtrade_export` | `source.job_id` | ✅ 合理设计，建议添加例外条款 |
| `hdf5_export` | `source.job_id` | ✅ 合理设计，建议添加例外条款 |
| `report_generator` | `source.task_ids` | ✅ 合理设计，建议添加例外条款 |
| `component_catalog` | 无（查询类） | ✅ 合理设计，建议添加例外条款 |
| `batch_powerflow` | `source.models` | ✅ 合理设计，建议添加例外条款 |
| `disturbance_severity` | `source.job_id` | ✅ 合理设计，建议添加例外条款 |

**建议**：在 `SKILL_DEVELOPMENT_STANDARD.md` 第 2.1.1 节添加例外说明：

```markdown
#### 2.1.1 例外：后处理技能

后处理技能（结果导出、可视化、报告生成等）不需要 `model` 字段，
因为它们操作的是已有的仿真结果而非模型。这类技能应使用：

```python
"required": ["skill", "source"]  # 或 ["skill"]（查询类技能）
```

后处理技能包括：
- 结果导出类：`waveform_export`, `hdf5_export`, `comtrade_export`
- 可视化类：`visualize`, `compare_visualization`
- 报告类：`report_generator`
- 查询类：`component_catalog`
- 批量处理类：`batch_powerflow`, `batch_task_manager`
```

---

## 修复清单

### 必须修复（违反标准且无合理理由）

| 技能 | 修复内容 | 优先级 |
|------|----------|--------|
| `vsi_weak_bus` | 添加 `"skill"` 到 required | P0 |
| `reactive_compensation_design` | 添加 `"skill"` 到 required | P0 |
| `batch_task_manager` | 添加 `"skill"` 到 required | P0 |
| `dudv_curve` | 添加 `"skill"` 到 required | P0 |
| `protection_coordination` | 添加 `"skill"` 到 required | P0 |
| `loss_analysis` | 添加 `"skill"` 到 required | P0 |
| `model_validator` | 添加 `"skill"` 和 `"model"` 到 required | P0 |

### 文档更新（添加例外条款）

| 文档 | 更新内容 | 优先级 |
|------|----------|--------|
| `SKILL_DEVELOPMENT_STANDARD.md` | 添加后处理技能例外条款 | P1 |
| `SKILL_DEVELOPMENT_STANDARD.md` | 添加查询类技能例外条款 | P1 |

---

## 验证方法

修复后，可使用以下脚本验证：

```python
from cloudpss_skills.core import get_skill

skills_requiring_fix = [
    "vsi_weak_bus", "reactive_compensation_design", "batch_task_manager",
    "dudv_curve", "protection_coordination", "loss_analysis", "model_validator",
]

for name in skills_requiring_fix:
    skill = get_skill(name)
    required = skill.config_schema.get("required", [])
    assert "skill" in required, f"{name}: missing 'skill' in required"
    if name not in ["report_generator", "component_catalog"]:
        assert "model" in required, f"{name}: missing 'model' in required"
    print(f"✅ {name}: OK")
```

---

## 审计信息

- **审计时间**: 2026-04-16
- **审计依据**: `docs/skills/SKILL_DEVELOPMENT_STANDARD.md` v1.0.0
- **审计范围**: `cloudpss_skills/builtin/` 下 48 个技能
- **发现问题**: 17 个技能存在 required 字段不规范
- **必须修复**: 7 个技能（P0 违反标准）
- **文档例外**: 10 个技能（后处理/查询类，建议更新标准）

---

## 相关链接

- 标准文档：`docs/skills/SKILL_DEVELOPMENT_STANDARD.md`
- 审计脚本：见附录 A

---

## 附录 A: 审计脚本

```python
"""审计技能是否符合 SKILL_DEVELOPMENT_STANDARD.md"""
import importlib
import os
import sys

sys.path.insert(0, '.')

# 自动导入所有 builtin 技能触发注册
builtin_dir = "cloudpss_skills/builtin"
for filename in os.listdir(builtin_dir):
    if filename.endswith(".py") and not filename.startswith("_"):
        module_name = filename[:-3]
        try:
            importlib.import_module(f"cloudpss_skills.builtin.{module_name}")
        except Exception:
            pass

from cloudpss_skills.core.registry import _SKILL_REGISTRY

print(f"总技能数：{len(_SKILL_REGISTRY)}\n")

issues = []

for skill_name, skill in _SKILL_REGISTRY.items():
    schema = skill.config_schema
    required = schema.get("required", [])

    if "skill" not in required:
        issues.append((skill_name, "缺少'skill' in required"))

    if "model" not in required and skill_name not in [
        "study_pipeline",  # 流水线技能，model 可选
        # 后处理技能（建议添加例外条款）
        "waveform_export", "result_compare", "visualize",
        "compare_visualization", "comtrade_export", "hdf5_export",
        "report_generator", "component_catalog", "batch_powerflow",
        "disturbance_severity", "batch_task_manager", "model_hub",
    ]:
        issues.append((skill_name, "缺少'model' in required"))

if issues:
    print(f"发现 {len(issues)} 个问题:")
    for name, issue in issues:
        print(f"  - {name}: {issue}")
else:
    print("✅ 所有技能符合标准!")
```
