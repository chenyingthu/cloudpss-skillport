# CloudPSS 技能配置参考

## 配置结构

所有技能配置遵循统一结构：

```yaml
skill: <skill_name>

auth:
  token_file: .cloudpss_token  # 或 token: "直接指定"

model:
  rid: model/chenying/IEEE39     # 模型RID或本地路径
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

### emt_simulation（EMT暂态仿真）

```yaml
skill: emt_simulation

simulation:
  duration: 5.0               # 仿真时长（秒）
  step_size: 0.0001           # 积分步长（秒）
  timeout: 300                # 最大等待时间（秒）

output:
  channels: []                # 空表示导出全部通道
```

### emt_fault_study（EMT故障研究）

```yaml
skill: emt_fault_study

fault:
  location: "Bus1"            # 故障位置
  type: "three_phase"         # three_phase, single_phase, line_ground
  start_time: 0.1             # 故障开始时间（秒）
  duration: 0.05              # 故障持续时间（秒）

simulation:
  duration: 5.0
  step_size: 0.0001
```

### short_circuit（短路电流计算）

```yaml
skill: short_circuit

fault:
  bus: "Bus1"                 # 故障母线
  type: "three_phase"         # three_phase, single_phase, line_to_line, double_line_ground
```

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

### n2_security（N-2双重故障安全分析）

```yaml
skill: n2_security

analysis:
  branches: []                # 待检查支路（空表示全部）
  branch_pairs: []            # 双元件组合（空表示自动枚举）
  check_voltage: true
  check_thermal: true
  voltage_min: 0.95           # 电压下限
  voltage_max: 1.05           # 电压上限
  thermal_limit: 1.0          # 热稳定限值
  max_combinations: 100       # 最大组合数
  include_critical_pairs: true # 包含关键组合
```

### emt_n1_screening（EMT N-1安全筛查）

```yaml
skill: emt_n1_screening

analysis:
  branches: []                # 空表示全部
  duration: 5.0               # 每次EMT仿真时长
```

### contingency_analysis（预想事故分析）

```yaml
skill: contingency_analysis

analysis:
  contingencies: []           # 预想事故列表（空表示自动生成）
  check_voltage: true
  check_thermal: true
```

### maintenance_security（检修安全校核）

```yaml
skill: maintenance_security

analysis:
  outages:                    # 检修元件列表
    - "Gen_1"
  check_voltage: true
  check_thermal: true
```

### batch_powerflow（批量潮流）

```yaml
skill: batch_powerflow

models:                       # 多个模型列表
  - rid: model/chenying/IEEE39
    name: IEEE39
    source: cloud
  - rid: model/chenying/IEEE3
    name: IEEE3
    source: cloud
```

### param_scan（参数扫描）

```yaml
skill: param_scan

scan:
  component: "Load_1"         # 元件ID或名称
  parameter: "P"              # 参数名
  values: [10, 20, 30, 40, 50] # 参数值列表
  simulation_type: power_flow # power_flow 或 emt
```

### fault_clearing_scan（故障清除时间扫描）

```yaml
skill: fault_clearing_scan

scan:
  fault_location: "Bus1"      # 故障位置
  clearing_times: [0.05, 0.1, 0.15, 0.2]  # 清除时间列表
```

### fault_severity_scan（故障严重度扫描）

```yaml
skill: fault_severity_scan

scan:
  fault_locations: ["Bus1", "Bus2", "Bus3"]  # 故障位置列表
```

### batch_task_manager（批处理任务管理）

```yaml
skill: batch_task_manager

tasks:                        # 任务列表
  - name: "task1"
    skill: "power_flow"
    config: {}
```

### config_batch_runner（配置批量运行器）

```yaml
skill: config_batch_runner

configs:                      # 配置文件列表
  - "configs/scenario1.yaml"
  - "configs/scenario2.yaml"
```

### orthogonal_sensitivity（正交敏感性分析）

```yaml
skill: orthogonal_sensitivity

analysis:
  parameters:                 # 待扫描参数
    - component: "Load_1"
      parameter: "P"
      values: [10, 20, 30]
  orthogonal_array: L9        # 正交表类型
```

### voltage_stability（电压稳定分析）

```yaml
skill: voltage_stability

analysis:
  method: "continuation"      # 分析方法
  target_bus: "Bus7"          # 目标母线
```

### transient_stability（暂态稳定分析）

```yaml
skill: transient_stability

fault:
  location: "Bus1"
  type: "three_phase"
  duration: 0.1

