import importlib
import sys
from shared_tools.project_config import ProjectConfig


def _write(path, data):
    sys.modules.pop('yaml', None)
    yaml = importlib.import_module('yaml')
    import shared_tools.project_config as project_config
    importlib.reload(project_config)
    with open(path, 'w') as f:
        yaml.safe_dump(data, f)


def test_pure_new_schema(tmp_path):
    corpus = tmp_path / "corp"
    data = {
        "environment": {"active": "test"},
        "environments": {
            "test": {
                "corpus_root": str(corpus),
                "raw_data_dir": str(corpus / "raw"),
                "processed_dir": str(corpus / "proc"),
                "metadata_dir": str(corpus / "meta"),
                "logs_dir": str(corpus / "logs"),
            }
        },
    }
    cfg_path = tmp_path / "cfg.yaml"
    _write(cfg_path, data)
    cfg = ProjectConfig.from_yaml(str(cfg_path))
    assert cfg.get_corpus_root() == corpus
    assert cfg.get_raw_dir() == corpus / "raw"
    assert cfg.get_processed_dir() == corpus / "proc"
    assert cfg.get_metadata_dir() == corpus / "meta"
    assert cfg.get_logs_dir() == corpus / "logs"


def test_pure_legacy_schema(tmp_path):
    corpus = tmp_path / "corp"
    data = {
        "environment": {"active": "test"},
        "directories": {
            "corpus_root": str(corpus),
            "raw_data_dir": str(corpus / "raw"),
            "processed_dir": str(corpus / "proc"),
            "metadata_dir": str(corpus / "meta"),
            "logs_dir": str(corpus / "logs"),
        },
    }
    cfg_path = tmp_path / "cfg.yaml"
    _write(cfg_path, data)
    cfg = ProjectConfig.from_yaml(str(cfg_path))
    assert cfg.get_corpus_root() == corpus
    assert cfg.get_raw_dir() == corpus / "raw"
    assert cfg.get_processed_dir() == corpus / "proc"
    assert cfg.get_metadata_dir() == corpus / "meta"
    assert cfg.get_logs_dir() == corpus / "logs"
    assert cfg.get("environments.test.corpus_root") == str(corpus)


def test_mixed_schema_prioritises_directories(tmp_path):
    corpus = tmp_path / "corp"
    env_corpus = tmp_path / "env_corp"
    data = {
        "environment": {"active": "test"},
        "directories": {
            "corpus_root": str(corpus),
            "raw_data_dir": str(corpus / "raw"),
            "processed_dir": str(corpus / "proc"),
            "metadata_dir": str(corpus / "meta"),
            "logs_dir": str(corpus / "logs"),
        },
        "environments": {
            "test": {
                "corpus_root": str(env_corpus),
                "raw_data_dir": str(env_corpus / "raw"),
                "processed_dir": str(env_corpus / "proc"),
                "metadata_dir": str(env_corpus / "meta"),
                "logs_dir": str(env_corpus / "logs"),
            }
        },
    }
    cfg_path = tmp_path / "cfg.yaml"
    _write(cfg_path, data)
    cfg = ProjectConfig.from_yaml(str(cfg_path))
    assert cfg.get_corpus_root() == corpus
    assert cfg.get_raw_dir() == corpus / "raw"
    assert cfg.get_processed_dir() == corpus / "proc"
    assert cfg.get_metadata_dir() == corpus / "meta"
    assert cfg.get_logs_dir() == corpus / "logs"
    assert cfg.get("environments.test.corpus_root") == str(corpus)
