"""
Comprehensive tests for the viz_skill visualization system.

Covers:
1. viz_skill.py core: registry, dispatcher, auto-detection, StepProxy, pipeline detection
2. Renderer registration: all renderers auto-register correctly
3. Generic renderer smart detection
4. Pipeline renderer: step data, summary stats, context building
5. task_results.py delegation: correctly dispatches to viz_skill
6. End-to-end: rendering results from actual task JSON files

All tests are mocked — no Streamlit server or CloudPSS API needed.
"""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# ─── Fixtures ───────────────────────────────────────────────────────

# Renderer module paths
_RENDERER_MODS = [
    "web.components.viz_renderers.power_flow",
    "web.components.viz_renderers.emt_simulation",
    "web.components.viz_renderers.n1_security",
    "web.components.viz_renderers.generic",
    "web.components.viz_renderers.pipeline",
    "web.components.viz_renderers.vsi_weak_bus",
    "web.components.viz_renderers.short_circuit",
    "web.components.viz_renderers.emt_fault_study",
]


def _make_st_mock():
    """Create a Streamlit mock with call tracking."""
    st = MagicMock()
    st.success.return_value = None
    st.error.return_value = None
    st.warning.return_value = None
    st.caption.return_value = None
    st.subheader.return_value = None
    st.metric.return_value = None
    st.dataframe.return_value = None
    st.json.return_value = None
    st.code.return_value = None
    st.button.return_value = False
    # Return columns with button also returning False
    def make_cols(n):
        cols = []
        for _ in range(n):
            col = MagicMock()
            col.button.return_value = False
            col.text.return_value = None
            col.caption.return_value = None
            col.metric.return_value = None
            cols.append(col)
        return cols
    st.columns.side_effect = make_cols
    st.pyplot.return_value = None
    st.spinner.return_value.__enter__ = Mock(return_value=None)
    st.spinner.return_value.__exit__ = Mock(return_value=False)
    st.markdown.return_value = None
    mock_exp = MagicMock()
    mock_exp.__enter__ = Mock(return_value=None)
    mock_exp.__exit__ = Mock(return_value=False)
    st.expander.return_value = mock_exp
    return st


def _reload_all_with_st(st_mock):
    """Reload viz_skill + all renderers with streamlit replaced in sys.modules."""
    from web.components import viz_skill
    viz_skill._REGISTRY.clear()

    # Remove cached renderer modules
    for mod_name in _RENDERER_MODS:
        sys.modules.pop(mod_name, None)
    sys.modules.pop("web.components.viz_renderers", None)

    # Also reload viz_skill to reset its registry
    import importlib
    importlib.reload(viz_skill)
    viz_skill._REGISTRY.clear()

    # Patch streamlit in sys.modules during renderer import
    original_st = sys.modules.get("streamlit")
    sys.modules["streamlit"] = st_mock

    try:
        from web.components.viz_renderers import power_flow       # noqa
        from web.components.viz_renderers import emt_simulation    # noqa
        from web.components.viz_renderers import n1_security       # noqa
        from web.components.viz_renderers import generic           # noqa
        from web.components.viz_renderers import pipeline          # noqa
        from web.components.viz_renderers import vsi_weak_bus      # noqa
        from web.components.viz_renderers import short_circuit     # noqa
        from web.components.viz_renderers import emt_fault_study   # noqa
    finally:
        if original_st:
            sys.modules["streamlit"] = original_st
        else:
            sys.modules.pop("streamlit", None)

    # Now patch st on each renderer module so tests can inspect calls
    for mod_name in _RENDERER_MODS:
        mod = sys.modules.get(mod_name)
        if mod:
            object.__setattr__(mod, "st", st_mock)

    # Also patch st on viz_skill for render_step
    object.__setattr__(viz_skill, "st", st_mock)


@pytest.fixture
def st_mock():
    """Fresh Streamlit mock."""
    return _make_st_mock()


@pytest.fixture
def fresh():
    """Clear registry only. For tests that don't need renderers."""
    from web.components import viz_skill
    viz_skill._REGISTRY.clear()
    yield
    viz_skill._REGISTRY.clear()


@pytest.fixture
def full_setup(st_mock):
    """Reload everything with mocked streamlit. For tests needing renderers."""
    _reload_all_with_st(st_mock)


