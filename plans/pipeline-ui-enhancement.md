# Pipeline UI Enhancement: 完善 study_pipeline 复杂操控界面

## Context

当前 `study_pipeline` 的前端交互和结果展示都非常基础：

### task_create.py 的问题
- **无专门的 pipeline 配置编辑器**：`study_pipeline` 走的是 generic JSON 编辑，用户需要在文本框里手写复杂的 pipeline YAML
- **缺少 pipeline 专用的 step builder UI**：无法可视化地添加/编辑/排序/配置 pipeline 步骤
- **不支持高级特性**：`foreach` 循环、`when` 条件、`depends_on` 依赖关系、`parallel` 并行标记都没有 UI 支持
- **无配置模板**：只有一个 power_flow 步骤的默认模板，无法帮助用户快速构建多步骤流水线

### viz_renderers/pipeline.py 的问题
- **只显示基本 expanders**：没有 DAG 依赖关系可视化，没有并行组识别
- **无结果正确性验证**：只渲染数据，不验证结果是否符合物理规律（如潮流收敛后母线电压是否在 0.95-1.05 p.u. 范围内）
- **无跨步骤数据流追踪**：步骤间的数据传递和变量插值不可见
- **foreach 循环结果无聚合展示**：多次迭代的结果没有汇总统计
- **缺少执行时间线**：无法直观看出哪些步骤并行执行

### task_results.py 的问题
- **仍保留旧的 inline renderers**：`_render_power_flow`, `_render_emt`, `_render_n1`, `_render_generic` 仍然存在，与 viz_skill 分发器并存
- **流水线结果检测但未使用 viz_skill**：`_show_results` 中虽然有 `_render_generic` 的 fallback，但 pipeline 类型结果需要确保被正确分发

## 设计方案

### 核心目标

1. **可视化 Pipeline 配置** — 在 task_create 中提供直观的 pipeline 步骤构建器
2. **可视化 Pipeline 结果** — 增强 pipeline renderer，展示 DAG 依赖、并行组、时间线、数据流
3. **结果正确性验证** — 不仅渲染数据，还要验证结果是否符合物理规律和逻辑
4. **测试体系** — 全面的单元+集成+浏览器测试

### 模块结构变化

```
web/components/
    task_create.py                     # 修改：新增 pipeline_step_builder()
    task_results.py                    # 修改：移除旧 inline renderers，完全委托 viz_skill
    viz_skill.py                       # 小幅修改：新增 foreach 检测
    viz_renderers/
        __init__.py                    # 修改：添加 pipeline_dag 导入
        pipeline.py                    # 重写：DAG 可视化 + 并行组 + 时间线 + 数据流 + 验证
        pipeline_dag.py                # 新增：纯 DAG 图渲染（matplotlib/networkx）
        pipeline_validation.py         # 新增：结果正确性验证逻辑
    pipeline_editor.py                 # 新增：task_create 中的 pipeline 配置编辑器组件
```

## Phase 1: Pipeline 配置编辑器 (task_create 增强)

### 1.1 新增 `web/components/pipeline_editor.py`

可视化 pipeline 步骤构建器，替代 generic JSON 编辑：

```python
def render_pipeline_editor(config: dict):
    """Interactive pipeline step builder."""
    # 1. Global settings: continue_on_failure, max_workers
    # 2. Step list with drag-drop reordering (Streamlit session_state based)
    # 3. For each step:
    #    - name (text input)
    #    - skill (selectbox from skill_catalog)
    #    - config (skill-specific editor or JSON)
    #    - depends_on (multi-select from existing step names)
    #    - when (conditional expression builder)
    #    - foreach (loop variable + values list)
    #    - parallel (checkbox)
    # 4. Add/Remove step buttons
    # 5. Visual dependency preview (simple text: "步骤A → 步骤B")
    # 6. YAML preview of full pipeline config
    # 7. Validation (check for circular deps, missing skills, etc.)
```

### 1.2 修改 `web/components/task_create.py`

```python
# In _edit_skill_params():
elif skill_name == "study_pipeline":
    from web.components.pipeline_editor import render_pipeline_editor
    render_pipeline_editor(config)
```

### 1.3 Pipeline 模板库

提供常见 pipeline 模板供用户快速选择：
- **潮流+N-1+可视化**（最常用）
- **EMT仿真+故障研究+对比分析**
- **VSI弱母线分析+无功补偿设计**
- **批量参数扫描+结果对比**

## Phase 2: Pipeline 结果渲染增强

### 2.1 重写 `viz_renderers/pipeline.py`

