import json
import hashlib
from pathlib import Path

from shared_tools.processors.deduplicator import Deduplicator


def test_sha256_duplicate_detection(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    f1 = corpus / "a.txt"
    f2 = corpus / "b.txt"
    f1.write_text("one")
    f2.write_text("two")
    sha = hashlib.sha256(b"same").hexdigest()
    for f in (f1, f2):
        with open(Path(f"{f}.meta"), "w") as m:
            json.dump({"sha256": sha, "title": "x"}, m)
    d = Deduplicator(corpus_dir=corpus)
    d.scan_corpus()
    dups = d.find_duplicates()
    assert any(g.get("hash") == sha for g in dups)
