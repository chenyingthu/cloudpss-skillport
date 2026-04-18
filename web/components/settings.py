"""
Settings: Multi-profile CloudPSS server, token, and owner configuration.

Saves configuration to:
- Token → writes to project root .cloudpss_token file (when a profile is activated)
- Server URL → updates CLOUDPSS_API_URL env var
- Config file → web/data/settings.json for persistence

Data model (settings.json):
{
    "profiles": [{"id", "name", "server_preset", "server_url", "token", "user_name", "is_default", "created_at"}],
    "active_profile_id": "prof_xxxxxxxx"
}
"""
import os
import json
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "data" / "settings.json"
TOKEN_FILE = PROJECT_ROOT.parent / ".cloudpss_token"

SERVER_URL_MAP = {
    "public": "https://cloudpss.net/",
    "internal": "http://166.111.60.76:50001",
}

# ─── Data Layer ─────────────────────────────────────────────────────────

def generate_profile_id() -> str:
    """Generate an 8-char random profile ID."""
    return "prof_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def _default_settings() -> dict:
    """Return default settings structure."""
    return {
        "profiles": [],
        "active_profile_id": None,
    }


def migrate_settings() -> dict:
    """Migrate legacy flat settings.json to multi-profile format. Idempotent."""
    raw = _read_raw()
    if raw is None:
        return _default_settings()

    # Already migrated
    if "profiles" in raw:
        # Ensure active_profile_id exists
        if "active_profile_id" not in raw:
            profiles = raw.get("profiles", [])
            raw["active_profile_id"] = profiles[0]["id"] if profiles else None
        return raw

    # Legacy format: flat {server_preset, token, user_name, ...}
    try:
        profile = {
            "id": generate_profile_id(),
            "name": "默认配置",
            "server_preset": raw.get("server_preset", "internal"),
            "server_url": raw.get("server_url", ""),
            "token": raw.get("token", ""),
            "user_name": raw.get("user_name", ""),
            "is_default": True,
            "created_at": datetime.now().isoformat(),
        }
        migrated = {
            "profiles": [profile],
            "active_profile_id": profile["id"],
        }
        _write_raw(migrated)
        return migrated
    except Exception:
        return _default_settings()


def _read_raw() -> Optional[dict]:
    """Read raw settings JSON. Returns None if file doesn't exist or is corrupt."""
    if not SETTINGS_FILE.exists():
        return None
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_raw(settings: dict) -> None:
    """Write settings to file atomically."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings() -> dict:
    """Load settings, migrating if needed."""
    return migrate_settings()


def save_settings(settings: dict) -> None:
    """Save settings to file."""
    _write_raw(settings)


def get_active_profile(settings: dict) -> Optional[dict]:
    """Return the currently active profile dict, or None."""
    active_id = settings.get("active_profile_id")
    if not active_id:
        return None
    return get_profile_by_id(settings, active_id)


def get_profile_by_id(settings: dict, profile_id: str) -> Optional[dict]:
    """Look up a profile by ID."""
    for p in settings.get("profiles", []):
        if p["id"] == profile_id:
            return p
    return None


def get_default_profile_id(settings: dict) -> Optional[str]:
    """Return the ID of the default profile, or the first profile if none marked."""
    for p in settings.get("profiles", []):
        if p.get("is_default"):
            return p["id"]
    profiles = settings.get("profiles", [])
    return profiles[0]["id"] if profiles else None


def save_profile(settings: dict, profile_data: dict) -> dict:
    """Create or update a profile. Returns updated settings."""
    profiles = settings.setdefault("profiles", [])
    profile_id = profile_data.get("id")
    if profile_id:
        # Update existing
        for i, p in enumerate(profiles):
            if p["id"] == profile_id:
                profiles[i] = {**profiles[i], **profile_data}
                break
    else:
        # Create new
        new_id = generate_profile_id()
        new_profile = {
            "id": new_id,
            "name": profile_data.get("name", "新方案"),
            "server_preset": profile_data.get("server_preset", "public"),
            "server_url": profile_data.get("server_url", ""),
            "token": profile_data.get("token", ""),
            "user_name": profile_data.get("user_name", ""),
            "is_default": False,
            "created_at": datetime.now().isoformat(),
        }
        profiles.append(new_profile)
        if not settings.get("active_profile_id"):
            settings["active_profile_id"] = new_id
    return settings


def delete_profile(settings: dict, profile_id: str) -> dict:
    """Delete a profile. Returns updated settings. At least one profile must remain."""
    profiles = settings.get("profiles", [])
    if len(profiles) <= 1:
        return settings  # Keep at least one profile

    settings["profiles"] = [p for p in profiles if p["id"] != profile_id]

    # If active was deleted, set active to first remaining
    if settings.get("active_profile_id") == profile_id:
        remaining = settings["profiles"]
        settings["active_profile_id"] = remaining[0]["id"] if remaining else None

    # If default was deleted, set default to first remaining
    for p in settings["profiles"]:
        if p.get("is_default"):
            break
    else:
        for p in settings["profiles"]:
            p["is_default"] = False
        if settings["profiles"]:
            settings["profiles"][0]["is_default"] = True

    return settings


def set_active_profile(settings: dict, profile_id: str) -> dict:
    """Set the active profile. Returns updated settings."""
    settings["active_profile_id"] = profile_id
    return settings


def set_default_profile(settings: dict, profile_id: str) -> dict:
    """Set the default profile (for new task creation). Returns updated settings."""
    for p in settings.get("profiles", []):
        p["is_default"] = (p["id"] == profile_id)
    return settings


def apply_profile(profile: dict) -> None:
    """Apply a profile's settings: write token file and set env vars."""
    if not profile:
        return

    # Save token
    token = profile.get("token", "").strip()
    if token:
        TOKEN_FILE.write_text(token, encoding="utf-8")
        os.environ["CLOUDPSS_TOKEN"] = token
    elif TOKEN_FILE.exists():
        # Token cleared: remove file and env var
        TOKEN_FILE.unlink(missing_ok=True)
        os.environ.pop("CLOUDPSS_TOKEN", None)

    # Set API URL
    preset = profile.get("server_preset", "internal")
    server_url = profile.get("server_url", "").strip()

    if preset == "custom" and server_url:
        os.environ["CLOUDPSS_API_URL"] = server_url
    elif preset in SERVER_URL_MAP:
        os.environ["CLOUDPSS_API_URL"] = SERVER_URL_MAP[preset]


