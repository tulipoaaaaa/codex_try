from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from PySide6.QtCore import QObject, Signal as pyqtSignal

from shared_tools.storage.corpus_manager import CorpusManager


class CorpusStatsService(QObject):
    """Service for loading and providing corpus statistics."""

    stats_updated = pyqtSignal(dict)

    def __init__(self, project_config, corpus_manager: Optional[CorpusManager] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.project_config = project_config
        self.corpus_manager = corpus_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats: Dict[str, object] = {}

    # ------------------------------------------------------------------
    def _stats_file(self) -> Optional[Path]:
        """Return path to the corpus statistics JSON file if available."""
        if hasattr(self.project_config, "get_stats_path"):
            try:
                return Path(self.project_config.get_stats_path())
            except Exception:  # pragma: no cover - defensive
                return None
        if hasattr(self.project_config, "get_corpus_root"):
            try:
                return Path(self.project_config.get_corpus_root()) / "corpus_stats.json"
            except Exception:  # pragma: no cover - defensive
                return None
        return None

    # ------------------------------------------------------------------
    def refresh_stats(self) -> None:
        """Try to load corpus statistics from manager or JSON file."""
        stats: Dict[str, object] = {}

        if self.corpus_manager and hasattr(self.corpus_manager, "get_corpus_stats"):
            try:
                stats = self.corpus_manager.get_corpus_stats()  # type: ignore[attr-defined]
            except Exception as exc:  # pragma: no cover - runtime guard
                self.logger.debug("CorpusManager.get_corpus_stats failed: %s", exc)

        if not stats:
            path = self._stats_file()
            if path and path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        stats = json.load(fh)
                except Exception as exc:  # pragma: no cover - runtime guard
                    self.logger.debug("Failed loading stats file %s: %s", path, exc)

        if stats:
            self.stats = stats
        self.stats_updated.emit(stats)

    # ------------------------------------------------------------------
    def get_domain_summary(self) -> Dict[str, int]:
        """Return mapping of domain name to document count."""
        domains = self.stats.get("domains", {}) if isinstance(self.stats, dict) else {}
        summary: Dict[str, int] = {}
        if isinstance(domains, dict):
            for domain, data in domains.items():
                if isinstance(data, dict):
                    count = (
                        data.get("total_files")
                        or data.get("pdf_files")
                        or data.get("count")
                        or 0
                    )
                else:
                    count = int(data) if isinstance(data, (int, float)) else 0
                summary[domain] = count
        return summary

    # ------------------------------------------------------------------
    def get_domain_size_summary(self) -> Dict[str, float]:
        """Return mapping of domain name to size in MB."""
        domains = self.stats.get("domains", {}) if isinstance(self.stats, dict) else {}
        summary: Dict[str, float] = {}
        if isinstance(domains, dict):
            for domain, data in domains.items():
                if isinstance(data, dict):
                    size = (
                        data.get("size_mb")
                        or data.get("total_size_mb")
                        or 0
                    )
                else:
                    size = float(data) if isinstance(data, (int, float)) else 0.0
                summary[domain] = float(size)
        return summary

    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, object]:
        """Return basic corpus summary information."""
        stats = self.stats if isinstance(self.stats, dict) else {}
        return {
            "total_files": stats.get("total_files") or stats.get("doc_count") or 0,
            "total_size_mb": stats.get("total_size_mb") or stats.get("total_size") or 0,
            "total_tokens": stats.get("total_tokens", 0),
            "active_domains": len(stats.get("domains", {})),
        }

    # ------------------------------------------------------------------
    def get_domain_distribution(self) -> Dict[str, float]:
        """Return percent distribution of documents by domain."""
        counts = self.get_domain_summary()
        total = sum(counts.values())
        if not total:
            return {}
        return {d: round((c / total) * 100, 2) for d, c in counts.items()}

    # ------------------------------------------------------------------
    def get_language_distribution(self, metadata_dir: Path | str) -> Dict[str, int]:
        """Count documents by language from metadata JSON files."""
        path = Path(metadata_dir)
        counts: Dict[str, int] = {}
        if not path.exists():
            return counts
        for meta in path.rglob("*.json"):
            try:
                with open(meta, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                lang = data.get("language") or data.get("lang")
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
            except Exception:  # pragma: no cover - runtime guard
                continue
        return counts

    # ------------------------------------------------------------------
    def get_daily_document_counts(self, metadata_dir: Path | str) -> Dict[str, int]:
        """Return mapping of ISO date to document count from metadata timestamps."""
        path = Path(metadata_dir)
        counts: Dict[str, int] = {}
        if not path.exists():
            return counts
        for meta in path.rglob("*.json"):
            try:
                with open(meta, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                ts = (
                    data.get("timestamp")
                    or data.get("date")
                    or data.get("created")
                    or data.get("created_at")
                )
                if not ts:
                    continue
                dt = datetime.fromisoformat(str(ts))
                day = dt.date().isoformat()
                counts[day] = counts.get(day, 0) + 1
            except Exception:  # pragma: no cover - runtime guard
                continue
        return counts
