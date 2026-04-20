# 项目开发指南

本文档为接续开发的学生提供完整的项目环境搭建和开发指南。

---

## 一、环境要求

| 要求 | 版本 | 说明 |
|-----|------|------|
| Python | >= 3.8 | 推荐 3.10+ |
| pip | 最新版 | 用于安装依赖 |
| Git | 任意版本 | 代码版本控制 |
| Node.js | >= 16 | Playwright E2E测试需要 |

---

## 二、极速安装（推荐）

```bash
# 1. 克隆项目
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-sim-skill.git
cd cloudpss-sim-skill

# 2. 安装 cloudpss-toolkit（必须先装！）
git clone https://github.com/chenyingthu/CloudPSS_skillhub.git ../CloudPSS_skillhub
cd ../CloudPSS_skillhub
pip install -e .

# 3. 返回项目目录并安装依赖
cd ../cloudpss-sim-skill

# 4. 配置 CloudPSS Token（必须！）
# 访问 https://www.cloudpss.net → 个人中心 → API Token
echo "你的token" > .cloudpss_token

# 5. 安装项目依赖（可选，用于本地测试）
pip install -e ".[dev]"

# 6. 安装 Playwright（用于E2E测试）
pip install playwright pytest-playwright
playwright install chromium
```

---

## 三、快速验证安装

### 3.1 验证 toolkit 安装

```bash
python -m cloudpss_skills list
# 应输出 50 个技能列表
```

### 3.2 验证 Web 应用

```bash
# 启动 Web 界面
streamlit run web/app.py --server.port=8502

# 浏览器访问 http://localhost:8502
```

### 3.3 运行单元测试

```bash
# 运行所有单元测试（不需网络）
pytest tests/ -v --ignore=tests/e2e/

# 预期结果: 291 passed, 7 skipped
```

---

## 四、项目结构

```
cloudpss-sim-skill/
├── web/                    # Streamlit Web 应用
│   ├── app.py             # 主应用入口
│   ├── components/        # UI 组件
│   │   ├── task_create.py     # 任务创建页面
│   │   ├── settings.py        # 设置页面（含多配置Profile）
│   │   ├── pipeline_editor.py # 流程编排编辑器
│   │   └── ...
│   ├── core/              # 核心逻辑
│   │   ├── skill_catalog.py   # 技能目录
│   │   ├── task_executor.py   # 任务执行器
│   │   └── task_store.py      # 任务存储
│   └── data/              # 本地数据存储
│
├── scripts/               # 命令行工具
│   ├── smart_config.py       # 自然语言配置生成
│   ├── component_mapper.py   # 模型元件查询
│   ├── channel_helper.py     # 通道名称推断
│   ├── fuzzy_matcher.py      # 拼写纠错
│   ├── friendly_validator.py # 配置验证
│   └── interactive_wizard.py # 交互式向导
│
├── tests/                 # 测试代码
│   ├── test_*.py         # 单元测试（291个）
│   └── e2e/              # E2E 测试
│       └── test_all_skills.py # 48技能全量测试
│
├── configs/               # 生成的配置文件（gitignore）
├── results/              # 仿真结果输出（gitignore）
│
├── cloudpss-sim-v2.skill # Claude Code Skill 定义文件
├── CLAUDE.md              # Claude Code 开发指南
├── README.md              # 用户使用文档
├── pyproject.toml         # Python 项目配置
└── .gitignore             # Git 忽略配置
```

---

## 五、开发指南

### 5.1 启动 Web 应用

```bash
# 开发模式启动（热重载）
streamlit run web/app.py --server.port=8502 --server.reload=true

# 生产模式启动
streamlit run web/app.py --server.port=8502 --server.headless=true
```

### 5.2 运行测试

#### 单元测试（快速，无需网络）

```bash
# 运行所有单元测试
pytest tests/ -v --ignore=tests/e2e/

# 运行特定测试
pytest tests/test_config_schema_validity.py -v
pytest tests/test_parameter_extraction.py -v
pytest tests/test_mocked_execution.py -v
```

#### E2E 测试（需要 CloudPSS Token）

```bash
# 确保 token 已配置
cat .cloudpss_token

# 运行完整 E2E 测试
python tests/e2e/test_all_skills.py --headless

# 运行特定技能测试
python tests/e2e/test_all_skills.py --skills power_flow,emt_simulation --headless
```

### 5.3 代码规范

```bash
# 代码格式化
black web/ tests/

# 类型检查（如果使用）
mypy web/
```

---

## 六、常见问题

### Q1: 提示 "cloudpss-toolkit 未安装"

```bash
# 确认 toolkit 已安装
pip show cloudpss-toolkit

# 如果未安装，重新安装
cd ../cloudpss-toolkit
pip install -e .
```

### Q2: Web 界面无法启动（端口被占用）

```bash
# 查看端口占用
lsof -i:8502

# 杀掉占用进程
kill -9 <PID>

# 或使用其他端口
streamlit run web/app.py --server.port=8503
```

### Q3: E2E 测试失败（找不到技能按钮）

```bash
# 确认 Playwright 已安装
pip install playwright pytest-playwright
playwright install chromium

# 如果仍然失败，可能是页面结构变化，需要更新测试代码
```

### Q4: Token 验证失败

```bash
# 确认 token 文件存在且有效
cat .cloudpss_token

# 测试 token 是否有效
curl -H "Authorization: Bearer $(cat .cloudpss_token)" https://api.cloudpss.net/v1/me
```

---

## 七、关键文件说明

| 文件 | 用途 |
|-----|------|
| `web/components/task_create.py` | 任务创建页面，包含配置生成和执行逻辑 |
| `web/components/settings.py` | 设置页面，管理多配置方案（Profile） |
| `web/core/task_executor.py` | 任务执行器，调用 cloudpss-toolkit |
| `web/core/skill_catalog.py` | 技能目录，加载和管理 50 个技能 |
| `scripts/smart_config.py` | 自然语言配置生成器 |

---

## 八、测试结果统计

| 测试类型 | 数量 | 说明 |
|---------|------|------|
| 单元测试 | 291 | 需 token 可选，大部分可离线运行 |
| E2E 测试 | 48 | 需要完整环境，测试所有技能 |
| 测试通过率 | 72.9% | 35/48 技能通过（见下方备注） |

**E2E 测试备注：**
- 通过: 35 个技能（72.9%）
- 失败: 8 个（需要真实 job_id 数据）
- 超时: 5 个（算法执行时间过长）

**不属于代码问题的失败：**
- 执行超时 (5个): n1_security, n2_security, maintenance_security, reactive_compensation_design, study_pipeline
- 需要真实数据 (8个): result_compare, visualize, waveform_export 等需要先运行仿真任务

---

## 九、接续开发建议

### 9.1 优先任务

1. **优化超时技能**: 5个超时技能需要算法优化或异步改造
2. **添加数据 mock**: 8个需要真实数据的技能可添加测试用 mock 数据
3. **完善文档**: 更新 CLAUDE.md 中的测试数量描述

### 9.2 代码规范

- 使用 `black` 格式化代码
- 添加类型注解（推荐使用）
- 新增测试用例覆盖新功能
- 提交前运行 `pytest tests/ -v`

### 9.3 调试技巧

```python
# 在代码中添加调试输出
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*最后更新: 2026-04-20*
*维护者: CloudPSS Research Team*