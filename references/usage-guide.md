# CloudPSS 技能 v2 使用指南

## 安装要求

### 1. 克隆项目

```bash
git clone https://git.tsinghua.edu.cn/chen_ying/cloudpss-api-new.git
cd cloudpss-api-new
```

### 2. 安装依赖

```bash
pip install cloudpss matplotlib pandas pyyaml
```

### 3. 配置Token

1. 访问 https://www.cloudpss.net
2. 登录 → 个人中心 → API Token → 生成新Token
3. 保存Token：
   ```bash
   echo "your_token_here" > .cloudpss_token
   ```

## 快速开始

### 查看可用技能

```bash
python -m cloudpss_skills list
```

### 运行技能

**潮流计算**：
```bash
python -m cloudpss_skills run --config cloudpss_skills/templates/power_flow.yaml
```

**EMT仿真**：
```bash
python -m cloudpss_skills run --config cloudpss_skills/templates/emt_simulation.yaml
```

### 生成自定义配置

```bash
python cloudpss-sim-v2/scripts/generate_config.py power_flow model/holdme/IEEE39 configs/
```

## 在Claude Code中使用

当Claude Code加载了 `cloudpss-sim-v2` 技能后，可以直接用自然语言：

- "帮我跑个IEEE39的潮流计算"
- "对IEEE3做EMT仿真，时长5秒"
- "做N-1安全校核"

Claude会自动：
1. 检测当前目录是否有cloudpss_skills
2. 检查 .cloudpss_token 是否存在
3. 根据请求生成YAML配置
4. 执行仿真
5. 返回结果摘要

## 故障排除

### 问题1：找不到cloudpss_skills模块

**解决**：确保在项目根目录运行：
```bash
cd /path/to/cloudpss-api-new
python -m cloudpss_skills list
```

### 问题2：Token无效

**解决**：
1. 检查Token是否过期（在CloudPSS网站重新生成）
2. 确认Token文件路径正确
3. 检查Token文件是否包含多余空格

### 问题3：模型不存在

**解决**：
- 确认使用正确的默认模型：`model/holdme/IEEE39` 或 `model/holdme/IEEE3`
- 或使用自己拥有的模型RID

### 问题4：仿真超时

**解决**：
- 对于复杂模型，在配置中增加timeout参数
- EMT仿真可能需要300-600秒

## 高级用法

### 自定义模型参数

编辑生成的YAML文件，修改model部分：

```yaml
model:
  rid: ./my_model.yaml  # 本地模型
  source: local
```

### 批量运行多个配置

```bash
for config in configs/*.yaml; do
    python -m cloudpss_skills run --config "$config"
done
```

### 结果后处理

```python
import json

# 读取潮流结果
with open('results/power_flow_xxx.json', 'r') as f:
    data = json.load(f)
    print(f"收敛状态: {data.get('converged', 'N/A')}")
```
