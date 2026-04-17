# 多配置方案（Profiles）管理系统

## Context

当前系统只支持单一的全局 server/token/owner 配置（`web/data/settings.json`）。实际使用中，用户需要在多个 CloudPSS 服务器之间切换（清华内部服务器 vs 公开服务器 vs 自定义），每个服务器对应不同的 token 和 owner。目前切换需要手动修改全局设置，操作繁琐。

需求：实现多配置方案管理，类似 LLM API 多 profile 管理模式。用户可以创建多个配置方案（每个方案包含 server/token/owner），在创建任务时选择一个方案使用。

## 新数据模型

```json
{
  "profiles": [
    {
      "id": "prof_a1b2c3d4",
      "name": "清华内部",
      "server_preset": "internal",
      "server_url": "",
      "token": "",
      "user_name": "chenying",
      "is_default": true,
      "created_at": "2026-04-17T10:00:00"
    }
  ],
  "active_profile_id": "prof_a1b2c3d4"
}
```

- `server_preset`: `internal` / `public` / `custom`
- `is_default`: 任务创建时的默认选择
- `active_profile_id`: 当前全局激活的方案

## 修改文件清单

| # | 文件 | 说明 |
|---|------|------|
| 1 | `web/components/settings.py` | 数据层（迁移/CRUD）+ UI 重写（左侧列表+右侧编辑） |
| 2 | `web/components/task_create.py` | 顶部添加方案选择器，RID 规范化用选中 profile 的 user_name |
| 3 | `web/core/task_executor.py` | auth 注入改用 task.config 中 `_profile_id` 对应的 profile |
| 4 | `web/app.py` | 启动时 apply active profile |

## 实施步骤

### Phase 1: settings.py 数据层
- `generate_profile_id()` → 8 位随机字符串
- `migrate_settings()` → 旧 flat 格式→新 profiles 数组（幂等）
- `get_active_profile()` / `get_default_profile_id()` / `get_profile_by_id()`
- `save_profile()` / `delete_profile()` / `set_active_profile()` / `set_default_profile()`
- `apply_settings()` 改为 `apply_profile(profile)` 接受 profile dict

### Phase 2: settings.py UI 重写
- 左侧：profile 列表（名称 + 服务器图标 + default/active 标记）+ `+ 新增方案`
- 右侧：编辑表单（名称/服务器预设/自定义URL/Token/用户名）+ 操作按钮（设为默认/激活/删除）
- 底部：当前状态 + 连接测试

### Phase 3: task_create.py 集成
- 任务创建表单顶部添加 profile 下拉选择器（默认 `is_default` profile）
- `_get_current_user()` 改为接受 `profile_id` 参数
- `_load_example()` 使用选中 profile 的 token 和 user_name
- `_confirm_and_run()` 在 task.config 中存入 `_profile_id`

### Phase 4: task_executor.py 集成
- `_inject_auth()` 从 `task.config["_profile_id"]` 查找 profile，fallback 到 active
- `_apply_server()` 签名从 `settings: dict` 改为 `profile: dict`

### Phase 5: app.py 启动
- 启动时调用 `apply_profile(active_profile)` 写入 token 和 env vars

## 迁移策略
首次加载旧版 `settings.json` 时自动迁移为 profiles 数组，保留所有原有数据。

## 验证方式
1. 设置页创建 2 个 profile → 切换激活 → 连接测试
2. 创建任务 → 方案选择器显示所有 profile → 选择不同方案加载示例
3. 执行任务 → 使用任务关联 profile 的 auth
4. 删除 profile → 关联的旧任务 fallback 到 active profile
