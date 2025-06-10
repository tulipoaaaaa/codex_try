import sys
import types
import json

# Stub heavy modules before importing CLI
for mod in [
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    "plotly",
    "plotly.subplots",
    "plotly.graph_objects",
    "plotly.express",
    "requests",
    "yaml",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

import CorpusBuilderApp.cli as cli  # noqa: E402


def test_diff_corpus_no_changes(tmp_path, capsys):
    data = {
        "domains": {"a": {"txt": 1, "json": 1}},
        "total_files": 2,
        "total_tokens": 10,
        "hashes": ["h1"],
    }
    p1 = tmp_path / "p1.json"
    p2 = tmp_path / "p2.json"
    p1.write_text(json.dumps(data))
    p2.write_text(json.dumps(data))

    exit_code = cli.main(["diff-corpus", "--profile-a", str(p1), "--profile-b", str(p2)])
    captured = capsys.readouterr().out
    assert "Total file delta: 0" in captured
    assert exit_code == 0


def test_diff_corpus_detect_changes(tmp_path, capsys):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    p1.write_text(json.dumps({"domains": {}, "total_files": 0, "total_tokens": 0, "hashes": []}))
    p2.write_text(
        json.dumps({"domains": {"x": {"txt": 1, "json": 0}}, "total_files": 1, "total_tokens": 5, "hashes": ["a"]})
    )
    exit_code = cli.main(["diff-corpus", "--profile-a", str(p1), "--profile-b", str(p2)])
    out = capsys.readouterr().out
    assert "Total file delta: 1" in out
    assert exit_code == 1
