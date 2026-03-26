#!/usr/bin/env python3
"""
友好的配置验证器

提供人性化的配置验证和错误提示。
解决 Issue #007: 配置验证错误信息不够友好
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class FriendlyValidator:
    """友好的配置验证器"""

    # 常见错误模式
    ERROR_PATTERNS = {
        "token_missing": {
            "pattern": r"token.*not.*found|token.*missing|认证失败|authentication",
            "title": "❌ Token 认证失败",
            "cause": "缺少有效的 CloudPSS API Token",
            "solution": """
解决步骤：
1. 访问 https://www.cloudpss.net
2. 登录 → 个人中心 → API Token
3. 点击"生成新Token"
4. 在项目根目录创建 token 文件：
   echo "your_token_here" > .cloudpss_token
5. 重新运行命令
"""
        },
        "model_not_found": {
            "pattern": r"model.*not.*found|模型.*不存在|model.*error",
            "title": "❌ 模型未找到",
            "cause": "指定的模型RID不存在或无法访问",
            "solution": """
解决步骤：
1. 检查模型RID格式是否正确（格式：model/owner/name）
2. 确认您有权限访问该模型
3. 使用以下已验证的默认模型：
   - IEEE39: model/holdme/IEEE39 （适合潮流和N-1）
   - IEEE3: model/holdme/IEEE3 （适合EMT暂态）
4. 在CloudPSS网站上确认模型存在
"""
        },
        "component_not_found": {
            "pattern": r"component.*not.*found|元件.*不存在|component.*error",
            "title": "❌ 元件未找到",
            "cause": "指定的元件ID在模型中不存在",
            "solution": """
解决步骤：
1. 使用 component_mapper.py 查询可用元件：
   python cloudpss-sim-v2/scripts/component_mapper.py --model model/holdme/IEEE3 --type 负载

2. 使用通配符模式匹配多个元件：
   component: "Load_*"  # 匹配所有负载

3. 常见元件命名模式：
   - 负载: Load_1, Load_2, Load_Bus1
   - 发电机: Gen_1, Generator_1, G1
   - 变压器: T_1, Transformer_1
   - 线路: Line_1, Line_Bus1_Bus2
"""
        },
        "schema_validation": {
            "pattern": r"schema.*validation|validation.*failed|配置.*错误",
            "title": "❌ 配置格式错误",
            "cause": "YAML配置不符合技能的模式要求",
            "solution": """
常见错误和修复方法：

错误1: 数值类型错误
  错误: tolerance: "1e-6"  (字符串)
  正确: tolerance: 1e-6   (数字，不加引号)

错误2: 缺少必需字段
  检查是否包含：
  - skill: 技能名称
  - model.rid: 模型RID
  - auth.token_file: Token文件路径

错误3: 字段名称错误
  常见错误拼写：
  - simlation → simulation
  - algoritm → algorithm
  - tolerence → tolerance

参考模板：
  cloudpss_skills/templates/<skill_name>.yaml
"""
        },
        "timeout": {
            "pattern": r"timeout|timed out|超时",
            "title": "⏱️ 仿真超时",
            "cause": "仿真运行时间超过了设定的最大等待时间",
            "solution": """
解决步骤：
1. 在配置中增加 timeout 值：
   simulation:
     timeout: 600  # 增加到600秒

2. 检查模型复杂度：
   - 大型模型可能需要更长时间
   - EMT仿真通常比潮流计算慢

3. 检查CloudPSS服务器状态：
   - 访问 https://www.cloudpss.net 查看服务状态
   - 高峰期可能需要更长时间
"""
        },
        "convergence": {
            "pattern": r"convergence|not converge|不收敛",
            "title": "❌ 潮流不收敛",
            "cause": "潮流计算无法在给定条件下收敛到稳态解",
            "solution": """