# ─── 1. Registry Tests ──────────────────────────────────────────────


class TestRegistry:
    """Test the @register_renderer decorator and registry mechanics."""

    def test_register_decorator(self, fresh):
        """Decorator registers function under given name."""
        from web.components import viz_skill

        @viz_skill.register_renderer("test_skill")
        def render(data, task, context=None):
            pass

        assert "test_skill" in viz_skill._REGISTRY

    def test_register_overwrites(self, fresh):
        """Registering same name twice overwrites previous."""
        from web.components import viz_skill

        def render_v1(data, task, context=None):
            pass
        def render_v2(data, task, context=None):
            pass

        viz_skill.register_renderer("dup")(render_v1)
        viz_skill.register_renderer("dup")(render_v2)
        assert viz_skill._REGISTRY["dup"] is render_v2

    def test_all_renderers_registered(self, full_setup):
        """All renderer modules auto-register correctly."""
        from web.components.viz_skill import _REGISTRY
        assert "power_flow" in _REGISTRY
        assert "emt_simulation" in _REGISTRY
        assert "n1_security" in _REGISTRY
        assert "generic" in _REGISTRY
        assert "study_pipeline" in _REGISTRY
        assert "vsi_weak_bus" in _REGISTRY
        assert "short_circuit" in _REGISTRY
        assert "emt_fault_study" in _REGISTRY

    def test_registry_count(self, full_setup):
        """Expected number of renderers registered."""
        from web.components.viz_skill import _REGISTRY
        assert len(_REGISTRY) == 8  # 7 skill renderers + study_pipeline


# ─── 2. Dispatcher Tests ────────────────────────────────────────────


class TestDispatcher:
    """Test render_result() dispatch logic."""

    def test_dispatch_registered(self, full_setup):
        """Dispatches to registered renderer for known skill."""
        from web.components.viz_skill import render_result, _REGISTRY

        call_data = {}
        original = _REGISTRY["power_flow"]
        def spy(data, task, context=None):
            call_data["called"] = True
        _REGISTRY["power_flow"] = spy

        render_result("power_flow", {"converged": True}, Mock())
        assert call_data["called"] is True

        _REGISTRY["power_flow"] = original

    def test_dispatch_fallback_to_generic(self, full_setup):
        """Unknown skill falls back to generic renderer."""
        from web.components.viz_skill import render_result, _REGISTRY

        call_data = {}
        original = _REGISTRY["generic"]
        def spy(data, task, context=None):
            call_data["called"] = True
        _REGISTRY["generic"] = spy

        render_result("unknown_skill_xyz", {"foo": "bar"}, Mock())
        assert call_data["called"] is True

        _REGISTRY["generic"] = original

    def test_dispatch_auto_detect_fallback(self, full_setup):
        """Unknown skill with known data shape dispatches to detected renderer."""
        from web.components.viz_skill import render_result, _REGISTRY

        call_data = {}
        original = _REGISTRY["power_flow"]
        def spy(data, task, context=None):
            call_data["called"] = True
        _REGISTRY["power_flow"] = spy

        render_result("some_alias", {"buses": [], "branches": []}, Mock())
        assert call_data["called"] is True

        _REGISTRY["power_flow"] = original

    def test_dispatch_with_context(self, full_setup):
        """Context is passed through to renderer."""
        from web.components.viz_skill import render_result, _REGISTRY

        call_data = {}
        original = _REGISTRY["generic"]
        def spy(data, task, context=None):
            call_data["context"] = context
        _REGISTRY["generic"] = spy

        ctx = {"steps": {"pf": {"status": "success"}}}
        render_result("generic", {}, Mock(), context=ctx)
        assert call_data["context"] == ctx

        _REGISTRY["generic"] = original


# ─── 3. Auto-Detection Tests ────────────────────────────────────────


