"""
Tests for pipeline editor, enhanced renderer, DAG visualization, validation, and integration.
"""
import pytest
import sys
from unittest.mock import MagicMock, patch


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_streamlit():
    """Mock streamlit module for unit testing."""
    mock_st = MagicMock()
    # columns returns enough mock columns for any call
    mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
    mock_st.expander.return_value.__enter__ = lambda s: None
    mock_st.expander.return_value.__exit__ = lambda s, *a: None
    mock_st.slider.return_value = 0
    mock_st.selectbox.side_effect = lambda *a, **kw: a[0][0] if a and a[0] else ""
    mock_st.text_input.side_effect = lambda *a, **kw: kw.get("value", "")
    mock_st.number_input.side_effect = lambda *a, **kw: kw.get("value", 0)
    mock_st.checkbox.side_effect = lambda *a, **kw: kw.get("value", False)
    mock_st.multiselect.side_effect = lambda *a, **kw: kw.get("default", [])
    mock_st.text_area.side_effect = lambda *a, **kw: kw.get("value", "")
    # tabs context manager
    mock_st.tabs.return_value = [MagicMock() for _ in range(5)]
    # progress
    mock_st.progress.return_value = None
    return mock_st


@pytest.fixture
def sample_pipeline_data():
    """Sample pipeline result data."""
    return {
        "steps": [
            {
                "name": "潮流计算",
                "skill": "power_flow",
                "status": "success",
                "duration": 10.5,
                "result_data": {
                    "converged": True,
                    "buses": [
                        {"Bus": "Bus1", "Vm": 1.02, "Va": 0.0, "Pgen": 100, "Qgen": 20, "Pload": 0, "Qload": 0},
                        {"Bus": "Bus2", "Vm": 0.98, "Va": -2.5, "Pgen": 0, "Qgen": 0, "Pload": 80, "Qload": 15},
                    ],
                    "branches": [],
                },
                "depends_on": [],
                "parallel": False,
            },
            {
                "name": "N-1分析",
                "skill": "n1_security",
                "status": "success",
                "duration": 25.3,
                "result_data": {
                    "total_scenarios": 10,
                    "violations": [],
                },
                "depends_on": ["潮流计算"],
                "parallel": False,
            },
            {
                "name": "VSI分析",
                "skill": "vsi_weak_bus",
                "status": "success",
                "duration": 8.2,
                "result_data": {
                    "vsi_results": [
                        {"bus": "Bus1", "vsi": 0.35},
                        {"bus": "Bus2", "vsi": 0.72},
                    ],
                    "weak_buses": [],
                },
                "depends_on": ["潮流计算"],
                "parallel": True,
            },
        ],
    }


# ─── Pipeline Editor Tests ──────────────────────────────────────────────────

class TestPipelineEditor:
    """Test pipeline_editor.py component."""

    def test_get_pipeline_templates(self):
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        assert len(templates) >= 4
        assert "潮流 + N-1 + 可视化" in templates
        assert "EMT故障研究 + 对比分析" in templates
        assert "VSI弱母线 + 无功补偿" in templates
        assert "并行参数扫描" in templates

    def test_template_structure(self):
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        for name, steps in templates.items():
            assert isinstance(steps, list)
            assert len(steps) >= 2
            for step in steps:
                assert "skill" in step
                assert "name" in step
                assert "depends_on" in step
                assert "parallel" in step

    def test_parallel_template(self):
        from web.components.pipeline_editor import _get_pipeline_templates
        parallel_tpl = _get_pipeline_templates()["并行参数扫描"]
        parallel_steps = [s for s in parallel_tpl if s.get("parallel")]
        assert len(parallel_steps) >= 2
        for s in parallel_steps:
            assert not s.get("depends_on") or s.get("depends_on") == []

    def test_validate_dependencies_clean(self):
        from web.components.pipeline_editor import _validate_dependencies
        steps = [
            {"name": "A", "skill": "power_flow", "depends_on": []},
            {"name": "B", "skill": "n1_security", "depends_on": ["A"]},
        ]
        issues = _validate_dependencies(steps)
        assert issues == []

    def test_validate_missing_dependency(self):
        from web.components.pipeline_editor import _validate_dependencies
        steps = [
            {"name": "B", "skill": "n1_security", "depends_on": ["nonexistent"]},
        ]
        issues = _validate_dependencies(steps)
        assert len(issues) >= 1
        assert "nonexistent" in issues[0]

    def test_validate_circular_dependency(self):
        from web.components.pipeline_editor import _validate_dependencies
        steps = [
            {"name": "A", "skill": "pf", "depends_on": ["B"]},
            {"name": "B", "skill": "n1", "depends_on": ["A"]},
        ]
        issues = _validate_dependencies(steps)
        assert any("循环依赖" in issue for issue in issues)

    def test_validate_empty_step_name(self):
        from web.components.pipeline_editor import _validate_dependencies
        steps = [{"name": "", "skill": "", "depends_on": []}]
        issues = _validate_dependencies(steps)
        assert any("未指定" in issue for issue in issues)


