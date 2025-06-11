import types
import pytest
from shared_tools.ui_wrappers.base_wrapper import DummySignal

# Patch BaseWrapper and worker thread with lightweight versions
class DummyTarget:
    def __init__(self):
        self.stats = {"files_processed": 3, "success_rate": 1.0}
    def get_stats(self):
        return self.stats

class DummyWorker:
    def __init__(self, target, op, **kw):
        self.progress = DummySignal()
        self.error = DummySignal()
        self.finished = DummySignal()
        self.target = target
    def start(self):
        self.progress.emit(1,1,"done")
        self.finished.emit({"ok": True})
    def isRunning(self):
        return False
    def stop(self):
        pass
    def wait(self):
        pass

class DummyBaseWrapper:
    def __init__(self, config, task_queue_manager=None):
        self.config = config
        self.task_queue_manager = task_queue_manager
        self.logger = "logger"
        self.completed = DummySignal()
        self.status_updated = DummySignal()
        self.progress_updated = DummySignal()
        self.error_occurred = DummySignal()
        self._is_running = False
        self.worker = None
        self.target = DummyTarget()
        self._progress = 0
        self._test_mode = False
    def _create_target_object(self):
        return self.target
    def _get_operation_type(self):
        return "process"
    def start(self, **kw):
        self.worker = DummyWorker(self.target, "process", **kw)
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self._is_running = True
        self.worker.start()
    def stop(self):
        self._is_running = False
    def get_status(self):
        return {"running": self._is_running}
    def is_running(self):
        return self._is_running
    def set_test_mode(self, enabled=True):
        self._test_mode = enabled
    def refresh_config(self):
        self.refreshed = True
    def _on_progress(self, *a):
        self.last_progress = a
    def _on_error(self, e):
        self.last_error = e
    def _on_finished(self, r):
        self._is_running = False
        self.completed.emit(r)

import shared_tools.ui_wrappers.processors.processor_mixin as pm

@pytest.fixture(autouse=True)
def patch_basewrapper(monkeypatch):
    monkeypatch.setattr(pm, "BaseWrapper", DummyBaseWrapper)
    yield

class SimpleProcessor(pm.ProcessorMixin):
    pass

def test_delegated_properties(tmp_config_path):
    proc = SimpleProcessor(config={"path": str(tmp_config_path)})
    assert proc.config == {"path": str(tmp_config_path)}
    assert isinstance(proc.completed, DummySignal)
    assert isinstance(proc.progress_updated, DummySignal)
    assert proc.task_queue_manager is None
    proc.task_queue_manager = "tqm"
    assert proc.task_queue_manager == "tqm"
    proc.processor = "x"
    assert proc.processor == "x"
    assert proc.target is not None

def test_start_stop_get_status():
    proc = SimpleProcessor(config={})
    proc.start()
    assert proc.worker is not None
    status = proc.get_status()
    assert status.get("running") is False
    proc.stop()
    assert not proc.is_running()

def test_processing_stats_and_callbacks():
    proc = SimpleProcessor(config={})
    captured = {}
    proc.completed.connect(lambda r: captured.update(r))
    proc.start()
    assert captured == {"ok": True}
    stats = proc.get_processing_stats()
    assert stats == {"files_processed": 3, "success_rate": 1.0}
    proc.refresh_config()
    assert getattr(proc._bw, "refreshed", False)
