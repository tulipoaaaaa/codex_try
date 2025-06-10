import sys
import types
import importlib
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

# Restore real PyYAML for this test
sys.modules.pop("yaml", None)
yaml = importlib.import_module("yaml")

import CorpusBuilderApp.cli as cli  # noqa: E402


def test_generate_default_config(tmp_path: Path):
    cfg_path = tmp_path / "cfg.yaml"

    exit_code = cli.main(["generate-default-config", "--output", str(cfg_path)])
    assert exit_code == 0
    assert cfg_path.exists()

    with open(cfg_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict)
    assert "environment" in data
