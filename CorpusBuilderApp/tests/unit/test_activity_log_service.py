import pytest

def test_log_records_and_emits(qapp):
    from shared_tools.services.activity_log_service import ActivityLogService
    service = ActivityLogService()
    received = []
    service.activity_added.connect(lambda e: received.append(e))
    service.log("test", "message", {"a":1})
    assert received
    assert service.load_recent(1)[0] == received[0]


def test_service_updates_recent_activity(qapp, mock_project_config):
    # Provide missing Qt classes when running with stubs
    from PySide6 import QtWidgets, QtCore
    if not hasattr(QtWidgets, "QScrollArea"):
        QtWidgets.QScrollArea = object
    if getattr(QtCore, "QObject", None) is object:
        class DummyQObject(object):
            def __init__(self, *a, **k):
                pass
        QtCore.QObject = DummyQObject

    from shared_tools.services.activity_log_service import ActivityLogService

    service = ActivityLogService()

    from app.ui.widgets.recent_activity import RecentActivity

    widget = RecentActivity(mock_project_config)
    before = widget.activities_layout.count()
    service.activity_added.connect(widget.add_activity)
    service.log("Test", "Something happened")
    assert widget.activities_layout.count() == before + 1