```python
@register_renderer("study_pipeline")
def render(data: dict, task, context=None):
    # ─── 1. 总体摘要 ─────────────────────────
    # 成功率进度条、总耗时、并行度统计

    # ─── 2. 执行时间线 ───────────────────────
    # 识别并行组，用 st.columns 展示并行步骤
    # 用 st.progress 显示相对耗时比例

    # ─── 3. DAG 依赖关系图 ───────────────────
    # 用 matplotlib/networkx 绘制 DAG 图
    # 节点颜色 = 执行状态（绿=成功，红=失败，灰=跳过）
    # 边 = depends_on 关系

    # ─── 4. 数据流追踪 ───────────────────────
    # 展示步骤间的数据传递
    # 变量插值解析结果展示

    # ─── 5. 逐步结果（增强版） ───────────────
    # 与现有 render_step 兼容
    # foreach 循环步骤展示迭代汇总统计

    # ─── 6. 结果正确性验证 ───────────────────
    # 调用 pipeline_validation 对每个步骤验证
```

### 2.2 新增 `viz_renderers/pipeline_dag.py`

```python
def render_dag(steps: list) -> None:
    """Render DAG visualization of pipeline steps."""
    # 使用 networkx 构建 DAG
    # 节点属性：name, skill, status, duration
    # 边属性：depends_on
    # 布局：topological sort 分层
    # 颜色：status 映射
    # 用 matplotlib 渲染，st.pyplot 展示
```

### 2.3 新增 `viz_renderers/pipeline_validation.py`

```python
def validate_pipeline_result(data: dict) -> list[dict]:
    """Validate pipeline results for correctness.

    Returns list of validation findings:
    [
        {
            "step": "潮流计算",
            "check": "voltage_range",
            "result": "pass" | "fail" | "warning",
            "detail": "所有母线电压在 0.95-1.05 p.u. 范围内",
            "physical_basis": "IEEE 标准要求运行电压在 0.95-1.05 p.u."
        },
        ...
    ]
    """
    findings = []
    for step in data.get("steps", []):
        skill = step.get("skill", "")
        result = step.get("result_data", {})

        if skill == "power_flow":
            findings.extend(_validate_power_flow(step, result))
        elif skill == "emt_simulation":
            findings.extend(_validate_emt(step, result))
        elif skill == "n1_security":
            findings.extend(_validate_n1(step, result))
        elif skill == "vsi_weak_bus":
            findings.extend(_validate_vsi(step, result))
        elif skill == "short_circuit":
            findings.extend(_validate_short_circuit(step, result))

    return findings

def _validate_power_flow(step, result):
    """物理规律验证：潮流计算结果正确性检查"""
    checks = []

    # 1. 电压范围检查
    buses = result.get("buses", [])
    for bus in buses:
        vm = float(bus.get("Vm", 1.0))
        if vm < 0.90 or vm > 1.10:
            checks.append({
                "step": step.get("name", ""),
                "check": "voltage_critical",
                "result": "fail",
                "detail": f"母线 {bus.get('Bus')} 电压 {vm:.4f} p.u. 超出 0.90-1.10 范围",
                "physical_basis": "电力系统安全运行要求母线电压在 0.90-1.10 p.u. 范围内"
            })
        elif vm < 0.95 or vm > 1.05:
            checks.append({
                "step": step.get("name", ""),
                "check": "voltage_warning",
                "result": "warning",
                "detail": f"母线 {bus.get('Bus')} 电压 {vm:.4f} p.u. 偏离 0.95-1.05 推荐范围",
                "physical_basis": "IEEE 标准推荐运行电压在 0.95-1.05 p.u."
            })

    # 2. 功率平衡检查
    total_gen_p = sum(float(b.get("Pgen", 0)) for b in buses)
    total_load_p = sum(float(b.get("Pload", 0)) for b in buses)
    loss_p = total_gen_p - total_load_p
    loss_pct = (loss_p / total_gen_p * 100) if total_gen_p else 0
    if loss_pct > 15:
        checks.append({
            "step": step.get("name", ""),
            "check": "loss_high",
            "result": "warning",
            "detail": f"网损 {loss_pct:.1f}% 偏高，通常 < 5%",
            "physical_basis": "正常电力系统网损一般 < 5%，> 15% 可能存在模型错误"
        })

    # 3. 收敛性检查
    if not result.get("converged", False):
        checks.append({
            "step": step.get("name", ""),
            "check": "convergence",
            "result": "fail",
            "detail": "潮流计算未收敛",
            "physical_basis": "潮流计算必须收敛，否则结果无物理意义"
        })

    return checks
```

## Phase 3: task_results.py 清理

### 3.1 移除旧 inline renderers

删除 `_render_power_flow`, `_render_emt`, `_render_n1`, `_render_generic` 函数。

