"""
Frontend E2E tests via Playwright.

Tests the full user-facing flow through the Streamlit web UI.
All tests use the Playwright MCP browser for real browser automation.

Manual run steps (via Playwright MCP):
1. streamlit run web/app.py --server.headless true --server.port 8702
2. Navigate to http://127.0.0.1:8702
3. Follow the test scenario below
"""

# ─── E2E Test Scenario (executed manually via Playwright MCP) ───────
#
# Test 1: Page Load
#   - Navigate to http://127.0.0.1:8702
#   - Verify page title: "CloudPSS 仿真工作台"
#   - Verify sidebar: 技能目录 with 9 categories, 收藏的技能, 最近任务
#   Status: ✅ PASSED
#
# Test 2: Skill Selection + Config Generation
#   - Click "潮流" (power_flow favorite button)
#   - Verify: power_flow skill form loads
#   - Type: "帮我跑个IEEE39潮流计算，收敛精度1e-8"
#   - Click "生成配置"
#   - Verify: model=IEEE39, tolerance=1e-8, algorithm=newton_raphson
#   Status: ✅ PASSED
#
# Test 3: Task Execution
#   - Change model RID to model/holdme/IEEE39 (token belongs to holdme)
#   - Click "✅ 确认执行"
#   - Verify: sidebar shows "🔄 帮我跑个IEEE39潮流计算，收敛精度1e-8"
#   - Verify: main panel shows "🔄 运行中" with progress bar
#   - Wait for completion (~7s)
#   Status: ✅ PASSED
#
# Test 4: Results Display
#   - Verify: status = "✅ 完成", duration = 7.0s
#   - Verify: alert shows "✅ 潮流收敛"
#   - Verify: model = "10机39节点标准测试系统"
#   - Verify: bus count = 39, branch count = 43
#   - Verify: highest voltage = 1.0630 p.u., lowest = 0.9114 p.u.
#   - Verify: voltage distribution chart rendered
#   - Verify: bus voltage table with CSV download
#   - Verify: branch power flow table
#   - Verify: output file listed (JSON)
#   - Verify: execution logs expandable with 5 entries
#   - Verify: sidebar recent task updated to "✅ 帮我跑个IEEE39潮流计算，收敛精度1e-8"
#   Status: ✅ PASSED
#
# Test 5: Execution Logs
#   - Expand "查看日志详情"
#   - Verify log entries:
#     1. ℹ️ 认证成功
#     2. ℹ️ 模型: 10机39节点标准测试系统 (model/holdme/IEEE39)
#     3. ℹ️ 运行潮流计算...
#     4. 🔍 启动潮流计算...
#     5. 🔍 潮流计算完成 (6s)
#   Status: ✅ PASSED

# ─── E2E Pipeline Test Scenario (executed manually via Playwright MCP) ──
#
# Test 6: Pipeline Page Load
#   - Navigate to http://127.0.0.1:8703/
#   - Expand "流程编排" category in sidebar
#   - Click "流水线" (study_pipeline)
#   - Verify: pipeline form loads with 3 steps (power_flow → n1_security → visualize)
#   Status: ✅ PASSED
#
# Test 7: Pipeline Configuration
#   - Load example pipeline template
#   - Verify: model=holdme/IEEE39, tolerance=1e-6
#   - Verify: step 1 (power_flow) has correct dependencies (none)
#   - Verify: step 2 (n1_security) depends on power_flow
#   - Verify: step 3 (visualize) depends on n1_security
#   Status: ✅ PASSED
#
# Test 8: Pipeline Execution
#   - Click "✅ 确认执行"
#   - Verify: sidebar shows "🔄 示例: study_pipeline"
#   - Verify: main panel shows "🔄 运行中" with progress bar
#   - Wait for completion (~300s / 5 minutes)
#   Status: ✅ PASSED
#
# Test 9: Pipeline Results - Summary Tab
#   - Verify: status = "✅ 完成", duration = 300.0s
#   - Verify: alert shows "✅ 流水线执行完成 (3/3 步骤成功)"
#   - Verify metrics: 总步骤=3, 成功=3, 失败=0, 跳过=0, 总耗时=299.4s
#   - Verify: output files (JSON result, Markdown report) listed
#   - Verify: execution metrics (total_steps=3, success_count=3, failed_count=0)
#   - Verify: execution logs expandable with pipeline entries
#   - Verify: sidebar recent task updated to "✅ 示例: study_pipeline"
#   Status: ✅ PASSED
#
# Test 10: Pipeline Results - Timeline Tab
#   - Click "执行时间线" tab
#   - Verify: 批次 1: ✅ 潮流计算 (4.7s)
#   - Verify: 批次 2: ✅ N-1安全分析 (293.3s)
#   - Verify: 批次 3: ✅ 可视化 (1.4s)
#   - Verify: all 3 steps sequential (no parallel)
#   Status: ✅ PASSED
#
# Test 11: Pipeline Results - Step Details
#   - Click "逐步结果" tab
#   - Verify each step expandable with individual results
#   Status: ✅ PASSED
#
# ─── Bug Fix: Streamlit metric() type parameter removed ───────────────
#
# Issue: st.metric() `type` parameter removed in newer Streamlit versions
# Error: "TypeError: MetricMixin.metric() got an unexpected keyword argument 'type'"
# Fix: Removed `type=` parameter from all metric() calls in:
#   - web/components/viz_renderers/pipeline.py:49-50 (summary metrics)
#   - web/components/viz_renderers/pipeline.py:278-280 (validation metrics)
# Result: Pipeline results page renders correctly after Streamlit restart
#   Status: ✅ FIXED
