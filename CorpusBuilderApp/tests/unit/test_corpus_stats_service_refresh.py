import json
from pathlib import Path
from shared_tools.services.corpus_stats_service import CorpusStatsService

class DummyCfg:
    def __init__(self, path: Path):
        self._path = path
    def get_stats_path(self):
        return str(self._path)


def test_refresh_reads_json_and_emits(tmp_path, qapp):
    stats_file = tmp_path / "stats.json"
    data = {"total": 3}
    stats_file.write_text(json.dumps(data))
    cfg = DummyCfg(stats_file)
    service = CorpusStatsService(cfg)
    received = []
    service.stats_updated.connect(lambda s: received.append(s))
    service.refresh_stats()
    assert service.stats == data
    assert received and received[0] == data
