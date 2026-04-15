"""
viz_skill: Visualization registry and dispatcher.

Acts as the "visualization control engine" that loads appropriate
renderers for each simulation skill's results.

Usage:
    from web.components.viz_skill import render_result, is_pipeline_result, render_pipeline
    render_result(task.skill_name, result_data, task)

Adding a new renderer:
    1. Create viz_renderers/my_skill.py
    2. Use @register_renderer("my_skill") on the render() function
    3. Import in viz_renderers/__init__.py
"""
from typing import Callable, Dict, Any, Optional

# ─── Registry ───────────────────────────────────────────────────

_REGISTRY: Dict[str, Callable] = {}


def register_renderer(skill_name: str):
    """Decorator to register a renderer function.

    Usage:
        @register_renderer("power_flow")
        def render(result_data, task, context=None):
            ...
    """
    def decorator(func):
        _REGISTRY[skill_name] = func
        return func
    return decorator


def render_result(skill_name: str, result_data: dict, task, context: dict = None) -> None:
    """Dispatch to the appropriate renderer for a skill's results.

    Falls back to auto-detection if no renderer is registered, then to generic.
    """
    renderer = _REGISTRY.get(skill_name)
    if renderer:
        renderer(result_data, task, context)
        return

    # Auto-detection fallback
    detected = detect_result_type(result_data)
    if detected and detected != skill_name:
        detected_renderer = _REGISTRY.get(detected)
        if detected_renderer:
            detected_renderer(result_data, task, context)
            return

    # Final fallback to generic
    generic = _REGISTRY.get("generic")
    if generic:
        generic(result_data, task, context)


# ─── Auto-Detection ─────────────────────────────────────────────

def detect_result_type(result_data: dict) -> Optional[str]:
    """Detect the result type from data shape when skill_name is unknown."""
    if not result_data:
        return None

    # Power flow: has buses/branches OR bus_count/branch_count with converged flag
    if "buses" in result_data and "branches" in result_data:
        return "power_flow"
    if "bus_count" in result_data and "branch_count" in result_data and "converged" in result_data:
        return "power_flow"

    # EMT simulation: has plots
    if "plots" in result_data or "plot_count" in result_data:
        return "emt_simulation"

    # N-1 security: has violation info
    if "violation_count" in result_data or "total_branches" in result_data:
        return "n1_security"

    # VSI weak bus: has vsi_results or weak_buses
    if "vsi_results" in result_data or "weak_buses" in result_data:
        return "vsi_weak_bus"

    # Short circuit: has fault_location or short_circuit_mva
    if "fault_location" in result_data or "short_circuit_mva" in result_data:
        return "short_circuit"

    # EMT fault study: has scenarios or fault_end_time
    if "scenarios" in result_data or "fault_end_time" in result_data:
        return "emt_fault_study"

    return None


def is_pipeline_result(result_data: dict) -> bool:
    """Check if result_data is from a pipeline execution."""
    return isinstance(result_data.get("steps"), list)


# ─── Step Proxy ─────────────────────────────────────────────────

class _StepProxy:
    """Adapter that makes a pipeline step dict look like a Task object.

    Allows skill renderers to work with both Task objects and pipeline steps.
    """
    def __init__(self, step: dict, context: dict = None):
        self._step = step
        self._context = context or {}

    @property
    def skill_name(self) -> str:
        return self._step.get("skill", "")

    @property
    def name(self) -> str:
        return self._step.get("name", self._step.get("skill", ""))

    @property
    def status(self) -> str:
        s = self._step.get("status", "")
        if s == "success":
            return "done"
        elif s == "failed":
            return "failed"
        return s

    @property
    def result_data(self) -> dict:
        return self._step.get("result_data", {})

    @property
    def artifacts(self) -> list:
        return self._step.get("artifacts", [])

    @property
    def metrics(self) -> dict:
        return self._step.get("metrics", {})

    @property
    def config(self) -> dict:
        return self._step.get("config", {})

    @property
    def error(self) -> Optional[str]:
        return self._step.get("error")


def render_step(step: dict, context: dict = None) -> None:
    """Render a single pipeline step by dispatching to its skill renderer."""
    proxy = _StepProxy(step, context)
    skill_name = step.get("skill", "")

    if step.get("status") == "failed":
        import streamlit as st
        st.error(f"步骤失败: {step.get('error', '未知错误')}")
        return

    result_data = step.get("result_data", {})
    render_result(skill_name, result_data, proxy, context)


def render_pipeline(task) -> None:
    """Render pipeline results by delegating to the study_pipeline renderer.

    This is called from task_results.py when is_pipeline_result() is True.
    It loads the pipeline renderer and dispatches to it.
    """
    from web.components.viz_renderers import pipeline  # noqa: F401 — ensures registered
    renderer = _REGISTRY.get("study_pipeline")
    if renderer:
        renderer(task.result_data, task)


# ─── Matplotlib Chinese Font Config ─────────────────────────────
# Applied at import time so all renderers benefit.

import matplotlib
matplotlib.rcParams['font.sans-serif'] = [
    'Noto Sans CJK SC', 'Noto Sans CJK JP', 'Noto Sans CJK',
    'Droid Sans Fallback', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False


# ─── Register all renderers ─────────────────────────────────────
# Import all renderer modules to trigger @register_renderer decorators.
# Done at module level so renderers are available immediately on import.
from web.components.viz_renderers import (  # noqa: F401
    power_flow,       # noqa: F401
    emt_simulation,   # noqa: F401
    n1_security,      # noqa: F401
    generic,          # noqa: F401
    pipeline,         # noqa: F401
    vsi_weak_bus,     # noqa: F401
    short_circuit,    # noqa: F401
    emt_fault_study,  # noqa: F401
)