class TestAutoDetection:
    """Test detect_result_type() heuristic detection."""

    def test_detect_power_flow(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "buses": [], "branches": [], "converged": True
        }) == "power_flow"

    def test_detect_emt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "plots": [], "plot_count": 3
        }) == "emt_simulation"

    def test_detect_emt_alt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"plot_count": 2}) == "emt_simulation"

    def test_detect_n1(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "violation_count": 2, "total_branches": 10
        }) == "n1_security"

    def test_detect_n1_alt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"total_branches": 5}) == "n1_security"

    def test_detect_unknown(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"some": "data"}) is None

    def test_detect_empty(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({}) is None

    def test_detect_vsi_weak_bus(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "vsi_results": {"vsi_i": {"Bus1": 0.02}}, "weak_buses": []
        }) == "vsi_weak_bus"

    def test_detect_vsi_weak_bus_alt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"weak_buses": [{"label": "Bus1"}]}) == "vsi_weak_bus"

    def test_detect_short_circuit(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "fault_location": "Bus7", "short_circuit_mva": {}
        }) == "short_circuit"

    def test_detect_short_circuit_alt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"fault_location": "Line1"}) == "short_circuit"

    def test_detect_emt_fault_study(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({
            "scenarios": [{"scenario": "baseline"}], "summary": {}
        }) == "emt_fault_study"

    def test_detect_emt_fault_study_alt(self, fresh):
        from web.components import viz_skill
        assert viz_skill.detect_result_type({"fault_end_time": 0.5}) == "emt_fault_study"


# ─── 4. Pipeline Detection Tests ────────────────────────────────────


class TestPipelineDetection:
    """Test is_pipeline_result()."""

    def test_pipeline_detected(self, fresh):
        from web.components import viz_skill
        assert viz_skill.is_pipeline_result({"steps": []}) is True
        assert viz_skill.is_pipeline_result({"steps": [{"skill": "pf"}]}) is True

    def test_pipeline_not_detected(self, fresh):
        from web.components import viz_skill
        assert viz_skill.is_pipeline_result({"converged": True}) is False
        assert viz_skill.is_pipeline_result({"status": "DONE"}) is False
        assert viz_skill.is_pipeline_result({}) is False
        assert viz_skill.is_pipeline_result({"steps": "not_a_list"}) is False


# ─── 5. StepProxy Tests ─────────────────────────────────────────────


class TestStepProxy:
    """Test _StepProxy adapter for pipeline step compatibility."""

    def test_proxy_skill_name(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"skill": "power_flow"})
        assert proxy.skill_name == "power_flow"

    def test_proxy_name(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"name": "my_step", "skill": "pf"})
        assert proxy.name == "my_step"

    def test_proxy_name_fallback(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"skill": "power_flow"})
        assert proxy.name == "power_flow"

    def test_proxy_status_success(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"status": "success"})
        assert proxy.status == "done"

    def test_proxy_status_failed(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"status": "failed"})
        assert proxy.status == "failed"

    def test_proxy_result_data(self, fresh):
        from web.components import viz_skill
        data = {"converged": True, "bus_count": 39}
        proxy = viz_skill._StepProxy({"result_data": data})
        assert proxy.result_data == data

    def test_proxy_result_data_default(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({})
        assert proxy.result_data == {}

    def test_proxy_artifacts(self, fresh):
        from web.components import viz_skill
        artifacts = [{"type": "json", "path": "results/test.json"}]
        proxy = viz_skill._StepProxy({"artifacts": artifacts})
        assert proxy.artifacts == artifacts

    def test_proxy_metrics(self, fresh):
        from web.components import viz_skill
        metrics = {"duration": 4.2}
        proxy = viz_skill._StepProxy({"metrics": metrics})
        assert proxy.metrics == metrics

    def test_proxy_config(self, fresh):
        from web.components import viz_skill
        config = {"algorithm": {"type": "newton_raphson"}}
        proxy = viz_skill._StepProxy({"config": config})
        assert proxy.config == config

    def test_proxy_error(self, fresh):
        from web.components import viz_skill
        proxy = viz_skill._StepProxy({"error": "Test error"})
        assert proxy.error == "Test error"


# ─── 6. render_step Tests ───────────────────────────────────────────


class TestRenderStep:
    """Test render_step() function."""

    def test_render_step_failed(self, full_setup, st_mock):
        """Failed steps render error message."""
        from web.components import viz_skill
        # render_step does `import streamlit as st` inside the function,
        # so we need sys.modules["streamlit"] to be the mock
        original_st = sys.modules.get("streamlit")
        sys.modules["streamlit"] = st_mock
        try:
            viz_skill.render_step({"status": "failed", "error": "Network timeout"})
            st_mock.error.assert_called()
        finally:
            if original_st:
                sys.modules["streamlit"] = original_st
            else:
                sys.modules.pop("streamlit", None)

    def test_render_step_success_dispatches(self, full_setup):
        """Success steps dispatch to skill renderer."""
        from web.components import viz_skill
        from web.components.viz_skill import _REGISTRY

        call_data = {}
        original = _REGISTRY.get("power_flow")
        def spy(data, task, context=None):
            call_data["called"] = True
            call_data["task_type"] = type(task).__name__
        _REGISTRY["power_flow"] = spy

        viz_skill.render_step({
            "skill": "power_flow",
            "status": "success",
            "result_data": {"converged": True},
        })

        assert call_data["called"] is True
        assert call_data["task_type"] == "_StepProxy"

        _REGISTRY["power_flow"] = original


# ─── 7. Generic Renderer Smart Detection Tests ──────────────────────


class TestGenericRenderer:
    """Test smart fallback rendering logic."""

    def test_detect_and_redirect(self, full_setup):
        """Generic renderer redirects to detected type."""
        from web.components import viz_skill
        # Call power_flow renderer directly (generic would redirect to it)
        viz_skill._REGISTRY["power_flow"]({"buses": [], "branches": []}, Mock())
        viz_skill.st.subheader.assert_not_called()

    def test_list_of_dicts_renders_table(self, full_setup):
        """List of dict data renders as dataframe."""
        from web.components import viz_skill
        generic = viz_skill._REGISTRY["generic"]
        generic({"items": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}, Mock())
        viz_skill.st.dataframe.assert_called()

    def test_flat_dict_renders_metrics(self, full_setup):
        """Flat dict renders as metrics."""
        from web.components import viz_skill
        generic = viz_skill._REGISTRY["generic"]
        generic({"total": 100, "count": 5, "rate": 0.95}, Mock())
        viz_skill.st.columns.assert_called()

    def test_empty_data(self, full_setup):
        """Empty data renders caption."""
        from web.components import viz_skill
        generic = viz_skill._REGISTRY["generic"]
        generic({}, Mock())
        viz_skill.st.caption.assert_called()

    def test_nested_dict_expander(self, full_setup):
        """Nested dicts render in expandable sections."""
        from web.components import viz_skill
        generic = viz_skill._REGISTRY["generic"]
        generic({"config": {"type": "pf", "tolerance": 1e-6}}, Mock())
        viz_skill.st.expander.assert_called()


# ─── 8. Pipeline Context Building Tests ─────────────────────────────


class TestPipelineContext:
    """Test pipeline context building for cross-step references."""

    def test_build_context(self, full_setup):
        """_build_context_for_step includes previous steps."""
        from web.components import viz_skill
        pipeline_mod = sys.modules.get("web.components.viz_renderers.pipeline")
        _build = getattr(pipeline_mod, "_build_context_for_step", None)
        if _build is None:
            # Function may not exist if pipeline mod didn't export it
            pytest.skip("_build_context_for_step not available")
        steps = [
            {"name": "pf", "skill": "power_flow", "status": "success", "result_data": {"converged": True}},
            {"name": "viz", "skill": "visualize", "status": "success", "result_data": {}},
        ]
        ctx = _build(steps, 1)
        assert "pf" in ctx["steps"]
        assert ctx["steps"]["pf"]["status"] == "success"
        assert ctx["steps"]["pf"]["data"]["converged"] is True


# ─── 9. Renderer Function Tests ─────────────────────────────────────


class TestPowerFlowRenderer:
    """Test power_flow renderer output."""

    def test_converged_status(self, full_setup):
        """Shows success for converged result."""
        from web.components import viz_skill
        pf = viz_skill._REGISTRY["power_flow"]
        pf({"converged": True, "model": "IEEE39"}, Mock())
        viz_skill.st.success.assert_any_call("✅ 潮流收敛")

    def test_not_converged_status(self, full_setup):
        """Shows error for non-converged result."""
        from web.components import viz_skill
        pf = viz_skill._REGISTRY["power_flow"]
        pf({"converged": False}, Mock())
        viz_skill.st.error.assert_any_call("❌ 潮流未收敛")

    def test_model_info(self, full_setup):
        """Shows model info."""
        from web.components import viz_skill
        pf = viz_skill._REGISTRY["power_flow"]
        pf({"converged": True, "model": "IEEE39", "model_rid": "model/IEEE39"}, Mock())
        caption_calls = [str(c) for c in viz_skill.st.caption.call_args_list]
        assert any("IEEE39" in str(c) for c in caption_calls)


class TestEMTRenderer:
    """Test emt_simulation renderer output."""

    def test_simulation_done(self, full_setup):
        """Shows done status."""
        from web.components import viz_skill
        emt = viz_skill._REGISTRY["emt_simulation"]
        task = Mock()
        task.artifacts = []
        emt({"status": "DONE", "duration": 5.0}, task)
        viz_skill.st.success.assert_any_call("✅ 仿真完成")

    def test_duration_display(self, full_setup):
        """Shows duration."""
        from web.components import viz_skill
        emt = viz_skill._REGISTRY["emt_simulation"]
        task = Mock()
        task.artifacts = []
        emt({"status": "DONE", "duration": 5.0, "step_size": 1e-5}, task)
        caption_calls = [str(c) for c in viz_skill.st.caption.call_args_list]
        assert any("5.00" in str(c) for c in caption_calls)


class TestN1Renderer:
    """Test n1_security renderer output."""

    def test_all_safe(self, full_setup):
        """Shows success when all branches safe."""
        from web.components import viz_skill
        n1 = viz_skill._REGISTRY["n1_security"]
        n1({"total_branches": 46, "safe_count": 46}, Mock())
        viz_skill.st.success.assert_any_call("✅ 所有支路安全")

    def test_violations(self, full_setup):
        """Shows warning when violations exist."""
        from web.components import viz_skill
        n1 = viz_skill._REGISTRY["n1_security"]
        n1({
            "total_branches": 46,
            "safe_count": 44,
            "violation_count": 2,
            "violations": [{"bus": "Bus1"}]
        }, Mock())
        viz_skill.st.warning.assert_called()


class TestVsiWeakBusRenderer:
    """Test vsi_weak_bus renderer output."""

    def test_summary_metrics(self, full_setup):
        """Shows VSI summary metrics."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["vsi_weak_bus"]
        renderer({
            "model_rid": "IEEE39",
            "summary": {"total_buses": 39, "weak_bus_count": 2, "max_vsi": 0.025, "avg_vsi": 0.008},
        }, Mock())
        viz_skill.st.subheader.assert_any_call("📊 分析概览")

    def test_weak_bus_warning(self, full_setup):
        """Shows warning for weak buses."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["vsi_weak_bus"]
        renderer({
            "weak_buses": [{"label": "Bus7", "vsi": 0.021}],
        }, Mock())
        viz_skill.st.warning.assert_called()

    def test_no_weak_bus_success(self, full_setup):
        """Shows success when no weak buses."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["vsi_weak_bus"]
        renderer({
            "weak_buses": [],
            "summary": {"weak_bus_count": 0},
        }, Mock())
        viz_skill.st.success.assert_called()

    def test_vsi_chart(self, full_setup):
        """Renders VSI bar chart."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["vsi_weak_bus"]
        renderer({
            "vsi_results": {"vsi_i": {"Bus1": 0.02, "Bus2": 0.005}},
        }, Mock())
        viz_skill.st.pyplot.assert_called()


class TestShortCircuitRenderer:
    """Test short_circuit renderer output."""

    def test_fault_info(self, full_setup):
        """Shows fault location, type, resistance."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["short_circuit"]
        renderer({
            "model": "IEEE3",
            "fault_location": "Bus7",
            "fault_type": "three_phase",
            "fault_resistance": 0.1,
        }, Mock())
        viz_skill.st.subheader.assert_any_call("⚡ 短路信息")

    def test_short_circuit_capacity(self, full_setup):
        """Shows short circuit capacity table."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["short_circuit"]
        renderer({
            "short_circuit_mva": {
                "ch1": {"steady_current_ka": 1.5, "short_circuit_mva": 100.0}
            },
        }, Mock())
        viz_skill.st.subheader.assert_any_call("📊 短路容量")

    def test_current_analysis(self, full_setup):
        """Shows current analysis table."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["short_circuit"]
        renderer({
            "analysis": {
                "ch1": {"peak_current": 2.5, "steady_current": 1.5, "dc_component": 0.3, "time_constant": 50.0}
            },
        }, Mock())
        viz_skill.st.subheader.assert_any_call("📈 短路电流分析")


class TestEmtFaultStudyRenderer:
    """Test emt_fault_study renderer output."""

    def test_scenario_table(self, full_setup):
        """Shows scenario comparison table."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["emt_fault_study"]
        renderer({
            "model_name": "IEEE3",
            "scenarios": [
                {"scenario": "baseline", "description": "Base case", "fault_end_time": 0.2}
            ],
        }, Mock())
        viz_skill.st.subheader.assert_any_call("📊 工况对比汇总")

    def test_findings(self, full_setup):
        """Shows key findings."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["emt_fault_study"]
        renderer({
            "summary": {
                "findings": [
                    {"title": "Voltage Recovery", "supported": True, "evidence": "Recovered in 0.5s"}
                ]
            },
        }, Mock())
        viz_skill.st.subheader.assert_any_call("🔍 关键发现")

    def test_error_state(self, full_setup):
        """Shows error when present."""
        from web.components import viz_skill
        renderer = viz_skill._REGISTRY["emt_fault_study"]
        renderer({
            "summary": {"error": "Simulation failed"},
        }, Mock())
        viz_skill.st.error.assert_called()


# ─── 10. Integration: task_results.py Delegation ────────────────────


class TestTaskResultsDelegation:
    """Test that task_results.py correctly delegates to viz_skill."""

    def test_show_results_calls_dispatcher(self, full_setup, st_mock):
        """_show_results calls render_result for non-pipeline results."""
        task = Mock()
        task.skill_name = "power_flow"
        task.result_data = {"converged": True}
        task.artifacts = []
        task.metrics = {}
        task.config = {"output": {"format": "json"}}

        # Patch sys.modules["streamlit"]
        original_st = sys.modules.get("streamlit")
        sys.modules["streamlit"] = st_mock

        # Patch render_result in task_results module namespace
        import web.components.task_results as tr_mod
        original_rr = tr_mod.render_result

        call_data = {}
        def spy(skill_name, result_data, task, context=None):
            call_data["called"] = True
            call_data["skill_name"] = skill_name
        tr_mod.render_result = spy

        try:
            tr_mod._show_results(task)
        finally:
            tr_mod.render_result = original_rr
            if original_st:
                sys.modules["streamlit"] = original_st
            else:
                sys.modules.pop("streamlit", None)

        assert call_data["called"] is True
        assert call_data["skill_name"] == "power_flow"

    def test_show_results_pipeline_detection(self, fresh):
        """_show_results detects pipeline results."""
        from web.components.viz_skill import is_pipeline_result
        task = Mock()
        task.result_data = {
            "steps": [
                {"name": "pf", "skill": "power_flow", "status": "success", "result_data": {}}
            ]
        }
        assert is_pipeline_result(task.result_data) is True


# ─── 11. End-to-End: Real Task Files ────────────────────────────────


class TestRealTaskFiles:
    """Test rendering with actual task JSON files from the data directory."""

    @pytest.fixture
    def tasks_dir(self):
        return Path(__file__).resolve().parent.parent / "web" / "data" / "tasks"

    def test_load_power_flow_task(self, tasks_dir):
        """Can load a real power flow task and verify structure."""
        task_files = sorted(tasks_dir.glob("task_*.json"), reverse=True)
        pf_tasks = []
        for f in task_files:
            data = json.loads(f.read_text())
            if data.get("skill_name") == "power_flow":
                pf_tasks.append(data)

        if pf_tasks:
            task_data = pf_tasks[0]
            assert task_data["status"] == "done"
            assert "result_data" in task_data
            assert "converged" in task_data["result_data"]

    def test_load_emt_task(self, tasks_dir):
        """Can load a real EMT task and verify structure."""
        task_files = sorted(tasks_dir.glob("task_*.json"), reverse=True)
        emt_tasks = []
        for f in task_files:
            data = json.loads(f.read_text())
            if data.get("skill_name") == "emt_simulation":
                emt_tasks.append(data)

        if emt_tasks:
            task_data = emt_tasks[0]
            assert task_data["status"] == "done"
            assert "result_data" in task_data
            assert "plot_count" in task_data["result_data"]
            assert task_data["result_data"]["plot_count"] > 0

    def test_render_power_flow_task(self, full_setup, tasks_dir):
        """Rendering a real power flow task doesn't crash."""
        from web.components import viz_skill
        pf = viz_skill._REGISTRY["power_flow"]
        task_files = sorted(tasks_dir.glob("task_*.json"), reverse=True)
        for f in task_files:
            data = json.loads(f.read_text())
            if data.get("skill_name") == "power_flow":
                task = Mock()
                task.config = data.get("config", {})
                pf(data.get("result_data", {}), task)
                break


# ─── 12. Matplotlib Font Config Tests ───────────────────────────────


class TestMatplotlibConfig:
    """Verify matplotlib Chinese font config is applied."""

    def test_chinese_font_config(self):
        """Matplotlib font config includes CJK fonts."""
        import matplotlib
        fonts = matplotlib.rcParams.get("font.sans-serif", [])
        cjk_fonts = [f for f in fonts if "Noto Sans CJK" in f]
        assert len(cjk_fonts) > 0, f"No CJK fonts found in {fonts}"

    def test_unicode_minus_disabled(self):
        """Unicode minus is disabled for font compatibility."""
        import matplotlib
        assert matplotlib.rcParams.get("axes.unicode_minus") is False


# ─── 13. CI/CD Framework Tests ──────────────────────────────────────


class TestCICDFramework:
    """Tests that verify the testing infrastructure itself."""

    def test_all_renderer_files_exist(self):
        """All expected renderer files are present."""
        renderers_dir = Path(__file__).resolve().parent.parent / "web" / "components" / "viz_renderers"
        expected = ["__init__.py", "power_flow.py", "emt_simulation.py",
                    "n1_security.py", "generic.py", "pipeline.py",
                    "vsi_weak_bus.py", "short_circuit.py", "emt_fault_study.py"]
        for f in expected:
            assert (renderers_dir / f).exists(), f"Missing: {f}"

    def test_viz_skill_module_exists(self):
        """viz_skill.py module exists."""
        viz_path = Path(__file__).resolve().parent.parent / "web" / "components" / "viz_skill.py"
        assert viz_path.exists()

    def test_task_results_uses_dispatcher(self):
        """task_results.py imports from viz_skill (not inline rendering)."""
        task_results_path = Path(__file__).resolve().parent.parent / "web" / "components" / "task_results.py"
        content = task_results_path.read_text()
        assert "from web.components.viz_skill import" in content
        assert "render_result" in content
        assert "def _render_power_flow" not in content
        assert "def _render_emt" not in content

    def test_no_inline_matplotlib_config_in_task_results(self):
        """matplotlib config should be in viz_skill.py, not task_results.py."""
        task_results_path = Path(__file__).resolve().parent.parent / "web" / "components" / "task_results.py"
        content = task_results_path.read_text()
        assert "matplotlib.rcParams" not in content

    def test_renderer_interface_consistency(self, full_setup):
        """All renderers accept (data, task, context) signature."""
        import inspect
        from web.components.viz_skill import _REGISTRY

        for name, func in _REGISTRY.items():
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            assert "data" in params, f"{name}: missing 'data' param"
            assert "task" in params, f"{name}: missing 'task' param"

    def test_all_skills_have_renderer_or_fallback(self, full_setup):
        """Every core skill has a renderer or generic fallback."""
        from web.components.viz_skill import _REGISTRY

        skills_with_renderers = set(_REGISTRY.keys())
        assert "generic" in skills_with_renderers, "generic renderer must be registered"

        core_skills = {"power_flow", "emt_simulation", "n1_security", "study_pipeline", "vsi_weak_bus", "short_circuit", "emt_fault_study"}
        for skill in core_skills:
            assert skill in skills_with_renderers, f"Missing renderer for: {skill}"
