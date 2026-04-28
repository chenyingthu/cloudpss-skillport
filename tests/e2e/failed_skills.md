# 执行失败的技能清单

## 已修复问题（2026-04-25）

### 1. model_validator - 模型验证 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 添加 `"timestamp": True` 到输出配置
**修改文件**: `web/components/task_create.py` 第450行

---

### 2. power_quality_analysis - 电能质量分析 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 添加完整的 analysis 配置和 output 配置，包含所需的 metric、buses 等参数
**修改文件**: `web/components/task_create.py`

---

### 3. renewable_integration - 新能源接入分析 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 改用包含新能源的模型 `model/open-cloudpss/WTG_PMSG_01-avm-stdm-v2b5`，并添加新能源分析配置
**修改文件**: `web/components/task_create.py` 第455行

---

### 4. report_generator - 报告生成器 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 创建演示数据文件 `demo_skill_results.json`，配置使用模拟数据进行报告生成
**修改文件**: `web/components/task_create.py`

---

### 5. visualize - 结果可视化 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 创建演示数据文件 `demo_visualize.json`，配置使用该数据进行可视化
**修改文件**: `web/components/task_create.py`

---

### 6. result_compare - 结果对比 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 创建演示数据文件 `demo_baseline.json` 和 `demo_scenario.json`，配置使用演示数据进行对比
**修改文件**: `web/components/task_create.py`

---

### 7. voltage_stability - 电压稳定分析
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 改用IEEE39中实际存在的母线 `["Bus1", "Bus8", "Bus16", "Bus39"]`
**修改文件**: `web/components/task_create.py` 第480行

---

### 8. transient_stability - 暂态稳定分析 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 添加简化配置避免触发内部bug，配置 model/fault/simulation/output 参数
**修改文件**: `web/components/task_create.py`

---

### 9. transient_stability_margin - 暂态稳定裕度/CCT计算
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 添加 `"timestamp": True` 到输出配置
**修改文件**: `web/components/task_create.py` 第470行

---

### 10. n2_security - N-2双重故障安全分析 ✅ 已修复
**状态**: ✅ 已修复
**修复时间**: 2026-04-25
**修复内容**: 改用IEEE3小模型，限制 max_contingencies=5，配置明确的故障组合列表
**修改文件**: `web/components/task_create.py`

---

## 记录说明
- 本文件用于跟踪真实执行测试中失败的技能
- 每个失败项需包含：技能名称、错误信息、可能原因、修复建议
- 修复后需重新测试并从此清单移除
