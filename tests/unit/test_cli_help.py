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

from CorpusBuilderApp import cli  # noqa: E402


def test_help_message_empty_args(capsys):
    exit_code = cli.main([])
    out = capsys.readouterr().out
    assert "generate-default-config" in out
    assert "diff-corpus" in out
    assert exit_code == 0


def test_help_message_flag(capsys):
    exit_code = cli.main(["--help"])
    out = capsys.readouterr().out
    assert "export-corpus" in out
    assert exit_code == 0