解决步骤：
1. 调整收敛参数：
   algorithm:
     tolerance: 1e-4  # 放宽收敛精度（默认1e-6）
     max_iterations: 200  # 增加最大迭代次数

2. 检查模型参数：
   - 检查是否有不合理的阻抗值
   - 检查发电机出力和负载是否平衡
   - 检查变压器分接头设置

3. 尝试不同算法：
   algorithm:
     type: fast_decoupled  # 尝试快速分解法
"""
        },
        "job_not_found": {
            "pattern": r"job.*not.*found|任务.*不存在|job_id",
            "title": "❌ 仿真任务不存在",
            "cause": "指定的Job ID无效或已过期",
            "solution": """
解决步骤：
1. 先运行仿真获取有效的Job ID：
   python -m cloudpss_skills run --config power_flow.yaml

2. 从输出中复制Job ID

3. 在后处理技能中使用：
   source:
     job_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

注意：Job ID 有有效期，过期后需要重新运行仿真
"""
        },
        "network_error": {
            "pattern": r"network|connection|connect|网络|连接",
            "title": "❌ 网络连接错误",
            "cause": "无法连接到 CloudPSS 服务器",
            "solution": """
解决步骤：
1. 检查网络连接：
   ping cloudpss.net

2. 检查防火墙设置：
   - 确保可以访问 https://www.cloudpss.net
   - 确保 WebSocket 连接未被阻止（端口443）

3. 检查代理设置：
   - 如果需要代理，设置环境变量：
     export HTTPS_PROXY=http://proxy.example.com:8080

4. 稍后重试：
   - CloudPSS 服务器可能暂时不可用
