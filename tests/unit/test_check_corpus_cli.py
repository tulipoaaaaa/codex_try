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


def test_check_corpus(monkeypatch):
    called = {}

    def fake_check(config, validate_metadata, auto_fix, check_integrity):
        called.update({
            "validate_metadata": validate_metadata,
            "auto_fix": auto_fix,
            "check_integrity": check_integrity,
        })

    monkeypatch.setattr(
        "tools.check_corpus_structure.check_corpus_structure", fake_check
    )

    test_args = [
        "check-corpus",
        "--config",
        "tests/data/sample_config.yaml",
        "--validate-metadata",
        "--auto-fix",
        "--check-integrity",
    ]

    cli.main(test_args)

    assert called["validate_metadata"]
    assert called["auto_fix"]
    assert called["check_integrity"]
