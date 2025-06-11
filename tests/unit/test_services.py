import json
from pathlib import Path

from shared_tools.services.system_monitor import SystemMonitor
from shared_tools.services.task_queue_manager import TaskQueueManager
from shared_tools.services.corpus_stats_service import CorpusStatsService
from shared_tools.services.activity_log_service import ActivityLogService
from shared_tools.ui_wrappers.base_wrapper import DummySignal

class DummyConfig:
    def __init__(self, stats_path: Path):
        self.stats_path = stats_path
    def get_stats_path(self):
        return str(self.stats_path)
    def get_corpus_dir(self):
        return str(self.stats_path.parent)

class DummyManager:
    def get_corpus_stats(self):
        return {"total_files": 2}

def test_system_monitor(monkeypatch):
    metrics = []
    m = SystemMonitor(interval_ms=10)
    m.system_metrics.connect(lambda c,r,d: metrics.append((c,r,d)))
    monkeypatch.setattr('psutil.cpu_percent', lambda: 1.0)
    monkeypatch.setattr('psutil.virtual_memory', lambda: type('m',(),{'percent':2.0})())
    monkeypatch.setattr('psutil.disk_usage', lambda p: type('d',(),{'percent':3.0})())
    m._emit_metrics()
    assert metrics[-1] == (1.0,2.0,3.0)
    m.stop()
    assert not m.timer.isActive()


def test_task_queue_manager():
    tq = TaskQueueManager(test_mode=True)
    counts = []
    tq.queue_counts_changed.connect(lambda a,b,c,d: counts.append((a,b,c,d)))
    tq.add_task('t', {'name':'x'})
    tq.update_task('t', 'completed', 100)
    summary = tq.get_task_summary()
    assert summary['completed'] == 1
    assert counts


def test_corpus_stats_service(tmp_path):
    stats_file = tmp_path / 'stats.json'
    data = {"total_files":1,"domains":{"a":{"count":1,"size_mb":1}}}
    stats_file.write_text(json.dumps(data))
    cfg = DummyConfig(stats_file)
    svc = CorpusStatsService(cfg)
    received = []
    svc.stats_updated.connect(lambda s: received.append(s))
    svc.refresh_stats()
    assert received and received[0]['total_files'] == 1
    assert svc.get_summary()['total_files'] == 1
    assert svc.get_domain_summary()['a'] == 1
    assert svc.get_domain_size_summary()['a'] == 1.0
    dist = svc.get_domain_distribution()
    assert dist['a'] == 100.0


def test_activity_log_service():
    svc = ActivityLogService()
    entries = []
    svc.activity_added.connect(lambda e: entries.append(e))
    svc.log('test','message')
    assert entries and entries[0]['source'] == 'test'
    assert svc.load_recent(1)
