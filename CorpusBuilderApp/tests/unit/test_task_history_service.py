import pytest

from shared_tools.services.task_history_service import TaskHistoryService


def test_add_and_update_task(qapp):
    service = TaskHistoryService()
    added = []
    updated = []
    service.task_added.connect(lambda t: added.append(t))
    service.task_updated.connect(lambda t: updated.append(t))
    service.add_task("t1", {"name": "Task"})
    assert added and added[0]["name"] == "Task"
    service.update_task("t1", status="running", progress=50)
    assert updated and updated[0]["progress"] == 50
    tasks = service.load_recent_tasks()
    assert tasks[-1]["status"] == "running"