analysis:
  monitor_generators: true
  post_fault_duration: 5.0
```

### transient_stability_margin（暂态稳定裕度/CCT计算）

```yaml
skill: transient_stability_margin

fault_scenarios:
  - location: "Bus1"          # 故障位置（必需）
    type: "three_phase"       # three_phase, single_phase, line_ground
    duration: 0.1

generators: []                # 需监控的发电机列表

analysis:
  compute_cct: true           # 计算CCT
  compute_margin: true        # 计算稳定裕度
  margin_baseline: 0.5        # 裕度基准
  max_iterations: 20          # 最大迭代次数
  cct_tolerance: 0.001        # CCT容差
  cct_initial_upper_bound: 1.0
  cct_search_upper_bound: 5.0
  emt_timeout: 300.0
```

### small_signal_stability（小信号稳定分析）

```yaml
skill: small_signal_stability

analysis:
  method: "eigenvalue"        # 特征值分析法
```

### frequency_response（频率响应分析）

```yaml
skill: frequency_response

analysis:
  frequency_range: [0.1, 100] # 频率范围（Hz）
```

### vsi_weak_bus（VSI弱母线分析）

```yaml
skill: vsi_weak_bus

analysis:
  voltage_threshold: 0.05     # 电压阈值（标幺值）
```

### dudv_curve（DUDV曲线生成）

```yaml
skill: dudv_curve

analysis:
  target_bus: "Bus7"          # 目标母线
```

### result_compare（结果对比）

```yaml
skill: result_compare

comparison:
  results:                    # 待对比结果列表
    - path: "results/run1.json"
      name: "场景1"
    - path: "results/run2.json"
      name: "场景2"
```

### visualize（结果可视化）

```yaml
skill: visualize

visualization:
  result_path: "results/xxx.json"  # 结果文件路径
  plot_type: "bar"            # bar, line, pie
```

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

### hdf5_export（HDF5数据导出）

```yaml
skill: hdf5_export

export:
  source_path: "results/xxx.json"
  output_path: "results/data.h5"
```

### disturbance_severity（扰动严重度分析）

```yaml
skill: disturbance_severity

analysis:
  disturbance_location: "Bus1"
```

### compare_visualization（对比可视化）

```yaml
skill: compare_visualization

visualization:
  results:                    # 多场景结果
    - path: "results/run1.json"
      name: "场景1"
    - path: "results/run2.json"
      name: "场景2"
```

### comtrade_export（COMTRADE导出）

```yaml
skill: comtrade_export

export:
  job_id: "abc123"            # 仿真任务ID
  channels: []                # 通道列表（空表示全部）
  output_path: "results/comtrade/"
```

### harmonic_analysis（谐波分析）

```yaml
skill: harmonic_analysis

analysis:
  target_bus: "Bus7"          # 目标母线
  harmonic_orders: [3, 5, 7, 9, 11]  # 谐波次数
```

### power_quality_analysis（电能质量分析）

```yaml
skill: power_quality_analysis

analysis:
  target_bus: "Bus7"
  metrics: ["voltage_sag", "voltage_swell", "interruption"]
```

### reactive_compensation_design（无功补偿设计）

```yaml
skill: reactive_compensation_design

compensation:
  target_bus: "Bus7"          # 补偿母线
  method: "optimal"           # optimal, heuristic
```

### renewable_integration（新能源接入分析）

```yaml
skill: renewable_integration

renewable:
  type: "pv"                  # pv 或 wind
  bus: "Bus8"                 # 接入母线
  capacity: 100               # 额定容量（MW）

analysis:
  scr:
    enabled: true
    threshold: 3.0            # SCR阈值
  voltage_variation:
    enabled: true
    tolerance: 0.05           # 电压变化容差
  harmonic_injection:
    enabled: true
    limits:
      thd: 0.05               # THD限值
  lvrt_compliance:
    enabled: true
    standard: "gb"            # gb, iee, iec
  stability_impact:
    enabled: true
```

### topology_check（拓扑检查）

```yaml
skill: topology_check

check:
  validate_connectivity: true
  report_islands: true
```

### parameter_sensitivity（参数灵敏度分析）

```yaml
skill: parameter_sensitivity

analysis:
  parameters:
    - component: "Load_1"
      parameter: "P"
      variation: 0.1          # 变化比例
```

### auto_channel_setup（自动量测配置）

```yaml
skill: auto_channel_setup

channels:
  auto_add: true              # 自动添加通道
  channel_types: ["voltage", "current", "power"]
```

### auto_loop_breaker（模型自动解环）

```yaml
skill: auto_loop_breaker

