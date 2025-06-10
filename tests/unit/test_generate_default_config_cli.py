import sys
import types
import yaml
import json
from pathlib import Path

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

from CorpusBuilderApp import cli  # noqa: E402


def test_generate_default_config(tmp_path: Path, monkeypatch):
    out_file = tmp_path / "cfg.yaml"
    monkeypatch.setattr(
        yaml,
        "safe_dump",
        lambda data, fh, sort_keys=False: fh.write(json.dumps(data)),
    )
    monkeypatch.setattr(yaml, "safe_load", lambda text: json.loads(text))
    result = cli.main(["generate-default-config", "--output", str(out_file)])
    assert result == 0
    assert out_file.exists()
    data = yaml.safe_load(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "environment" in data

