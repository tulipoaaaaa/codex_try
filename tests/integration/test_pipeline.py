import json
from pathlib import Path
from shared_tools.ui_wrappers.base_wrapper import DummySignal
import pytest

pytest.skip("integration pipeline not configured", allow_module_level=True)
import shared_tools.ui_wrappers.processors.processor_mixin as pm

class DummyTarget:
    def __init__(self):
        self.stats = {"files_processed": 1, "success_rate": 1.0}
    def get_stats(self):
        return self.stats
    def extract_text(self, path, **k):
        return "text", {}
    def process(self, **k):
        return {}
    def classify(self, text, title=None):
        return {"domain": "ai", "confidence": 1.0}

class DummyWorker:
    def __init__(self, *a, **k):
        self.progress = DummySignal()
        self.error = DummySignal()
        self.finished = DummySignal()
        self.file_processed = DummySignal()
        self.document_classified = DummySignal()
        self.processing_completed = DummySignal()
    def start(self):
        self.progress.emit(1,1,"ok")
        self.file_processed.emit("f", True)
        self.document_classified.emit("doc","ai",1.0)
        self.finished.emit({"done": True})
        self.processing_completed.emit({"doc": {"domain": "ai"}})
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

import pytest
from shared_tools.services.corpus_stats_service import CorpusStatsService
from shared_tools.services.task_queue_manager import TaskQueueManager
from shared_tools.services.activity_log_service import ActivityLogService

@pytest.fixture(autouse=True)
def patch_classes(monkeypatch):
    monkeypatch.setattr(pm, "BaseWrapper", DummyBaseWrapper)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.pdf_extractor_wrapper.PDFExtractorWorker", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.text_extractor_wrapper.TextExtractorWorker", DummyWorker)
    monkeypatch.setattr("shared_tools.ui_wrappers.processors.domain_classifier_wrapper.DomainClassifierWorkerThread", DummyWorker)
    yield

def test_full_pipeline(tmp_path):
    tq = TaskQueueManager(test_mode=True)
    from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper
    from shared_tools.ui_wrappers.processors.text_extractor_wrapper import TextExtractorWrapper
    from shared_tools.ui_wrappers.processors.domain_classifier_wrapper import DomainClassifierWrapper
    pdf = PDFExtractorWrapper(config={}, task_queue_manager=tq)
    text = TextExtractorWrapper(config={}, task_queue_manager=tq)
    domain = DomainClassifierWrapper(config={}, task_queue_manager=tq)
    stats_file = tmp_path / "stats.json"
    svc = CorpusStatsService(type("Cfg",(),{"get_stats_path":lambda self:str(stats_file),"get_corpus_dir":lambda self:str(tmp_path)})())

    pdf_results = []
    text_results = []
    class_results = []
    pdf.file_processed.connect(lambda f,s: pdf_results.append(f))
    text.file_processed.connect(lambda f,s: text_results.append(f))
    domain.document_classified.connect(lambda d,dom,c: class_results.append(dom))

    pdf.start_batch_processing(["doc.pdf"])
    text.start_batch_processing(pdf_results)
    domain.start({"doc": {"text": "content"}})

    svc.stats = {"domains": {"ai": {"count": len(class_results)}}, "total_files": len(class_results)}
    summary = svc.get_domain_summary()
    assert summary["ai"] == 1