loop:
  detect: true
  break_method: "auto"        # 解环方法
```

### model_parameter_extractor（模型参数提取）

```yaml
skill: model_parameter_extractor

extract:
  component_types: ["Load", "Generator", "Transformer"]  # 元件类型
  output_format: "csv"        # csv, json
```

### model_builder（模型构建/修改）

```yaml
skill: model_builder

base_model:
  rid: "model/chenying/IEEE3"
  config_index: 0

modifications:                # 修改操作列表
  - action: "add_component"   # add_component, modify_component, remove_component
    component_type: "Load"
    label: "Load_New"
    parameters:
      P: 100
      Q: 50
    position:
      x: 0.5
      y: 0.5
    pin_connection:
      target_bus: "Bus1"
      pin_name: "0"

output:
  save: true
  branch: "new_branch"        # 可选，保存到分支
  name: "modified_model"
  description: "修改后的模型"
  tags: ["test"]
```

### model_validator（模型验证）

```yaml
skill: model_validator

models:
  - rid: "model/chenying/IEEE39"

validation:
  phases: ["topology", "powerflow"]  # topology, powerflow, emt, parameter
  timeout: 300
  powerflow_tolerance: 1e-6
  emt_duration: 1.0
```

### component_catalog（元件目录）

```yaml
skill: component_catalog

filters:
  tags: []                    # 按标签过滤
  name_pattern: ".*"          # 名称正则
  owner: "*"                  # 所有者

options:
  page_size: 1000
  include_details: true

output:
  format: "json"              # json, csv, console
  path: "results/catalog.json"
  group_by_tag: false
```

### thevenin_equivalent（戴维南等值）

```yaml
skill: thevenin_equivalent

model:
  rid: "model/chenying/IEEE39"
  source: cloud

pcc:
  bus: "bus8"                 # PCC母线名

equivalent:
  system_base_mva: 100.0      # 系统基准容量
  rating_mva: 200             # 可选，提供时顺带计算SCR
```

### model_hub（算例中心）

```yaml
skill: model_hub

action: "status"              # init, status, list_models, clone, push, pull, sync

server:                       # 服务器配置（可选）
  name: "cloudpss-main"
  url: "https://www.cloudpss.net"
  token_file: ".cloudpss_token"

model:                        # 算例配置（按action需要）
  name: "IEEE39"
  rid: "model/chenying/IEEE39"
  local_path: "./models/IEEE39"
  source_server: "cloudpss-main"
  target_server: "cloudpss-mirror"
  description: "IEEE39测试模型"
  tags: ["test"]
  force: false
  parallel: true
  max_workers: 4
```

### study_pipeline（流程编排）

```yaml
skill: study_pipeline

pipeline:                     # 步骤列表
  - name: "潮流计算"
    skill: "power_flow"
    config:
      algorithm:
        type: "newton_raphson"
        tolerance: 1e-6
  - name: "N-1分析"
    skill: "n1_security"
    depends_on: ["潮流计算"]  # 依赖关系
    config:
      analysis:
        check_voltage: true
        check_thermal: true
  - name: "可视化"
    skill: "visualize"
    depends_on: ["N-1分析"]
    config: {}

output:
  path: "./results/"
  prefix: "pipeline"
  generate_report: true

continue_on_failure: false    # 失败是否继续
max_workers: 4                # 最大并行worker数
```

### loss_analysis（网损分析）

```yaml
skill: loss_analysis

analysis:
  target_branches: []         # 目标支路（空表示全部）
```

### protection_coordination（保护配合）

```yaml
skill: protection_coordination

analysis:
  voltage_level: "110kV"      # 电压等级
```

### report_generator（报告生成）

```yaml
skill: report_generator

report:
  title: "仿真分析报告"
  sources:                    # 数据源
    - path: "results/power_flow.json"
      type: "power_flow"
    - path: "results/n1_security.json"
      type: "n1_security"
  format: "docx"              # docx, pdf, markdown
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
  rid: "${MODEL_RID:-model/chenying/IEEE39}"  # 支持默认值
```

## 默认模型

- **IEEE39**：`model/chenying/IEEE39` - 39节点系统，适合潮流和N-1
- **IEEE3**：`model/chenying/IEEE3` - 3节点系统，适合EMT暂态
- **IEEE9**：`model/chenying/IEEE9` - 9节点系统
- **IEEE14**：`model/chenying/IEEE14` - 14节点系统
- **IEEE118**：`model/chenying/IEEE118` - 118节点系统