"""
        }
    }

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = None
        if config_path:
            self.load_config(config_path)

    def load_config(self, path: str):
        """加载配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"❌ 无法加载配置文件: {e}")
            return False

    def analyze_error(self, error_message: str) -> Optional[Dict]:
        """分析错误消息并返回友好的解释"""
        error_lower = error_message.lower()

        for error_type, info in self.ERROR_PATTERNS.items():
            if re.search(info["pattern"], error_lower, re.IGNORECASE):
                return info

        return None

    def print_friendly_error(self, error_message: str):
        """打印友好的错误信息"""
        info = self.analyze_error(error_message)

        if info:
            print(f"\n{info['title']}")
            print("=" * 70)
            print(f"\n📋 错误原因：\n{info['cause']}")
            print(f"\n💡 解决方案：\n{info['solution']}")
            print("=" * 70)
        else:
            # 未知错误，打印原始信息
            print(f"\n❌ 发生错误：\n{error_message}")
            print("\n💡 常见错误解决方案请查看：")
            print("   cloudpss-sim-v2/references/troubleshooting.md")

    def validate_config_structure(self) -> Tuple[bool, List[str]]:
        """验证配置结构"""
        if not self.config:
            return False, ["配置未加载"]

        errors = []

        # 检查必需字段
        if "skill" not in self.config:
            errors.append("缺少必需字段 'skill'，请指定技能名称")

        if "model" not in self.config and "models" not in self.config:
            errors.append("缺少 'model' 或 'models' 字段，请指定模型")

        # 技能特定验证
        skill = self.config.get("skill", "")

        if skill == "param_scan":
            scan = self.config.get("scan", {})
            if not scan.get("component"):
                errors.append("param_scan 需要指定 scan.component（元件ID）")
            if not scan.get("parameter"):
                errors.append("param_scan 需要指定 scan.parameter（参数名）")
            if not scan.get("values"):
                errors.append("param_scan 需要指定 scan.values（参数值列表）")

        elif skill == "waveform_export":
            source = self.config.get("source", {})
            if not source.get("job_id"):
                errors.append("waveform_export 需要指定 source.job_id（仿真任务ID）")

        elif skill == "result_compare":
            sources = self.config.get("sources", {})
            if not sources.get("baseline") or not sources.get("comparison"):
                errors.append("result_compare 需要指定 baseline 和 comparison 结果文件")

        return len(errors) == 0, errors

    def print_validation_report(self):
        """打印验证报告"""
        print("\n🔍 配置验证报告")
        print("=" * 70)

        # 基本信息
        skill = self.config.get("skill", "未知")
        model = self.config.get("model", {}).get("rid", "未指定")

        print(f"\n📄 配置文件: {self.config_path}")
        print(f"🎯 技能类型: {skill}")
        print(f"📊 模型: {model}")

        # 结构验证
        is_valid, errors = self.validate_config_structure()

        if is_valid:
            print(f"\n✅ 配置结构: 通过")
        else:
            print(f"\n❌ 配置结构: 发现 {len(errors)} 个问题")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")

        # 详细检查
        print("\n📋 详细检查:")

        # 检查token文件
        token_file = self.config.get("auth", {}).get("token_file", ".cloudpss_token")
        if Path(token_file).exists():
            print(f"   ✅ Token文件: {token_file} (存在)")
        else:
            print(f"   ❌ Token文件: {token_file} (不存在)")
            print(f"      解决: echo 'your_token' > {token_file}")

        # 检查输出目录
        output_path = self.config.get("output", {}).get("path", "./results/")
        Path(output_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 输出目录: {output_path} (已就绪)")

        # 技能特定提示
        if skill == "power_flow":
            algo = self.config.get("algorithm", {})
            print(f"   ℹ️  算法: {algo.get('type', 'newton_raphson')}")
            print(f"   ℹ️  收敛精度: {algo.get('tolerance', 1e-6)}")

        elif skill == "emt_simulation":
            sim = self.config.get("simulation", {})
            print(f"   ℹ️  仿真时长: {sim.get('duration', 5.0)}s")
            print(f"   ℹ️  积分步长: {sim.get('step_size', 0.0001)}s")

        print("=" * 70)

        return is_valid

    def suggest_fixes(self):
        """建议修复"""
        if not self.config:
            return

        print("\n🔧 自动修复建议:")
        print("-" * 70)

        # 检查并修复常见问题
        fixes = []

        # 1. 确保auth存在
        if "auth" not in self.config:
            self.config["auth"] = {"token_file": ".cloudpss_token"}
            fixes.append("添加了默认的 auth.token_file")

        # 2. 确保output存在
        if "output" not in self.config:
            self.config["output"] = {
                "format": "json",
                "path": "./results/",
                "timestamp": True
            }
            fixes.append("添加了默认的 output 配置")

        # 3. 检查模型source
        if "model" in self.config and "source" not in self.config["model"]:
            self.config["model"]["source"] = "cloud"
            fixes.append("添加了 model.source = cloud")

        if fixes:
            for fix in fixes:
                print(f"   ✓ {fix}")

            # 保存修复后的配置
            backup_path = f"{self.config_path}.backup"
            Path(self.config_path).rename(backup_path)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)

            print(f"\n✅ 已修复并保存到: {self.config_path}")
            print(f"   原配置备份为: {backup_path}")
        else:
            print("   未发现需要修复的问题")

        print("-" * 70)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='友好的配置验证器')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--error', '-e', help='分析错误消息')
    parser.add_argument('--fix', '-f', action='store_true', help='自动修复配置')

    args = parser.parse_args()

    validator = FriendlyValidator()

    if args.error:
        # 分析错误消息
        validator.print_friendly_error(args.error)

    elif args.config:
        # 加载并验证配置
        if not validator.load_config(args.config):
            sys.exit(1)

        is_valid = validator.print_validation_report()

        if args.fix:
            validator.suggest_fixes()

        sys.exit(0 if is_valid else 1)

    else:
        print("用法:")
        print("  验证配置: python validator.py -c config.yaml")
        print("  分析错误: python validator.py -e 'model not found'")
        print("  自动修复: python validator.py -c config.yaml --fix")


if __name__ == "__main__":
    main()
