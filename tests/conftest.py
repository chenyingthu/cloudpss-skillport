"""
Shared fixtures for cloudpss-sim-skill integration tests.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

# Set internal API URL if not already configured
if "CLOUDPSS_API_URL" not in os.environ:
    os.environ["CLOUDPSS_API_URL"] = "http://166.111.60.76:50001"

# Load token from internal file (located in cloudpss-toolkit directory)
project_root = Path(__file__).resolve().parent.parent
toolkit_dir = project_root.parent / "cloudpss-toolkit"
for token_file in [
    toolkit_dir / ".cloudpss_token_internal",
    toolkit_dir / ".cloudpss_token",
    project_root / ".cloudpss_token",
]:
    if token_file.exists():
        token = token_file.read_text().strip()
        if token:
            os.environ["CLOUDPSS_TOKEN"] = token
            break

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that call the live CloudPSS API",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(
        reason="need --run-integration to run live CloudPSS integration tests"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def config_generator():
    """Fresh SmartConfigGenerator instance."""
    from smart_config import SmartConfigGenerator
    gen = SmartConfigGenerator()
    # Suppress toolkit availability warning during tests
    return gen


@pytest.fixture(scope="session", autouse=True)
def configure_cloudpss():
    """Configure CloudPSS SDK with internal API URL and token."""
    from cloudpss import setToken
    token = os.environ.get("CLOUDPSS_TOKEN", "").strip()
    if token:
        setToken(token)


@pytest.fixture(scope="session")
def auth_token():
    """Return the configured CloudPSS token."""
    token = os.environ.get("CLOUDPSS_TOKEN", "").strip()
    if not token:
        pytest.skip("missing CloudPSS token for integration tests")
    return token


@pytest.fixture
def mock_skill_result():
    """Factory for creating mock SkillResult objects."""
    def _make_result(skill_name="test_skill", success=True, data=None, error=None):
        from cloudpss_skills.core.base import SkillResult, SkillStatus
        return SkillResult(
            skill_name=skill_name,
            status=SkillStatus.SUCCESS if success else SkillStatus.FAILED,
            start_time=datetime.now(),
            data=data or {"mocked": True},
            error=error,
        )
    return _make_result


@pytest.fixture
def toolkit_skills():
    """Build a map of skill_name -> skill instance from toolkit."""
    try:
        from importlib import reload
        import cloudpss_skills.builtin
        reload(cloudpss_skills.builtin)

        skill_map = {}
        for name in dir(cloudpss_skills.builtin):
            cls = getattr(cloudpss_skills.builtin, name)
            if isinstance(cls, type) and hasattr(cls, 'name') and hasattr(cls, 'run'):
                try:
                    instance = cls()
                    skill_map[instance.name] = instance
                except Exception:
                    pass
        return skill_map
    except ImportError:
        return {}
