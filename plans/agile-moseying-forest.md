# Skill Examples: 为每个技能提供可加载的示例配置

## Context

用户打开 task_create 页面后面对空白的输入框，不清楚如何使用该技能。虽然 NL prompt 输入框有 placeholder，但大多数用户仍需要具体示例才能快速理解。

**目标**：为每个技能提供"加载示例"按钮，一键填充完整可用的配置，用户可直接"确认执行"或按需修改。

## 现有基础

- 每个 skill 已有 `get_default_config()` 方法（定义在 `cloudpss-toolkit` 的 builtin 技能文件中），返回完整可运行的 YAML 配置
- `skill_catalog.get_skill(name)` 可获取 skill 实例并调用 `get_default_config()`
- `task_create.py` 已有 session state 管理机制（`draft_config`, `draft_skill`, `draft_prompt`）

## 设计方案

### 修改 `web/components/task_create.py`

在 Step 1（选择技能）区域、技能描述下方，添加"📋 加载示例"按钮：

```python
# After skill description, before Step 2
if st.button("📋 加载示例"):
    _load_example(selected_skill_name)
```

新增 `_load_example(skill_name)` 函数：

```python
def _load_example(skill_name: str):
    """Load the default/example config for a skill into draft state."""
    if skill_name == "study_pipeline":
        # Pipeline needs a meaningful example with steps
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        tpl = templates["潮流 + N-1 + 可视化"]
        config = {
            "skill": "study_pipeline",
            "auth": {"token_file": ".cloudpss_token"},
            "model": {"rid": "model/holdme/IEEE39", "source": "cloud"},
            "pipeline": tpl,
            "continue_on_failure": False,
            "max_workers": 4,
            "output": {"format": "json", "path": "./results/", "timestamp": True},
        }
    else:
        skill = skill_catalog.get_skill(skill_name)
        if skill is None:
            st.error(f"未找到技能: {skill_name}")
            return
        config = skill.get_default_config()

    st.session_state.draft_config = config
    st.session_state.draft_skill = skill_name
    st.session_state.draft_prompt = f"示例: {skill_name}"
    st.session_state.validation_errors = []
    st.rerun()
```

### 用户体验流程

```
1. 选择技能 (e.g. power_flow)
2. 看到技能描述 + "📋 加载示例" 按钮
3. 点击 → 直接进入 Step 3 配置预览，已填充完整配置
4. 用户可以选择：
   - 直接"确认执行"（使用示例配置）
   - 修改模型RID、参数等后再执行
   - 回到 NL 输入框重新描述需求
```

## 修改文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `web/components/task_create.py` | 添加"📋 加载示例"按钮 + `_load_example()` 函数 |
| 新建 | `tests/test_skill_examples.py` | 验证每个技能的 `get_default_config()` 返回有效配置 |

## 实现阶段

**Phase 1: 添加示例加载功能**
- `task_create.py` 添加"加载示例"按钮（Step 1 区域，紧邻技能描述后）
- 实现 `_load_example()` 函数
- study_pipeline 特殊处理：使用 pipeline 编辑器已有模板（潮流+N-1+可视化），而非空 pipeline
- 验证：选择任意技能 → 点击"加载示例" → 配置填充 → 验证通过

**Phase 2: 测试覆盖**
- 遍历所有 37+ 技能，验证 `get_default_config()` 返回的配置能通过 `skill.validate()`
- 验证 study_pipeline 示例模板结构正确
- 验证示例配置的 model RID 格式正确

## 验证方式

1. 浏览器中：选择 power_flow → 点击"加载示例" → 看到 IEEE39 潮流计算配置 → 验证通过
2. 浏览器中：选择 study_pipeline → 点击"加载示例" → 看到 潮流+N-1+可视化 流水线（3步） → 依赖验证通过
3. 浏览器中：选择 emt_simulation → 点击"加载示例" → 看到 IEEE3 EMT 仿真配置 → 验证通过
4. `pytest tests/test_skill_examples.py -v` 确认所有技能示例配置有效
