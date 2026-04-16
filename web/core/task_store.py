"""
Task persistence layer.

Each task is stored as a JSON file in web/data/tasks/.
Uses atomic write (write to .tmp, then rename) for crash safety.
"""
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

TASKS_DIR = Path(__file__).resolve().parent.parent / "data" / "tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Task:
    id: str
    name: str
    skill_name: str
    status: str  # draft | confirmed | running | done | failed
    created_at: str
    config: Dict[str, Any]
    config_source: str = "nl"  # nl | manual
    nl_prompt: Optional[str] = None
    job_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)  # Execution logs


def _task_path(task_id: str) -> Path:
    return TASKS_DIR / f"task_{task_id}.json"


def create_task(
    name: str,
    skill_name: str,
    config: Dict[str, Any],
    config_source: str = "nl",
    nl_prompt: Optional[str] = None,
) -> Task:
    """Create a new task and persist it."""
    task = Task(
        id=str(uuid.uuid4())[:8],
        name=name,
        skill_name=skill_name,
        status="draft",
        created_at=datetime.now().isoformat(timespec="seconds"),
        config=config,
        config_source=config_source,
        nl_prompt=nl_prompt,
    )
    _save(task)
    return task


def get_task(task_id: str) -> Optional[Task]:
    """Load a task by ID."""
    path = _task_path(task_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Task(**data)


def list_tasks(limit: int = 50, offset: int = 0) -> List[Task]:
    """List tasks sorted by creation time (newest first)."""
    tasks = []
    for p in sorted(TASKS_DIR.glob("task_*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            tasks.append(Task(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return tasks[offset : offset + limit]


def save_task(task: Task) -> None:
    """Persist an existing task."""
    _save(task)


def delete_task(task_id: str) -> bool:
    """Delete a task file. Returns True if deleted."""
    path = _task_path(task_id)
    if path.exists():
        path.unlink()
        return True
    return False


def _save(task: Task) -> None:
    """Atomic write: write to .tmp then rename."""
    path = _task_path(task.id)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(asdict(task), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(str(tmp), str(path))
