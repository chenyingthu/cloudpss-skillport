# 开发需求：增强 visualize skill 适配 Pipeline 工作流

## 状态

- ✅ 需求 1：修复 SDK PowerFlowResult 处理（已完成，commit 3f6d91e）
- ✅ 需求 2：新增 source.data 直接数据通道（已完成，commit 3f6d91e）
- ✅ 需求 3：PowerFlowResult 历史回放（已完成，commit 3f6d91e + 003d6cf）
- ✅ 需求 4：输出格式容错（已完成，commit 003d6cf）
- ✅ 需求 5：time_data 作用域修复（已完成，commit 003d6cf）
- ✅ 需求 6：CJK 字体支持（已完成，commit 003d6cf）
- ✅ 全链路验证：pipeline (power_flow → n1_security → visualize) 3/3 成功
- ✅ 图表验证：39 个母线电压条形图正确渲染，含中文字体

## 已完成需求回顾

### 需求 1：修复 SDK PowerFlowResult 处理（已完成）
### 需求 2：新增 source.data 直接数据通道（已完成）

## 新发现问题：fetch_job_with_result 缺少 PowerFlowResult 历史回放

### 问题描述

需求 1 和 2 完成后，pipeline 中 visualize 步骤仍然失败：
```
✗ 可视化: 失败 - 潮流计算结果 buses 表为空
```

**根因**：`fetch_job_with_result` (`cloudpss_skills/core/utils.py:17`) 只对 EMT 历史任务做了回放（检测 `getPlots()` 返回空时调用 `replay_historical_emt_result`），但对 `PowerFlowResult` 的 `getBuses()` 也返回空历史任务，没有做同样处理。

**验证过程**：
```python
job = Job.fetch(job_id)
result = job.result
result.getBuses()  # 返回 [] 空列表

# 手动调用回放后
replayed = replay_historical_emt_result(job)
replayed.getBuses()  # 返回 39 条母线数据 ✅
```

`replay_historical_emt_result` 函数本身是通用的——它通过 `job.context[0]` 确定结果类型（`'function/CloudPSS/power-flow'` → `PowerFlowResult`），所以可以直接复用于 PowerFlowResult。

### 修改要求

**文件**: `cloudpss_skills/core/utils.py`

**位置**: `fetch_job_with_result` 函数，第 17-43 行

**当前逻辑**:
```python
if hasattr(result, "getPlots"):
    try:
        if len(list(result.getPlots())) == 0 and getattr(job, "output", None):
            replayed = replay_historical_emt_result(job)
            ...
```

**修改为**:
```python
# EMT 历史回放：getPlots() 为空时
if hasattr(result, "getPlots"):
    try:
        if len(list(result.getPlots())) == 0 and getattr(job, "output", None):
            replayed = replay_historical_emt_result(job)
            if replayed is not None:
                job._result = replayed
                result = replayed
    except Exception as e:
        logger.debug(f"历史 EMT 结果回放失败，回退到SDK默认结果: {e}")

# PowerFlowResult 历史回放：getBuses() 为空时
if hasattr(result, "getBuses"):
    try:
        if len(result.getBuses()) == 0 and getattr(job, "output", None):
            replayed = replay_historical_emt_result(job)
            if replayed is not None:
                job._result = replayed
                result = replayed
    except Exception as e:
        logger.debug(f"历史潮流结果回放失败，回退到SDK默认结果: {e}")
```

**验收标准**:
- 对历史潮流计算任务（已完成），`fetch_job_with_result` 返回的 `PowerFlowResult.getBuses()` 包含数据
- EMT 历史回放逻辑不受影响
- 新运行的任务（输出流仍在）无需回放也能正常获取

## 已完成需求 1 详情（仅供参考）

**文件**: `cloudpss_skills/builtin/visualize.py`

## 已完成需求 2 详情（仅供参考）

## 测试建议

```bash
# 1. 单独测试 visualize + power_flow job_id
python -m cloudpss_skills run --config configs/visualize_pf.yaml

# 2. 测试 pipeline 全链路
python -m cloudpss_skills run --config configs/pipeline.yaml

# 3. 验证向后兼容（本地文件方式）
python -m cloudpss_skills run --config configs/visualize_file.yaml
```
