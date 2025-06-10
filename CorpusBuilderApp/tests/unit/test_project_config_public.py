import os
import yaml
from shared_tools.project_config import ProjectConfig
import pytest


def _write_yaml(path, corpus_dir):
    """Write a minimal configuration file matching the current schema."""
    data = {
        "environment": {"active": "test"},
        "environments": {"test": {"corpus_dir": str(corpus_dir)}},
    }
    with open(path, "w") as f:
        yaml.safe_dump(data, f)


def test_from_yaml_and_getters(tmp_path, monkeypatch):
    corpus_root = tmp_path / 'corpus'
    _write_yaml(tmp_path / 'cfg.yaml', corpus_root)
    monkeypatch.setenv('CORPUS_ROOT', str(corpus_root))
    monkeypatch.setenv('RAW_DATA_DIR', str(corpus_root / 'raw'))
    monkeypatch.setenv('PROCESSED_DIR', str(corpus_root / 'processed'))
    monkeypatch.setenv('METADATA_DIR', str(corpus_root / 'metadata'))
    monkeypatch.setenv('LOGS_DIR', str(corpus_root / 'logs'))
    cfg = ProjectConfig.from_yaml(str(tmp_path / 'cfg.yaml'))
    assert cfg.get('environment.active') == 'test'
    assert cfg.get_corpus_root() == corpus_root
    assert cfg.get_corpus_dir() == corpus_root
    assert cfg.get_raw_dir() == corpus_root / 'raw'
    assert cfg.get_processed_dir() == corpus_root / 'processed'
    assert cfg.get_metadata_dir() == corpus_root / 'metadata'
    assert cfg.get_logs_dir() == corpus_root / 'logs'


def test_get_set_and_save(tmp_path, monkeypatch):
    corpus_root = tmp_path / 'corpus'
    cfg_path = tmp_path / 'cfg.yaml'
    _write_yaml(cfg_path, corpus_root)
    monkeypatch.setenv('CORPUS_ROOT', str(corpus_root))
    monkeypatch.setenv('RAW_DATA_DIR', str(corpus_root / 'raw'))
    monkeypatch.setenv('PROCESSED_DIR', str(corpus_root / 'processed'))
    monkeypatch.setenv('METADATA_DIR', str(corpus_root / 'metadata'))
    monkeypatch.setenv('LOGS_DIR', str(corpus_root / 'logs'))
    cfg = ProjectConfig.from_yaml(str(cfg_path))
    cfg.set('api_keys.github_token', 'abc123')
    cfg.save()
    monkeypatch.setenv('GITHUB_TOKEN', 'abc123')
    reloaded = ProjectConfig.from_yaml(str(cfg_path))
    assert reloaded.get('api_keys.github_token') == 'abc123'


def test_revalidate_and_reload(tmp_path, monkeypatch):
    corpus_root = tmp_path / 'corpus'
    cfg_path = tmp_path / 'cfg.yaml'
    _write_yaml(cfg_path, corpus_root)
    monkeypatch.setenv('CORPUS_ROOT', str(corpus_root))

    cfg = ProjectConfig.from_yaml(str(cfg_path))
    cfg.config['domains']['crypto_derivatives']['allocation'] = 'bad'
    with pytest.raises(Exception):
        cfg.revalidate()

    cfg.config['domains']['crypto_derivatives']['allocation'] = 0.3
    cfg.save()
    cfg.config['domains']['crypto_derivatives']['allocation'] = 0.1
    cfg.reload_from_file()
    assert cfg.get('domains.crypto_derivatives.allocation') == 0.3


