"""
Task executor: runs skills in background threads.

Pattern:
1. Load task from store
2. Validate config
3. Run skill.run(config)
4. Persist result data, artifacts, metrics
5. Update task status to done/failed
"""
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# Add smart_config to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from web.core import task_store, skill_catalog


def execute_task(task_id: str) -> None:
    """Execute a task in a background thread.

    Updates task status: confirmed → running → done/failed
    """
    task = task_store.get_task(task_id)
    if task is None:
        return

    task.status = "running"
    task.started_at = datetime.now().isoformat(timespec="seconds")
    task.error = None
    task_store.save_task(task)

    skill = skill_catalog.get_skill(task.skill_name)
    if skill is None:
        task.status = "failed"
        task.error = f"Skill '{task.skill_name}' not found"
        task.completed_at = datetime.now().isoformat(timespec="seconds")
        task_store.save_task(task)
        return

    # Validate before running
    try:
        validation = skill.validate(task.config)
        if not getattr(validation, "valid", False):
            task.status = "failed"
            errors = getattr(validation, "errors", ["Unknown validation error"])
            task.error = f"Config validation failed: {'; '.join(errors)}"
            task.completed_at = datetime.now().isoformat(timespec="seconds")
            task_store.save_task(task)
            return
    except Exception as e:
        task.status = "failed"
        task.error = f"Validation error: {e}"
        task.completed_at = datetime.now().isoformat(timespec="seconds")
        task_store.save_task(task)
        return

    # Execute
    try:
        result = skill.run(task.config)

        task.result_data = result.data if result.data else {}
        task.artifacts = [
            {
                "type": a.type,
                "path": a.path,
                "size": getattr(a, "size", 0),
                "description": getattr(a, "description", ""),
            }
            for a in getattr(result, "artifacts", [])
        ]
        task.metrics = getattr(result, "metrics", {})
        task.job_id = getattr(result, "job_id", None)

        if getattr(result, "success", False) or str(getattr(result, "status", "")) == "SUCCESS":
            task.status = "done"
        else:
            task.status = "failed"
            task.error = getattr(result, "error", "Skill returned failure")

    except Exception as e:
        task.status = "failed"
        task.error = f"Execution error: {type(e).__name__}: {e}"

    task.completed_at = datetime.now().isoformat(timespec="seconds")
    task_store.save_task(task)


def run_async(task_id: str) -> None:
    """Start task execution in a background thread."""
    thread = threading.Thread(target=execute_task, args=(task_id,), daemon=True)
    thread.start()
