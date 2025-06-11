import types
import pytest
from datetime import datetime
from shared_tools.services.task_queue_manager import TaskQueueManager
from shared_tools.services.corpus_stats_service import CorpusStatsService
from shared_tools.services.activity_log_service import ActivityLogService
from app.ui.tabs.dashboard_tab import DashboardTab

class DummyConfig:
    def __init__(self, stats):
        self.stats_path = stats
    def get_stats_path(self):
        return str(self.stats_path)
    def get_corpus_dir(self):
        return str(self.stats_path.parent)

def _make_tab(tmp_path, stats_data):
    stats_file = tmp_path / "stats.json"
    stats_file.write_text(stats_data)
    cfg = DummyConfig(stats_file)
    tab = DashboardTab.__new__(DashboardTab)
    tab.stats_service = CorpusStatsService(cfg)
    tab.task_queue_manager = TaskQueueManager(test_mode=True)
    tab.activity_log_service = ActivityLogService()
    tab.task_history_service = None
    tab.logger = types.SimpleNamespace(warning=lambda *a, **k: None)
    tab.stats_service.refresh_stats()
    return tab

@pytest.fixture(autouse=True)
def patch_psutil(monkeypatch):
    monkeypatch.setattr('psutil.cpu_percent', lambda interval=None: 10.0)
    monkeypatch.setattr('psutil.virtual_memory', lambda: types.SimpleNamespace(percent=20.0))
    monkeypatch.setattr('psutil.disk_usage', lambda p: types.SimpleNamespace(percent=30.0))
    monkeypatch.setattr('psutil.cpu_count', lambda: 2)
    monkeypatch.setattr('psutil.boot_time', lambda: (datetime.now().timestamp() - 3600))
    yield

def test_dashboard_methods(tmp_path):
    tab = _make_tab(tmp_path, '{"total_files":1, "domains":{"ai":{"count":1}}}')
    tab.task_queue_manager.add_task('t', {'status':'completed'})
    health = tab.get_corpus_health_data()
    perf = tab.get_performance_metrics_data()
    quick = tab.get_quick_stats_data()
    alerts = tab.get_alerts_data()
    assert len(health) == 3
    assert len(perf) == 3
    assert len(quick) == 4
    assert alerts