### 3.2 完全委托 viz_skill

```python
def _show_results(task):
    result_data = task.result_data or {}
    st.subheader("📊 仿真结果")

    if is_pipeline_result(result_data):
        render_pipeline(task)
    else:
        render_result(task.skill_name, result_data, task)
```

## Phase 4: 测试方案

### 4.1 单元测试 (pytest)

```
tests/test_pipeline_editor.py:
  - test_add_step, test_remove_step, test_reorder_steps
  - test_add_dependency, test_circular_dependency_detection
  - test_foreach_expansion, test_when_condition_parsing
  - test_config_to_yaml, test_yaml_to_config

tests/test_pipeline_validation.py:
  - test_validate_power_flow: voltage ranges, loss limits, convergence
  - test_validate_emt: waveform bounds, energy conservation
  - test_validate_n1: violation logic, safety margins
  - test_validate_vsi: VSI threshold, weak bus identification
  - test_validate_short_circuit: current limits, thermal stress
  - test_validate_full_pipeline: multi-step validation chain

tests/test_pipeline_dag.py:
  - test_dag_construction: graph from steps list
  - test_dag_rendering: matplotlib output generated
  - test_dag_colors: status-to-color mapping
  - test_dag_layout: topological ordering correct

tests/test_viz_skill.py (extend):
  - test_detect_pipeline_result: is_pipeline_result() variants
  - test_pipeline_renderer_output: full pipeline render
  - test_parallel_group_detection: identify concurrent steps
  - test_foreach_aggregation: foreach loop result display
  - test_validation_findings: validation results display
```

### 4.2 集成测试

```
tests/test_pipeline_e2e.py:
  - test_mocked_pipeline_execution:
      构造 pipeline 配置 → mock skill.run() → 验证 result_data 结构正确

  - test_pipeline_with_foreach:
      构造含 foreach 的 pipeline → mock → 验证步骤展开正确

  - test_pipeline_with_conditions:
      构造含 when 条件的 pipeline → mock → 验证条件分支

  - test_pipeline_parallel_execution:
      构造并行步骤 pipeline → mock → 验证并行组识别

tests/test_pipeline_browser.py (Playwright):
  - test_pipeline_config_editor:
      浏览器中创建 pipeline 任务 → 填写步骤 → 验证 YAML 预览

  - test_pipeline_result_display:
      浏览器中查看 pipeline 结果 → 验证 DAG 图、时间线、验证结果

  - test_pipeline_validation_ui:
      浏览器中验证正确性分析展示 → 验证物理规律检查
```

### 4.3 正确性分析测试

```
tests/test_result_correctness.py:
  """验证渲染的结果符合物理规律，不仅是'有输出'"""

  - test_power_flow_voltage_bounds:
      验证所有母线电压在合理范围内 (0.90-1.10 p.u.)

  - test_power_flow_power_balance:
      验证发电 = 负荷 + 网损（允许小误差）

  - test_emt_energy_conservation:
      EMT 波形数据满足能量守恒（波动在合理范围内）

  - test_n1_violation_logic:
      验证 N-1 越限判定逻辑一致性

  - test_vsi_physical_meaning:
      验证 VSI 值在 [0, 1] 范围内且弱母线判定正确

  - test_short_circuit_current_bounds:
      验证短路电流不超过设备额定限值

  - test_pipeline_cross_step_consistency:
      验证 pipeline 中前后步骤的数据一致性
      （如潮流计算后的电压应作为 EMT 仿真的初始条件）
```

### 4.4 浏览器测试 (Playwright MCP)

```
浏览器端到端测试流程：
1. 创建 pipeline 任务
   - 选择 study_pipeline 技能
   - 使用 pipeline 编辑器添加 3 个步骤
   - 设置依赖关系和并行标记
   - 验证 YAML 预览正确
   - 确认执行

2. 查看 pipeline 结果
   - 验证总体摘要正确（成功/失败统计）
   - 验证 DAG 依赖图渲染正确
   - 验证执行时间线展示
   - 验证每个步骤的结果渲染（委派给对应技能渲染器）
   - 验证 foreach 循环结果聚合
   - 验证结果正确性分析面板

3. 验证数据流
   - 确认跨步骤数据引用正确解析
   - 验证变量插值展示
```

## 修改文件清单