# ─── UI ────────────────────────────────────────────────────────────────

def _server_label(preset: str) -> str:
    """Return a human-readable server label."""
    labels = {
        "internal": "🏠 内部服务器",
        "public": "🌐 公共服务器",
        "custom": "🔧 自定义",
    }
    return labels.get(preset, preset)


def _test_connection(profile: dict) -> None:
    """Test the CloudPSS API connection for a given profile."""
    with st.spinner("正在测试连接..."):
        try:
            from cloudpss import Model
            models = Model.fetchMany(
                pageSize=1,
                baseUrl=SERVER_URL_MAP.get(profile.get("server_preset", "internal"),
                                           profile.get("server_url", "")),
            )
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


def _render_profile_list(settings: dict) -> Optional[str]:
    """Render the profile list sidebar. Returns the selected profile ID or None."""
    profiles = settings.get("profiles", [])
    active_id = settings.get("active_profile_id")
    default_id = get_default_profile_id(settings)

    st.markdown("**📂 配置方案**")

    for p in profiles:
        is_active = p["id"] == active_id
        is_default = p["id"] == default_id
        preset = p.get("server_preset", "public")

        # Build label with badges
        badges = []
        if is_active:
            badges.append("🟢")
        if is_default:
            badges.append("⭐")

        label = p.get("name", "未命名")
        if badges:
            label = " ".join(badges) + " " + label

        server_hint = _server_label(preset)
        if preset == "custom":
            server_hint = "🔧 " + (p.get("server_url", "") or "未设置")

        col1, col2 = st.columns([4, 1])
        with col1:
            selected = st.button(
                label,
                key=f"select_{p['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            )
            st.caption(server_hint)
        with col2:
            if st.button("🗑️", key=f"del_{p['id']}", help="删除此方案"):
                if len(profiles) > 1:
                    settings = delete_profile(settings, p["id"])
                    save_settings(settings)
                    st.rerun()
                else:
                    st.warning("至少保留一个方案")

        if selected:
            return p["id"]

    # Add new profile button
    if st.button("➕ 新增方案", use_container_width=True, type="secondary"):
        settings = save_profile(settings, {
            "name": "新方案",
            "server_preset": "public",
            "server_url": "",
            "token": "",
            "user_name": "",
        })
        new_id = settings["profiles"][-1]["id"]
        settings["active_profile_id"] = new_id
        save_settings(settings)
        st.rerun()

    return None


def _render_profile_editor(settings: dict, profile_id: str) -> dict:
    """Render the profile edit form. Returns updated settings."""
    profile = get_profile_by_id(settings, profile_id)
    if not profile:
        return settings

    st.markdown("---")
    st.subheader("✏️ 编辑方案")

    with st.form(f"edit_{profile_id}"):
        # Name
        name = st.text_input("方案名称", value=profile.get("name", ""), key=f"prof_name_{profile_id}")

        # Server preset
        preset_options = ["internal", "public", "custom"]
        current_preset = profile.get("server_preset", "public")
        # 安全获取索引，如果预设不在选项中则默认使用 public (index 1)
        try:
            preset_index = preset_options.index(current_preset)
        except ValueError:
            preset_index = 1  # 默认 public
        preset = st.selectbox(
            "服务器预设",
            options=preset_options,
            format_func=lambda x: {
                "internal": "内部服务器 (http://166.111.60.76:50001)",
                "public": "公共服务器 (https://cloudpss.net/)",
                "custom": "自定义地址",
            }.get(x, x),
            index=preset_index,
            key=f"prof_preset_{profile_id}",
        )

        # Custom URL
        custom_url = ""
        if preset == "custom":
            custom_url = st.text_input(
                "自定义服务器 URL",
                value=profile.get("server_url", ""),
                placeholder="http://your-server:port",
                key=f"prof_url_{profile_id}",
            )

        # Token
        token = st.text_input(
            "CloudPSS Token",
            value=profile.get("token", ""),
            type="password",
            help="从 CloudPSS 个人中心 → API Token 获取",
            key=f"prof_token_{profile_id}",
        )

        if not token:
            st.warning("⚠️ 未配置 Token")
        else:
            st.success("✅ Token 已配置")

        # User name (owner)
        user_name = st.text_input(
            "用户名 (Owner)",
            value=profile.get("user_name", ""),
            placeholder="用于 model/holdme/ 替换",
            key=f"prof_user_{profile_id}",
        )

        # Actions
        col1, col2, col3, col4 = st.columns(4)
        submitted = col1.form_submit_button("💾 保存", type="primary")
        activate = col2.form_submit_button(" 激活")
        set_default = col3.form_submit_button("⭐ 设为默认")
        test_conn = col4.form_submit_button("🔗 测试")

        if submitted:
            profile["name"] = name
            profile["server_preset"] = preset
            profile["server_url"] = custom_url
            profile["token"] = token
            profile["user_name"] = user_name
            settings = save_profile(settings, profile)
            save_settings(settings)
            st.success("✅ 方案已保存")
            st.rerun()

        if activate:
            # Save first, then activate
            profile["name"] = name
            profile["server_preset"] = preset
            profile["server_url"] = custom_url
            profile["token"] = token
            profile["user_name"] = user_name
            settings = save_profile(settings, profile)
            settings = set_active_profile(settings, profile_id)
            save_settings(settings)
            apply_profile(profile)
            st.success(f"✅ 已激活: {name}")
            st.rerun()

        if set_default:
            profile["name"] = name
            profile["server_preset"] = preset
            profile["server_url"] = custom_url
            profile["token"] = token
            profile["user_name"] = user_name
            settings = save_profile(settings, profile)
            settings = set_default_profile(settings, profile_id)
            save_settings(settings)
            st.success(f"✅ 已设为默认: {name}")
            st.rerun()

        if test_conn:
            _test_connection(profile)

    return settings


def render():
    """Render the settings page with multi-profile management."""
    st.title("⚙️ 系统设置")

    settings = load_settings()

    # Ensure at least one profile exists
    if not settings.get("profiles"):
        default_id = generate_profile_id()
        settings = save_profile(settings, {
            "id": default_id,
            "name": "默认配置",
            "server_preset": "internal",
        })
        settings["active_profile_id"] = default_id
        save_settings(settings)
        st.rerun()

    # Two-column layout
    col_list, col_editor = st.columns([1, 2])

    with col_list:
        selected_id = _render_profile_list(settings)

    with col_editor:
        # Determine which profile to edit: selected, then active, then default
        active_id = settings.get("active_profile_id")
        default_id = get_default_profile_id(settings)

        if selected_id and get_profile_by_id(settings, selected_id):
            edit_id = selected_id
        elif active_id and get_profile_by_id(settings, active_id):
            edit_id = active_id
        elif default_id:
            edit_id = default_id
        else:
            edit_id = settings["profiles"][0]["id"] if settings["profiles"] else None

        if edit_id:
            settings = _render_profile_editor(settings, edit_id)

    # ─── Current Status ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 当前激活方案状态")

    active_profile = get_active_profile(settings)
    if active_profile:
        col1, col2, col3 = st.columns(3)
        preset = active_profile.get("server_preset", "internal")
        server_url = SERVER_URL_MAP.get(preset, active_profile.get("server_url", "未设置"))
        col1.metric("服务器", server_url)
        col2.metric("Token", "✅" if active_profile.get("token") else "❌ 未配置")
        col3.metric("用户", active_profile.get("user_name", "未设置") or "未设置")
    else:
        st.warning("未激活任何方案")
