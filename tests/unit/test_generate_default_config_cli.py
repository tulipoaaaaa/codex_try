import sys
import types

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

import importlib  # noqa: E402
import CorpusBuilderApp.cli as cli  # noqa: E402


def test_generate_default_config(tmp_path):
    cfg_path = tmp_path / "cfg.yaml"

    # Restore real PyYAML functions for this test
    sys.modules.pop("yaml", None)
    real_yaml = importlib.import_module("yaml")
    sys.modules["yaml"] = real_yaml

    exit_code = cli.main(
        ["generate-default-config", "--output", str(cfg_path)]
    )
    assert exit_code == 0
    assert cfg_path.exists()
    with open(cfg_path, "r", encoding="utf-8") as fh:
        data = real_yaml.safe_load(fh)
    assert isinstance(data, dict)
    assert "environment" in data