# ─── Pipeline Renderer Tests ────────────────────────────────────────────────

class TestPipelineRendererEnhanced:
    """Test enhanced pipeline renderer."""

    def test_summary_renders(self, mock_streamlit, sample_pipeline_data):
        from web.components.viz_renderers import pipeline as pipeline_mod
        with patch.object(pipeline_mod.st, "columns", mock_streamlit.columns), \
             patch.object(pipeline_mod.st, "success", mock_streamlit.success), \
             patch.object(pipeline_mod.st, "warning", mock_streamlit.warning):
            pipeline_mod._render_summary(sample_pipeline_data["steps"], sample_pipeline_data)
        assert mock_streamlit.columns.called

    def test_timeline_identifies_parallel_batch(self, sample_pipeline_data):
        from web.components.viz_renderers.pipeline import _identify_batches
        batches = _identify_batches(sample_pipeline_data["steps"])
        assert len(batches) >= 2
        first_batch_names = [s.get("name") for s in batches[0]]
        assert "潮流计算" in first_batch_names

    def test_timeline_renders(self, mock_streamlit, sample_pipeline_data):
        from web.components.viz_renderers.pipeline import _render_timeline
        _render_timeline(sample_pipeline_data["steps"])

    def test_dag_text_renders(self, mock_streamlit, sample_pipeline_data):
        from web.components.viz_renderers import pipeline as pipeline_mod
        with patch.object(pipeline_mod.st, "caption", mock_streamlit.caption), \
             patch.object(pipeline_mod.st, "text", mock_streamlit.text):
            pipeline_mod._render_dag_text(sample_pipeline_data["steps"])
        assert mock_streamlit.caption.called

    def test_validation_findings(self, sample_pipeline_data):
        from web.components.viz_renderers.pipeline import _validate_pipeline
        findings = _validate_pipeline(sample_pipeline_data["steps"])
        assert isinstance(findings, list)
        assert len(findings) > 0
        for f in findings:
            assert "step" in f
            assert "check" in f
            assert "result" in f
            assert "detail" in f
            assert f["result"] in ("pass", "warning", "fail")


# ─── Pipeline Validation Tests ──────────────────────────────────────────────

