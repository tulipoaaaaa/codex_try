import pytest
from shared_tools.ui_wrappers.base_wrapper import DummySignal
import shared_tools.ui_wrappers.processors.processor_mixin as pm

# Dummy implementations reused from processor mixin tests
class DummyTarget:
    def __init__(self):
        self.stats = {"files_processed": 1, "success_rate": 1.0}
    def get_stats(self):
        return self.stats

class DummyWorker:
    def __init__(self, *a, **k):
        self.progress = DummySignal()
        self.error = DummySignal()
        self.finished = DummySignal()
        self.file_processed = DummySignal()
        self.domain_processed = DummySignal()
        self.document_classified = DummySignal()
        self.processing_completed = DummySignal()
    def start(self):
        self.progress.emit(1,1,"ok")
        self.file_processed.emit("f", True)
        self.document_classified.emit("doc","domain",1.0)
        self.domain_processed.emit("dom",1,1)
        self.finished.emit({"done": True})
        self.processing_completed.emit({"doc": {"domain": "test"}})
    def isRunning(self):
        return False
    def stop(self):
        pass
    def wait(self):
        pass

class DummyBaseWrapper(pm.BaseWrapper):
    def __init__(self, config, task_queue_manager=None):
        super().__init__(config, task_queue_manager=task_queue_manager, test_mode=True)
        self.target = DummyTarget()
    def _create_target_object(self):
        return self.target
    def _get_operation_type(self):
        return "process"

@pytest.fixture(autouse=True)
def patch_base(monkeypatch):
    monkeypatch.setattr(pm, "BaseWrapper", DummyBaseWrapper)
    yield


@pytest.fixture(autouse=True)
def patch_workers(monkeypatch):
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.pdf_extractor_wrapper.PDFExtractorWorker", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.text_extractor_wrapper.TextExtractorWorker", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.quality_control_wrapper.QCWorkerThread", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.corpus_balancer_wrapper.CorpusBalancerWorker", DummyWorker)
    yield

def _capture(signal):
    data = []
    signal.connect(lambda *a: data.append(a))
    return data

@pytest.mark.parametrize("import_path,start_method,args", [
    ("shared_tools.ui_wrappers.processors.pdf_extractor_wrapper.PDFExtractorWrapper", "start_batch_processing", [["f"]]),
    ("shared_tools.ui_wrappers.processors.text_extractor_wrapper.TextExtractorWrapper", "start_batch_processing", [["f"]]),
    ("shared_tools.ui_wrappers.processors.quality_control_wrapper.QualityControlWrapper", "start", [["f"]]),
    ("shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWrapper", "start", [{"doc": {"text": "t"}}]),
    ("shared_tools.ui_wrappers.processors.corpus_balancer_wrapper.CorpusBalancerWrapper", "start_balancing", [["d"]]),
])
def test_wrapper_basic(monkeypatch, import_path, start_method, args):
    module_path, class_name = import_path.rsplit('.',1)
    Wrapper = getattr(__import__(module_path, fromlist=[class_name]), class_name)
    w = Wrapper(config={})
    files = _capture(w.file_processed)
    done_signal = getattr(w, "batch_completed", getattr(w, "completed", None))
    assert done_signal is not None
    done = _capture(done_signal)
    getattr(w, start_method)(*args)
    assert not w._is_running
    assert files
    assert done
