from __future__ import annotations

import logging
from typing import Optional, List, Dict

from PySide6.QtCore import QObject, Signal as pyqtSignal

from shared_tools.project_config import ProjectConfig
from tools.check_corpus_structure import check_corpus_structure


class _LogCaptureHandler(logging.Handler):
    """Simple logging handler to capture log records."""

    def __init__(self) -> None:
        super().__init__()
        self.records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - simple
        self.records.append(record)


class CorpusValidatorService(QObject):
    """Service wrapper around ``check_corpus_structure`` utility."""

    validation_started = pyqtSignal()
    validation_completed = pyqtSignal(dict)
    validation_failed = pyqtSignal(str)

    def __init__(
        self,
        project_config: ProjectConfig,
        activity_log_service: Optional[object] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.project_config = project_config
        self.activity_log_service = activity_log_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: Dict[str, object] = {}

    # ------------------------------------------------------------------
    def validate_structure(self) -> None:
        """Run corpus structure validation and emit results."""
        self.validation_started.emit()
        handler = _LogCaptureHandler()
        target_logger = logging.getLogger("tools.check_corpus_structure")
        target_logger.addHandler(handler)
        prev_level = target_logger.level
        target_logger.setLevel(logging.INFO)
        try:
            check_corpus_structure(self.project_config)
            messages = [
                {"level": r.levelname.lower(), "message": r.getMessage()}
                for r in handler.records
            ]
            self.results = {"messages": messages}
            self.validation_completed.emit(self.results)
            if self.activity_log_service:
                for msg in messages:
                    try:
                        self.activity_log_service.log(
                            "CorpusValidator",
                            msg["message"],
                            {"level": msg["level"]},
                        )
                    except Exception:  # pragma: no cover - defensive
                        pass
        except Exception as exc:  # pragma: no cover - runtime guard
            self.logger.error("Validation failed: %s", exc)
            if self.activity_log_service:
                try:
                    self.activity_log_service.log(
                        "CorpusValidator", "Validation failed", {"error": str(exc)}
                    )
                except Exception:
                    pass
            self.validation_failed.emit(str(exc))
        finally:
            target_logger.removeHandler(handler)
            target_logger.setLevel(prev_level)