class TestPipelineValidation:
    """Test result correctness validation."""

    def test_validate_power_flow_converged(self):
        from web.components.viz_renderers.pipeline import _validate_power_flow
        result = {
            "converged": True,
            "buses": [
                {"Bus": "B1", "Vm": 1.0, "Pgen": 100, "Pload": 95},
            ],
        }
        findings = _validate_power_flow("PF", result)
        assert any(f["result"] == "pass" for f in findings)

    def test_validate_power_flow_voltage_fail(self):
        from web.components.viz_renderers.pipeline import _validate_power_flow
        result = {
            "converged": True,
            "buses": [
                {"Bus": "B1", "Vm": 0.85, "Pgen": 0, "Pload": 100},
            ],
        }
        findings = _validate_power_flow("PF", result)
        assert any(f["result"] == "fail" for f in findings)
        assert any("0.85" in f["detail"] for f in findings)

    def test_validate_power_flow_voltage_warning(self):
        from web.components.viz_renderers.pipeline import _validate_power_flow
        result = {
            "converged": True,
            "buses": [
                {"Bus": "B1", "Vm": 0.93, "Pgen": 0, "Pload": 50},
            ],
        }
        findings = _validate_power_flow("PF", result)
        assert any(f["result"] == "warning" for f in findings)

    def test_validate_power_flow_not_converged(self):
        from web.components.viz_renderers.pipeline import _validate_power_flow
        result = {"converged": False, "buses": []}
        findings = _validate_power_flow("PF", result)
        assert any(f["result"] == "fail" and "未收敛" in f["detail"] for f in findings)

    def test_validate_power_flow_high_loss(self):
        from web.components.viz_renderers.pipeline import _validate_power_flow
        result = {
            "converged": True,
            "buses": [
                {"Bus": "B1", "Vm": 1.0, "Pgen": 100, "Pload": 50},
            ],
        }
        findings = _validate_power_flow("PF", result)
        assert any(f["result"] == "warning" and "网损" in f["detail"] for f in findings)

    def test_validate_emt_converged(self):
        from web.components.viz_renderers.pipeline import _validate_emt
        findings = _validate_emt("EMT", {"converged": True})
        assert any(f["result"] == "pass" for f in findings)

    def test_validate_emt_not_converged(self):
        from web.components.viz_renderers.pipeline import _validate_emt
        findings = _validate_emt("EMT", {"converged": False})
        assert any(f["result"] == "fail" for f in findings)

    def test_validate_n1_clean(self):
        from web.components.viz_renderers.pipeline import _validate_n1
        findings = _validate_n1("N1", {"violations": []})
        assert any(f["result"] == "pass" for f in findings)

    def test_validate_n1_violations(self):
        from web.components.viz_renderers.pipeline import _validate_n1
        findings = _validate_n1("N1", {"violations": [{"line": "L1", "type": "thermal"}]})
        assert any(f["result"] == "warning" for f in findings)

    def test_validate_vsi_normal(self):
        from web.components.viz_renderers.pipeline import _validate_vsi
        result = {
            "vsi_results": [{"bus": "B1", "vsi": 0.3}],
            "weak_buses": [],
        }
        findings = _validate_vsi("VSI", result)
        assert any(f["result"] == "pass" for f in findings)

    def test_validate_vsi_weak_bus_warning(self):
        from web.components.viz_renderers.pipeline import _validate_vsi
        result = {
            "vsi_results": [{"bus": "B1", "vsi": 0.85}],
            "weak_buses": ["B1"],
        }
        findings = _validate_vsi("VSI", result)
        assert any(f["result"] == "warning" and "弱母线" in f["detail"] for f in findings)

    def test_validate_vsi_out_of_range(self):
        from web.components.viz_renderers.pipeline import _validate_vsi
        result = {
            "vsi_results": [{"bus": "B1", "vsi": 1.5}],
            "weak_buses": [],
        }
        findings = _validate_vsi("VSI", result)
        assert any(f["result"] == "fail" and "超出" in f["detail"] for f in findings)

    def test_validate_short_circuit_normal(self):
        from web.components.viz_renderers.pipeline import _validate_short_circuit
        result = {"fault_location": {"fault_current": 25.0}}
        findings = _validate_short_circuit("SC", result)
        assert any(f["result"] == "pass" for f in findings)

    def test_validate_short_circuit_high_current(self):
        from web.components.viz_renderers.pipeline import _validate_short_circuit
        result = {"fault_location": {"fault_current": 150.0}}
        findings = _validate_short_circuit("SC", result)
        assert any(f["result"] == "warning" for f in findings)

    def test_full_pipeline_validation(self, sample_pipeline_data):
        from web.components.viz_renderers.pipeline import _validate_pipeline
        findings = _validate_pipeline(sample_pipeline_data["steps"])
        assert isinstance(findings, list)
        assert len(findings) > 0
        for f in findings:
            assert "step" in f
            assert "check" in f
            assert "result" in f
            assert "detail" in f
            assert f["result"] in ("pass", "warning", "fail")


# ─── DAG Visualization Tests ───────────────────────────────────────────────

