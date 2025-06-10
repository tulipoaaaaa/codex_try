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

import CorpusBuilderApp.cli as cli  # noqa: E402


def test_stats_cli(monkeypatch, capsys):
    counts = {"A": 2, "B": 1}

    class DummyService:
        def __init__(self, cfg, corpus_manager=None, parent=None):
            pass

        def refresh_stats(self):
            pass

        def get_domain_summary(self):
            return counts

    monkeypatch.setattr(
        "shared_tools.project_config.ProjectConfig.from_yaml",
        lambda path: object(),
    )
    monkeypatch.setattr(
        "shared_tools.services.corpus_stats_service.CorpusStatsService",
        DummyService,
    )

    exit_code = cli.main(["stats", "--config", "cfg.yaml"])
    out_lines = capsys.readouterr().out.strip().splitlines()
    assert any("A:" in line for line in out_lines)
    assert any("B:" in line for line in out_lines)
    assert exit_code == 0
