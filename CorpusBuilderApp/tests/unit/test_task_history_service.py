from shared_tools.services.task_history_service import TaskHistoryService


def test_task_history_roundtrip(tmp_path, qapp):
    history_file = tmp_path / "history.json"
    svc = TaskHistoryService(history_file)
    svc.start_task("t1", "Test")
    svc.update_progress("t1", 50)
    svc.complete_task("t1")

    data = svc.get_history()
    assert data and data[0]["status"] == "completed"
    assert data[0]["progress"] == 100

    svc2 = TaskHistoryService(history_file)
    assert svc2.get_history()


def test_task_failure(tmp_path, qapp):
    svc = TaskHistoryService(None)
    svc.start_task("t2", "Fail")
    svc.fail_task("t2", "boom")
    hist = svc.get_history()
    assert hist[0]["status"] == "failed"
    assert hist[0]["error"] == "boom"
