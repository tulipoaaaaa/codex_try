import pytest
from shared_tools.services.activity_log_service import ActivityLogService

def test_log_records_and_emits(qapp):
    service = ActivityLogService()
    received = []
    service.activity_added.connect(lambda e: received.append(e))
    service.log("test", "message", {"a":1})
    assert received
    assert service.load_recent(1)[0] == received[0]
