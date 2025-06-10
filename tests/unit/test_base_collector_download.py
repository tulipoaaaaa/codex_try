import hashlib
import json
from types import SimpleNamespace
import time

import requests

from shared_tools.collectors.base_collector import BaseCollector


class DummyCollector(BaseCollector):
    def collect(self, *a, **k):
        pass


def test_download_file_retries_and_hash(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    log_dir = tmp_path / "log"
    meta_dir = tmp_path / "meta"
    cfg = SimpleNamespace(
        raw_data_dir=raw,
        log_dir=log_dir,
        metadata_dir=meta_dir,
        domain_configs={},
    )
    cfg.get_metadata_dir = lambda: meta_dir
    collector = DummyCollector(cfg)

    attempts = {"count": 0}

    class Resp:
        def __init__(self, content=b"data"):
            self.headers = {"Content-Length": str(len(content))}
            self._content = content

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=8192):
            yield self._content

    def fake_get(url, headers=None, stream=True, timeout=30):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise requests.RequestException("fail")
        return Resp()

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    path = collector.download_file("http://example.com/file", "file.txt")
    assert attempts["count"] == 2
    assert path is not None
    sha = hashlib.sha256(b"data").hexdigest()
    cache = json.load(open(meta_dir / "seen_hashes.json"))
    assert cache[sha] == str(path)
