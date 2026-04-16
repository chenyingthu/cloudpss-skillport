# 技能执行日志可视化：让技能调用过程可见

## Context

用户点击"确认执行"后，技能在后台执行，前端只显示"🔄 运行中"，用户看不到：
- 技能是否真的开始执行了？
- 当前执行到哪一步了？
- 有没有出错？错在哪里？

**目标**：在技能执行过程中，实时显示日志信息，让用户看到执行进度和诊断信息。

## 现状分析

### 现有日志机制（已完备）

**cloudpss-toolkit 已有完善的日志模式**：
- 35+ 技能文件已有 `def log()` 模式
- `LogEntry` 数据类：`timestamp`, `level`, `message`, `context`
- `SkillResult.logs` 存储所有日志

**示例日志**（power_flow.py）：
```python
log("INFO", "认证成功")
log("INFO", f"模型：{model.name} ({model.rid})")
log("INFO", "运行潮流计算...")
log("INFO", f"潮流计算完成")
```

**示例日志**（n1_security.py）：
```python
log("INFO", f"[{i + 1}/{len(branches)}] 停运支路：{branch['name']}")
log("INFO", f"  -> N-1 通过")
log("WARNING", f"  -> 发现电压/热稳定违规")
log("ERROR", f"  -> N-1 失败：潮流不收敛")
```

### 断裂的链路

**问题**：`task_executor.py` 调用 `skill.run()` 后，**丢弃了 `result.logs`**：

```python
result = skill.run(task.config)
task.result_data = result.data
task.artifacts = [...]  # 保存了
task.metrics = getattr(result, "metrics", {})  # 保存了
# result.logs 被丢弃了！
```

**Task 数据模型没有 logs 字段**

**前端轮询看不到日志**

## 改进方案

### 方案 A: 最小改动（已实施）

**核心思路**：保存技能日志到 task 文件，前端轮询显示。

**修改文件**：
1. `web/core/task_store.py` - 添加 logs 字段
2. `web/core/task_executor.py` - 保存 result.logs
3. `web/components/task_results.py` - 显示日志

**效果示例**：
```
📋 执行日志 (8 条)                            [▼]
  17:35:42 ℹ️ 认证成功
  17:35:43 ℹ️ 模型：10 机 39 节点标准测试系统 (model/chenying/IEEE39)
  17:35:43 ℹ️ 运行潮流计算...
  17:35:44 ℹ️ 从 CloudPSS 获取数据...
  17:35:47 ℹ️ 潮流计算完成
```

## 修改文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `web/core/task_store.py` | 添加 `logs` 字段到 Task 数据类 |
| 修改 | `web/core/task_executor.py` | 保存 `result.logs` 到 task.logs |
| 修改 | `web/components/task_results.py` | 新增日志显示区域（轮询中） |

## cloudpss-toolkit 修改需求

**好消息：不需要修改！**

现有 35+ 技能已经有完善的 `log()` 模式，日志直接返回到 `SkillResult.logs`。

## 验证方式

1. **功能验证**：
   - 执行 power_flow → 前端显示"认证成功"、"模型：xxx"、"运行潮流计算..."等日志
   - 执行 n1_security → 前端显示"[1/46] 停运支路：xxx"、"N-1 通过"等日志
   - 执行 study_pipeline → 前端显示每个步骤的开始/结束日志

2. **错误诊断验证**：
   - 故意配置错误的 token → 前端显示"❌ 认证失败：Invalid token"
   - 配置不存在的模型 → 前端显示"❌ 模型加载失败：..."

## 实现阶段

**Phase 1: 基础日志显示** ✅ 已完成
- 修改 task_store.py 添加 logs 字段
- 修改 task_executor.py 保存日志
- 修改 task_results.py 显示日志
- 验证 3-5 个技能的日志显示

**Phase 2 (可选): 完整覆盖**
- 确认所有 37+ 技能都有 log() 调用
- 补充缺失技能的日志记录
- 验证日志格式一致性

**Phase 3 (可选): 实时性增强**
- 如果需要真正的实时日志流，修改 toolkit 添加 SkillContext
- 添加日志级别过滤（DEBUG/INFO/WARNING/ERROR）
- 添加日志搜索/过滤功能
