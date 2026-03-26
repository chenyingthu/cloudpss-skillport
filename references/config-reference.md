# CloudPSS 技能配置参考

## 配置结构

所有技能配置遵循统一结构：

```yaml
skill: <skill_name>

auth:
  token_file: .cloudpss_token  # 或 token: "直接指定"

model:
  rid: model/holdme/IEEE39     # 模型RID或本地路径
  source: cloud                # cloud 或 local

# 技能特定配置...

output:
  format: json                 # json, csv, yaml
  path: ./results/             # 输出目录
  prefix: <skill_name>         # 文件名前缀
  timestamp: true              # 添加时间戳
```

## 各技能配置详情

### power_flow（潮流计算）

```yaml
skill: power_flow

algorithm:
  type: newton_raphson         # newton_raphson 或 fast_decoupled
  tolerance: 1.0e-6           # 收敛容差
  max_iterations: 100         # 最大迭代次数
```

**等待时间**：最大120秒，轮询间隔2秒

### emt_simulation（EMT仿真）

```yaml
skill: emt_simulation

simulation:
  duration: 5.0               # 仿真时长（秒）
  step_size: 0.0001           # 积分步长（秒）
  timeout: 300                # 最大等待时间（秒）

output:
  channels: []                # 空表示导出全部通道
```

**等待时间**：最大300秒，轮询间隔3秒

### batch_powerflow（批量潮流）

```yaml
skill: batch_powerflow

models:                       # 多个模型列表
  - rid: model/holdme/IEEE39
    name: IEEE39
    source: cloud
  - rid: model/holdme/IEEE3
    name: IEEE3
    source: cloud
```

**等待时间**：每个模型120秒

### n1_security（N-1安全校核）

```yaml
skill: n1_security

analysis:
  branches: []                # 空表示检查全部支路
  check_voltage: true         # 检查电压
  check_thermal: true         # 检查热稳定
  voltage_threshold: 0.05     # 电压越限阈值（标幺值）
  thermal_threshold: 1.0      # 热稳定阈值（标幺值）
```

**等待时间**：每个支路120秒

### param_scan（参数扫描）

```yaml
skill: param_scan

scan:
  component: "Load_1"         # 元件ID或名称
  parameter: "P"              # 参数名
  values: [10, 20, 30, 40, 50] # 参数值列表
  simulation_type: power_flow # power_flow 或 emt
```

**等待时间**：每个参数点120秒

### waveform_export（波形导出）

```yaml
skill: waveform_export

source:
  job_id: "abc123"            # 仿真任务ID

export:
  plots: [0, 1]               # 分组索引，空表示全部
  channels: []                # 通道名称，空表示全部
  time_range:                 # 时间范围（可选）
    start: 2.0
    end: 5.0
```

## 状态码说明

- `status = 0`：运行中
- `status = 1`：已完成（成功）
- `status = 2`：失败

## 环境变量

配置中支持环境变量：

```yaml
auth:
  token: "${CLOUDPSS_TOKEN}"
model:
  rid: "${MODEL_RID:-model/holdme/IEEE39}"  # 支持默认值
```

## 默认模型

- **IEEE39**：`model/holdme/IEEE39` - 39节点系统，适合潮流和N-1
- **IEEE3**：`model/holdme/IEEE3` - 3节点系统，适合EMT暂态
