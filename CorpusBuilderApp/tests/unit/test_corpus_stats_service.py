import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest



from shared_tools.services.corpus_stats_service import CorpusStatsService


def test_refresh_stats(tmp_path):
    """Ensure stats are loaded from JSON and signal emitted."""
    stats = {"documents": 5}
    stats_file = tmp_path / "corpus_stats.json"
    with open(stats_file, "w", encoding="utf-8") as fh:
        json.dump(stats, fh)

    cfg = type("Cfg", (object,), {"get_corpus_dir": lambda self: tmp_path})
    service = CorpusStatsService.__new__(CorpusStatsService)
    service.project_config = cfg()
    service.corpus_manager = None
    service.logger = MagicMock()
    service.stats = {}
    service.stats_updated = MagicMock()
    service.stats_updated.emit = MagicMock()

    service.refresh_stats()

    assert service.stats == stats
    service.stats_updated.emit.assert_called_once_with(stats)


def test_get_domain_size_summary():
    service = CorpusStatsService.__new__(CorpusStatsService)
    service.stats = {
        "domains": {
            "A": {"size_mb": 1.2, "pdf_files": 2},
            "B": {"total_size_mb": 3.4, "pdf_files": 1},
        }
    }
    summary = service.get_domain_size_summary()
    assert summary == {"A": 1.2, "B": 3.4}