class TestDAGVisualization:
    """Test DAG visualization logic."""

    def test_batch_identification(self, sample_pipeline_data):
        from web.components.viz_renderers.pipeline import _identify_batches
        batches = _identify_batches(sample_pipeline_data["steps"])
        assert len(batches) == 2
        assert len(batches[0]) == 1
        assert batches[0][0]["name"] == "潮流计算"
        assert len(batches[1]) == 2

    def test_sequential_chain(self):
        from web.components.viz_renderers.pipeline import _identify_batches
        steps = [
            {"name": "A", "depends_on": []},
            {"name": "B", "depends_on": ["A"]},
            {"name": "C", "depends_on": ["B"]},
        ]
        batches = _identify_batches(steps)
        assert len(batches) == 3
        assert batches[0][0]["name"] == "A"
        assert batches[1][0]["name"] == "B"
        assert batches[2][0]["name"] == "C"

    def test_all_parallel(self):
        from web.components.viz_renderers.pipeline import _identify_batches
        steps = [
            {"name": "A", "depends_on": []},
            {"name": "B", "depends_on": []},
            {"name": "C", "depends_on": []},
        ]
        batches = _identify_batches(steps)
        assert len(batches) == 1
        assert len(batches[0]) == 3

    def test_dag_text_renders(self, mock_streamlit):
        from web.components.viz_renderers import pipeline as pipeline_mod
        steps = [{"name": "A", "skill": "pf", "status": "success", "depends_on": [], "parallel": False}]
        with patch.object(pipeline_mod.st, "caption", mock_streamlit.caption), \
             patch.object(pipeline_mod.st, "text", mock_streamlit.text):
            pipeline_mod._render_dag_text(steps)
        assert mock_streamlit.caption.called


# ─── Integration Tests ─────────────────────────────────────────────────────

class TestPipelineIntegration:
    """Integration tests for pipeline editor + renderer workflow."""

    def test_editor_config_to_renderer_flow(self):
        """Test that editor output can be consumed by renderer."""
        pipeline_steps = [
            {"name": "潮流", "skill": "power_flow", "config": {}, "depends_on": [], "parallel": False},
            {"name": "N-1", "skill": "n1_security", "config": {}, "depends_on": ["潮流"], "parallel": False},
        ]
        result_data = {
            "steps": [
                {
                    "name": s["name"],
                    "skill": s["skill"],
                    "status": "success",
                    "duration": 5.0,
                    "result_data": {"converged": True},
                    "depends_on": s.get("depends_on", []),
                    "parallel": s.get("parallel", False),
                }
                for s in pipeline_steps
            ],
        }
        assert "steps" in result_data
        assert len(result_data["steps"]) == len(pipeline_steps)

    def test_template_to_execution(self):
        """Test that templates produce valid pipeline structures."""
        from web.components.pipeline_editor import _get_pipeline_templates
        templates = _get_pipeline_templates()
        for name, steps in templates.items():
            seen_names = set()
            for step in steps:
                sname = step.get("name", "")
                for dep in step.get("depends_on", []):
                    assert dep in seen_names, f"Template '{name}': step '{sname}' depends on future step '{dep}'"
                seen_names.add(sname)

    def test_context_building(self, sample_pipeline_data):
        """Test that context for cross-step references is built correctly."""
        from web.components.viz_renderers.pipeline import _build_context_for_step
        steps = sample_pipeline_data["steps"]

        ctx = _build_context_for_step(steps, 1)
        assert "潮流计算" in ctx["steps"]
        assert ctx["steps"]["潮流计算"]["status"] == "success"

        ctx0 = _build_context_for_step(steps, 0)
        assert len(ctx0["steps"]) == 0

    def test_renderer_with_foreach_step(self, mock_streamlit):
        """Test rendering a pipeline with foreach step."""
        data = {
            "steps": [
                {
                    "name": "scan",
                    "skill": "param_scan",
                    "status": "success",
                    "duration": 10.0,
                    "result_data": {"items": ["item1", "item2"]},
                    "foreach": {"items": "params", "item_name": "item"},
                },
            ],
        }
        mock_task = MagicMock()
        mock_task.config = {}
        from web.components.viz_renderers.pipeline import render
        with patch("web.components.viz_renderers.pipeline.st", mock_streamlit):
            render(data, mock_task)

    def test_renderer_with_skipped_step(self, mock_streamlit):
        """Test rendering a pipeline with skipped steps."""
        data = {
            "steps": [
                {"name": "A", "skill": "pf", "status": "failed", "duration": 5.0, "result_data": {}, "error": "test error"},
                {"name": "B", "skill": "n1", "status": "skipped", "duration": 0, "result_data": {}, "depends_on": ["A"]},
            ],
        }
        mock_task = MagicMock()
        mock_task.config = {}
        from web.components.viz_renderers.pipeline import render
        with patch("web.components.viz_renderers.pipeline.st", mock_streamlit):
            render(data, mock_task)