| 操作 | 文件 | 说明 | 状态 |
|------|------|------|------|
| 新建 | `web/components/pipeline_editor.py` | Pipeline 步骤可视化编辑器 | ✅ 已实现 |
| 修改 | `web/components/viz_renderers/pipeline.py` | 重写：DAG + 时间线 + 验证（内联实现） | ✅ 已实现 |
| 修改 | `web/components/task_create.py` | 添加 pipeline 编辑器支持 | ✅ 已实现 |
| 新建 | `tests/test_pipeline_features.py` | Pipeline 编辑器+渲染器+验证集成测试（36 tests） | ✅ 已实现 |
| ~~新建~~ | ~~`web/components/viz_renderers/pipeline_dag.py`~~ | ~~DAG 依赖关系图渲染~~ | ~~已计划~~ → 取消，代码内联到 pipeline.py |
| ~~新建~~ | ~~`web/components/viz_renderers/pipeline_validation.py`~~ | ~~结果正确性验证~~ | ~~已计划~~ → 取消，代码内联到 pipeline.py |
| 修改 | `web/components/task_results.py` | 清理旧 inline renderers | ✅ 已完成（之前提交） |
| 修改 | `tests/test_viz_skill.py` | 扩展 pipeline 相关测试 | ✅ 已有 pipeline 检测测试 |
| ~~新建~~ | ~~`tests/test_pipeline_e2e.py`~~ | ~~流水线端到端集成测试~~ | ~~已计划~~ → 功能已包含在 test_pipeline_features.py |
| ~~新建~~ | ~~`tests/test_result_correctness.py`~~ | ~~结果物理正确性验证测试~~ | ~~已计划~~ → 功能已包含在 test_pipeline_features.py |

## 实现阶段

**Phase 1: Pipeline 配置编辑器** ✅ 完成
- pipeline_editor.py 核心组件 ✅
- task_create.py 集成 ✅
- 模板库（4个常见模板：潮流+N-1+可视化、EMT故障研究+对比分析、VSI弱母线+无功补偿、并行参数扫描）✅
- 依赖验证（循环依赖检测、缺失依赖检测）✅
- YAML 预览 ✅
- 单元测试（7 tests）✅
- 浏览器 E2E 验证 ✅（模板加载、依赖验证、3 bug 修复：嵌套 expander、skill_catalog 作用域、slider format_func）
- 已提交至 main 分支 ✅

**Phase 2: Pipeline 结果渲染增强** ✅ 完成
- pipeline.py 重写：5-tab 布局（总体摘要、执行时间线、DAG依赖图、逐步结果、正确性验证）✅
- 并行批次识别（_identify_batches 拓扑排序）✅
- DAG 依赖图（matplotlib/networkx + 文本 fallback）✅
- 正确性验证（_validate_power_flow、_validate_emt、_validate_n1、_validate_vsi、_validate_short_circuit）✅
- 跨步骤上下文构建（_build_context_for_step）✅
- 技能分发（render_step 委托给 viz_skill）✅
- 单元测试（13 validation + 4 renderer + 4 DAG + 5 integration = 26 tests）✅
- 浏览器 E2E 验证 ✅

> **设计偏离说明**：原计划将 DAG 渲染和验证逻辑拆分为独立文件（pipeline_dag.py、pipeline_validation.py），实际采用内联实现——所有逻辑集成在 pipeline.py 中，减少模块间依赖，保持代码简洁。

**Phase 3: task_results.py 清理** ✅ 完成（已在之前提交中完成）
- 旧 inline renderers 已移除（_render_power_flow、_render_emt、_render_n1、_render_generic 不存在于 task_results.py）
- 完全委托 viz_skill 分发器（line 13: `from web.components.viz_skill import render_result, is_pipeline_result, render_pipeline`）
- 测试验证通过（test_task_results_uses_dispatcher 确认无内联渲染器）

**Phase 4: 集成测试** ✅ 完成
- 集成测试（test_pipeline_features.py：36 tests 覆盖编辑器、渲染器、验证、DAG、端到端流程）✅
- 浏览器测试（Playwright MCP：手动验证模板加载、依赖验证、配置验证）✅
- 正确性分析测试（集成在 test_pipeline_features.py 的 validation 测试中）✅

## 验证方式

1. Phase 1 ✅：浏览器中用 pipeline 编辑器创建任务，4 个模板均可正常加载，YAML 预览正确
2. Phase 2 ✅：Pipeline 结果页展示 DAG 图、时间线、验证面板，5 种技能验证逻辑覆盖完整
3. Phase 3 ✅：task_results.py 已无旧 inline renderers，完全委托 viz_skill
4. 全部 ✅：`pytest tests/ -v` 确认 225 tests 全部通过，0 失败

## 当前状态

- **225 tests passing, 7 skipped, 0 failures**
- **2 commits pushed to main**: `e6426f9` (nested expander fix) + `c1d4fc1` (scope + slider fixes)
- **Phase 1 + Phase 2 + Phase 3 全部完成**，所有功能已实现并验证
- 临时文件已清理（screenshots、.playwright-mcp/）
