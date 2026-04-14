"""
Settings: Configure CloudPSS server, token, and user info.

Saves configuration to:
- Token → writes to project root .cloudpss_token file
- Server URL → updates CLOUDPSS_API_URL env var
- Config file → web/data/settings.json for persistence
"""
import os
import json
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "web" / "data" / "settings.json"
TOKEN_FILE = PROJECT_ROOT / ".cloudpss_token"


def load_settings():
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "server_url": "",
        "server_preset": "internal",
        "token": "",
        "user_name": "",
    }


def save_settings(settings):
    """Save settings to file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply_settings(settings):
    """Apply settings to environment and token file."""
    # Save token
    token = settings.get("token", "").strip()
    if token:
        TOKEN_FILE.write_text(token, encoding="utf-8")
        os.environ["CLOUDPSS_TOKEN"] = token

    # Set API URL
    preset = settings.get("server_preset", "internal")
    server_url = settings.get("server_url", "").strip()

    url_map = {
        "public": "https://cloudpss.net/",
        "internal": "http://166.111.60.76:50001",
    }

    if preset == "custom" and server_url:
        os.environ["CLOUDPSS_API_URL"] = server_url
    elif preset in url_map:
        os.environ["CLOUDPSS_API_URL"] = url_map[preset]


def render():
    st.title("⚙️ 系统设置")

    settings = load_settings()

    with st.form("settings_form"):
        # ─── Server Preset ────────────────────────────────
        st.subheader("🌐 服务器配置")

        preset = st.selectbox(
            "服务器预设",
            options=["internal", "public", "custom"],
            format_func=lambda x: {
                "internal": "内部服务器 (http://166.111.60.76:50001)",
                "public": "公共服务器 (https://cloudpss.net/)",
                "custom": "自定义地址",
            }.get(x, x),
            index=0 if settings.get("server_preset") == "internal" else 1 if settings.get("server_preset") == "public" else 2,
        )

        custom_url = ""
        if preset == "custom":
            custom_url = st.text_input(
                "自定义服务器 URL",
                value=settings.get("server_url", ""),
                placeholder="http://your-server:port",
            )

        # ─── Token ────────────────────────────────────────
        st.subheader("🔑 API Token")

        current_token = ""
        token_file_exists = TOKEN_FILE.exists()
        if token_file_exists:
            current_token = TOKEN_FILE.read_text().strip()

        token = st.text_input(
            "CloudPSS Token",
            value=current_token or settings.get("token", ""),
            type="password",
            help="从 CloudPSS 个人中心 → API Token 获取",
        )

        if not token:
            st.warning(
                "⚠️ 未配置 Token\n\n"
                "获取方式：\n"
                "1. 访问 https://www.cloudpss.net 或内部服务器\n"
                "2. 登录 → 个人中心 → API Token\n"
                "3. 复制 Token 粘贴到上方输入框"
            )
        else:
            st.success("✅ Token 已配置")

        # ─── User Info ────────────────────────────────────
        st.subheader("👤 用户信息")

        user_name = st.text_input(
            "用户名",
            value=settings.get("user_name", ""),
            placeholder="输入你的名字（可选）",
        )

        # ─── Submit ───────────────────────────────────────
        submitted = st.form_submit_button("💾 保存配置", type="primary")

        if submitted:
            settings["server_preset"] = preset
            settings["server_url"] = custom_url
            settings["token"] = token
            settings["user_name"] = user_name

            save_settings(settings)
            apply_settings(settings)

            st.success("✅ 配置已保存并生效")
            st.rerun()

    # ─── Current Status ─────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 当前配置状态")

    col1, col2, col3 = st.columns(3)
    col1.metric("服务器", os.environ.get("CLOUDPSS_API_URL", "未设置"))
    col2.metric("Token", "✅ 已配置" if os.environ.get("CLOUDPSS_TOKEN") else "❌ 未配置")
    col3.metric("用户", settings.get("user_name", "未设置") or "未设置")

    # Test connection button
    if st.button("🔗 测试连接"):
        _test_connection()


def _test_connection():
    """Test the CloudPSS API connection."""
    with st.spinner("正在测试连接..."):
        try:
            from cloudpss import Model
            # Try to list models - lightweight test
            models = Model.fetchMany(pageSize=1)
            st.success("✅ 连接成功！")
            if models:
                st.caption(f"获取到 {len(models)} 个模型")
        except Exception as e:
            st.error(f"❌ 连接失败: {e}")
            st.info(
                "请检查：\n"
                "1. Token 是否正确\n"
                "2. 服务器地址是否可达\n"
                "3. 网络连接是否正常"
            )
