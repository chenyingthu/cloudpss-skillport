# CloudPSS 前端技能测试报告

**测试时间:** 2026-04-18
**测试范围:** 15 个代表性技能（共 50 个技能）
**测试工具:** Playwright MCP
**前端地址:** http://127.0.0.1:8702

---

## 📊 测试结果摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | 15 |
| 通过 | 7 (46.7%) |
| 失败 | 7 |
| 超时 | 1 |
| 总耗时 | 550.8 秒 |

---

## ✅ 通过的技能 (7个)

| # | 技能名称 | 类别 | 耗时 |
|---|----------|------|------|
| 1 | power_flow (潮流计算) | 仿真执行 | 27.6s |
| 2 | emt_simulation (EMT暂态仿真) | 仿真执行 | 33.2s |
| 3 | batch_powerflow (批量潮流计算) | 批量与扫描 | 27.4s |
| 4 | transient_stability (暂态稳定分析) | 稳定性分析 | 21.2s |
| 5 | harmonic_analysis (谐波分析) | 电能质量 | 53.9s |
| 6 | topology_check (拓扑检查) | 模型与拓扑 | 21.3s |
| 7 | short_circuit (短路电流计算) | 仿真执行 | 51.9s |

---

## ❌ 失败的技能 (7个)

### 1. visualize (结果可视化)
- **错误:** `ValueError: list.index(x): x not in list`
- **位置:** `web/components/task_create.py:362` (_edit_config)
- **状态:** 配置验证通过后前端渲染失败

### 2. report_generator (报告生成)
- **错误:** `ValueError: list.index(x): x not in list`
- **位置:** `web/components/task_create.py:362` (_edit_config)
- **状态:** 与 visualize 相同的前端渲染问题

### 3. vsi_weak_bus (VSI弱母线分析)
- **错误:** `Variable "$rid" got invalid value ""`
- **状态:** 示例配置中 rid 参数为空字符串

### 4. study_pipeline (流程编排)
- **错误:** 无法导航到技能页面
- **状态:** 前端导航找不到该技能按钮

### 5. contingency_analysis (预想事故分析)
- **错误:** `NameError: name 'base_model' is not defined`
- **状态:** 后端执行时变量未定义

### 6. param_scan (参数扫描分析)
- **错误:** 配置验证失败 (6 个错误)
- **状态:** 示例配置不符合 schema

### 7. reactive_compensation_design (无功补偿设计)
- **错误:** 配置验证失败 (1 个错误)
- **状态:** 示例配置不符合 schema

---

## ⏱️ 超时的技能 (1个)

### n1_security (N-1安全校核)
- **耗时:** 198.3s (超过 180s 超时限制)
- **状态:** 执行时间超过配置的超时时间
- **建议:** 增加超时时间或优化执行性能

---

## 🔧 修复任务

已创建以下修复任务：

1. **#46** - 修复前端渲染问题 (visualize, report_generator)
2. **#44** - 修复示例配置问题 (vsi_weak_bus)
3. **#47** - 修复导航问题 (study_pipeline)
4. **#43** - 修复后端执行问题 (contingency_analysis)
5. **#45** - 修复配置验证问题 (param_scan, reactive_compensation_design)

---

## 📁 测试报告文件

- **HTML 报告:** `tests/e2e/reports/test_report.html`
- **JSON 数据:** `tests/e2e/reports/test_report.json`
- **测试脚本:** `tests/e2e/test_all_skills.py`

---

## 🚀 下一步行动

1. **立即修复:** 处理 #46 和 #44 的前端和配置问题
2. **验证修复:** 重新测试失败的技能
3. **全面测试:** 修复完成后执行全部 50 个技能的测试
4. **性能优化:** 调查 n1_security 的超时问题

---

*报告生成时间: 2026-04-18T12:00:29*
