from PySide6.QtCore import QObject, Signal as pyqtSignal, QThread, QTimer
import time
from typing import Optional

from shared_tools.services.task_history_service import TaskHistoryService
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from shared_tools.services.task_queue_manager import TaskQueueManager
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from uuid import uuid4

from pathlib import Path


class DummySignal:
    """Lightweight signal used in test mode."""

    def __init__(self) -> None:
        self._slots: list = []

    def connect(self, slot) -> None:  # pragma: no cover - simple store
        self._slots.append(slot)

    def emit(self, *args, **kwargs) -> None:  # pragma: no cover - runtime helper
        for s in list(self._slots):
            s(*args, **kwargs)

class BaseWorkerThread(QThread):
    """Base worker thread for all collectors/processors"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, target_object, operation_type="collect", **kwargs):
        QThread.__init__(self)  # Initialize QThread explicitly
        self.target = target_object
        self.operation_type = operation_type
        self.kwargs = kwargs
        self._should_stop = False
        
    def run(self):
        try:
            if self.operation_type == "collect":
                results = self.target.collect(**self.kwargs)
            elif self.operation_type == "extract":
                results = self.target.extract_text(**self.kwargs)
            elif self.operation_type == "process":
                results = self.target.process(**self.kwargs)
            else:
                results = getattr(self.target, self.operation_type)(**self.kwargs)
                
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._should_stop = True

class BaseWrapper(QObject):
    """Base wrapper for all collectors and processors"""
    
    # Standard UI signals
    progress_updated = pyqtSignal(int)  # 0-100 percentage
    status_updated = pyqtSignal(str)    # Status message
    error_occurred = pyqtSignal(str)    # Error message
    completed = pyqtSignal(dict)        # Results dictionary
    
    def __init__(
        self,
        config,
        activity_log_service=None,
        task_history_service: TaskHistoryService | None = None,
        task_queue_manager: "TaskQueueManager | None" = None,
        test_mode: bool = False,
    ):
        QObject.__init__(self)  # Initialize QObject explicitly
        
        self.config = config
        self.worker = None
        self._is_running = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.activity_log_service = activity_log_service
        self.task_history_service = task_history_service
        self._task_id: str | None = None
        self.task_queue_manager = task_queue_manager
        self._progress = 0
        self._test_mode = False
        if test_mode:
            self.set_test_mode(True)
        
    @abstractmethod
    def _create_target_object(self):
        """Create the actual collector/processor object"""
        pass
        
    @abstractmethod
    def _get_operation_type(self):
        """Get the operation type for the worker thread"""
        pass
        
    def start(self, **kwargs):
        """Start the collection/processing operation"""
        if self._is_running:
            self.status_updated.emit("Operation already in progress")
            return

        self._is_running = True
        self.status_updated.emit("Starting operation...")
        self._task_id = str(uuid4())
        self._progress = 0
        if self.task_history_service:
            self.task_history_service.add_task(
                self._task_id,
                {"name": self.__class__.__name__, "status": "running", "progress": 0},
            )
        if self.task_queue_manager:
            self.task_queue_manager.add_task(
                self._task_id,
                {"name": self.__class__.__name__},
            )
        if self.activity_log_service:
            try:
                self.activity_log_service.log(
                    self.__class__.__name__,
                    "Task started",
                    {"status": "running", "task_id": self._task_id},
                )
            except Exception as exc:
                self.logger.warning("Activity log failed on start: %s", exc)
        
        target_obj = self._create_target_object()
        operation_type = self._get_operation_type()
        
        self.worker = BaseWorkerThread(target_obj, operation_type, **kwargs)
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        
    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress updates"""
        if total > 0:
            percentage = min(100, int((current / total) * 100))
            self.progress_updated.emit(percentage)
            if self.task_history_service and self._task_id:
                self.task_history_service.update_task(self._task_id, progress=percentage)
            if self.task_queue_manager and self._task_id:
                self.task_queue_manager.update_task(
                    self._task_id,
                    "running",
                    percentage,
                )
            self._progress = percentage
        if message:
            self.status_updated.emit(message)
        if self.task_history_service and self._current_task_id and total > 0:
            percentage = min(100, int((current / total) * 100))
            self.task_history_service.update_progress(self._current_task_id, percentage)
            
    def _on_error(self, error_message: str):
        """Handle errors"""
        self._is_running = False
        self.error_occurred.emit(error_message)
        self.status_updated.emit(f"Error: {error_message}")
        if self.task_history_service and self._task_id:
            self.task_history_service.update_task(
                self._task_id, status="error", error_message=error_message
            )
        if self.task_queue_manager and self._task_id:
            self.task_queue_manager.update_task(
                self._task_id,
                "failed",
                self._progress,
            )
        if self.activity_log_service:
            try:
                self.activity_log_service.log(
                    self.__class__.__name__,
                    "Task error",
                    {"status": "error", "task_id": self._task_id, "error_message": error_message},
                )
            except Exception as exc:
                self.logger.warning("Activity log failed on error: %s", exc)
        
    def _on_finished(self, results: Dict[str, Any]):
        """Handle completion"""
        self._is_running = False
        self.completed.emit(results)
        self.status_updated.emit("Operation completed successfully")
        if self.task_history_service and self._task_id:
            self.task_history_service.update_task(
                self._task_id, status="success", progress=100
            )
        if self.task_queue_manager and self._task_id:
            self.task_queue_manager.update_task(
                self._task_id,
                "completed",
                100,
            )
        if self.activity_log_service:
            try:
                self.activity_log_service.log(
                    self.__class__.__name__,
                    "Task completed",
                    {"status": "success", "task_id": self._task_id},
                )
            except Exception as exc:
                self.logger.warning("Activity log failed on complete: %s", exc)
        
    def stop(self):
        """Stop the operation"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self._is_running = False
            self.status_updated.emit("Operation stopped")
        if self.task_history_service and self._task_id:
            self.task_history_service.update_task(self._task_id, status="stopped")
        if self.task_queue_manager and self._task_id:
            self.task_queue_manager.update_task(self._task_id, "stopped")
            
    def get_status(self) -> Dict[str, Any]:
        """Get current operation status"""
        return {
            "is_running": self._is_running,
            "type": self.__class__.__name__
        }
        
    def is_running(self) -> bool:
        """Check if operation is currently running"""
        return self._is_running

    # ------------------------------------------------------------------
    def set_test_mode(self, enabled: bool = True) -> None:
        """Replace Qt signals with in-memory stubs for tests."""
        self._test_mode = enabled
        if enabled:
            for name in dir(self):
                try:
                    attr = getattr(self, name)
                except Exception:
                    continue
                if hasattr(attr, "connect") and hasattr(attr, "emit"):
                    setattr(self, name, DummySignal())

    def refresh_config(self):
        """Default no-op implementation; can be overridden by subclasses."""
        pass

class CollectorWrapperMixin:
    """Mixin for collector-specific functionality"""
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"documents_collected": 0, "last_run": None}

class ProcessorWrapperMixin:
    """Mixin for processor-specific functionality"""
    
    file_processed = pyqtSignal(str, bool)  # filepath, success
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if hasattr(self, 'target') and hasattr(self.target, 'get_stats'):
            return self.target.get_stats()
        return {"files_processed": 0, "success_rate": 0.0}