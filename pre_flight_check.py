#!/usr/bin/env python3
"""
测试环境预检脚本
在运行技能测试前，先验证环境和配置的合理性
"""
import sys
import socket
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.core import skill_catalog


def check_network(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    """检查网络连通性"""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, f"✅ {host}:{port} 可达"
    except socket.timeout:
        return False, f"❌ {host}:{port} 连接超时"
    except ConnectionRefused:
        return False, f"❌ {host}:{port} 连接被拒绝"
    except Exception as e:
        return False, f"❌ {host}:{port} 错误: {e}"


def check_server_http(url: str, timeout: int = 10) -> tuple[bool, str]:
    """检查HTTP服务是否正常"""
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        if response.status_code < 500:
            return True, f"✅ HTTP服务正常 (HTTP {response.status_code})"
        else:
            return False, f"⚠️ HTTP服务返回错误: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "❌ HTTP请求超时"
    except Exception as e:
        return False, f"❌ HTTP请求失败: {e}"


def check_token_file(token_path: Path) -> tuple[bool, str]:
    """检查token文件"""
    if not token_path.exists():
        return False, f"❌ Token文件不存在: {token_path}"

    try:
        token = token_path.read_text().strip()
        if not token:
            return False, "❌ Token文件为空"
        if len(token) < 50:  # JWT通常较长
            return False, f"⚠️ Token可能无效 (长度: {len(token)})"
        return True, f"✅ Token文件存在 (长度: {len(token)})"
    except Exception as e:
        return False, f"❌ Token读取失败: {e}"


def check_skill_config(skill_name: str, user: str) -> tuple[bool, str, dict]:
    """预检查技能配置是否合理"""
    from web.components.task_create import _enhance_config_for_skill

    skill = skill_catalog.get_skill(skill_name)
    if not skill:
        return False, "❌ 技能不存在", {}

    # 获取增强后的配置
    default_config = skill.get_default_config()
    config = _enhance_config_for_skill(default_config, skill_name, user)

    # 检查必需字段
    checks = []

    # 1. 检查skill字段
    if "skill" not in config:
        checks.append("❌ 缺少'skill'字段")
    else:
        checks.append(f"✅ skill={config['skill']}")

    # 2. 检查model字段
    model = config.get("model", {})
    if not model.get("rid"):
        checks.append("⚠️ 未配置model.rid")
    else:
        checks.append(f"✅ model.rid={model['rid']}")

    # 3. 检查auth字段
    auth = config.get("auth", {})
    if not auth.get("token_file"):
        checks.append("❌ 未配置auth.token_file")
    else:
        checks.append(f"✅ auth.token_file已配置")

    # 4. 检查output字段
    output = config.get("output", {})
    if not output.get("path"):
        checks.append("⚠️ 未配置output.path")
    else:
        checks.append(f"✅ output.path={output['path']}")

    # 5. 验证配置（调用技能validate）
    try:
        validation = skill.validate(config)
        if getattr(validation, "valid", False):
            checks.append("✅ Schema验证通过")
        else:
            errors = getattr(validation, "errors", [])
            checks.append(f"❌ Schema验证失败: {errors}")
    except Exception as e:
        checks.append(f"❌ Schema验证异常: {e}")

    all_passed = not any(c.startswith("❌") for c in checks)
    return all_passed, "\n     ".join(checks), config


def main():
    """运行所有预检"""
    print("=" * 70)
    print("🔍 测试环境预检")
    print("=" * 70)

    results = []

    # 1. 网络连通性检查
    print("\n📡 1. 网络连通性检查")
    ok1, msg1 = check_network("166.111.60.76", 50001)
    print(f"   {msg1}")
    results.append(("网络166.111.60.76:50001", ok1))

    # 2. HTTP服务检查
    print("\n🌐 2. HTTP服务检查")
    ok2, msg2 = check_server_http("http://166.111.60.76:50001")
    print(f"   {msg2}")
    results.append(("HTTP服务", ok2))

    # 3. Token检查
    print("\n🔑 3. Token检查")
    token_path = Path(".cloudpss_token")
    ok3, msg3 = check_token_file(token_path)
    print(f"   {msg3}")
    results.append(("Token文件", ok3))

    # 4. 技能配置检查
    print("\n⚙️ 4. 技能配置检查（修复的7个技能）")
    skills_to_check = [
        "model_validator",
        "transient_stability_margin",
        "renewable_integration",
        "voltage_stability",
        "power_quality_analysis",
        "transient_stability",
        "n2_security",
    ]

    all_skills_ok = True
    for skill_name in skills_to_check:
        ok, msg, _ = check_skill_config(skill_name, "chenying")
        status = "✅" if ok else "❌"
        print(f"   {status} {skill_name}:")
        print(f"      {msg}")
        results.append((f"技能-{skill_name}", ok))
        if not ok:
            all_skills_ok = False

    # 汇总
    print("\n" + "=" * 70)
    print("📊 预检结果汇总")
    print("=" * 70)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        emoji = "✅" if ok else "❌"
        print(f"   {emoji} {name}")

    print(f"\n总计: {passed}/{total} 项通过")

    if passed < total:
        print("\n⚠️ 警告: 有预检项未通过，建议修复后再进行真实执行测试")
        print("   特别是网络问题会导致所有技能测试失败")

    return passed == total


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()  # 忽略SSL警告

    all_ready = main()
    sys.exit(0 if all_ready else 1)
