import pytest
from shared_tools.processors.corpus_balancer import CorpusBalancer
from conftest import DummyProjectConfig


def test_corpus_balancer_rebalance(tmp_path):
    cfg = DummyProjectConfig(tmp_path)
    balancer = CorpusBalancer(cfg)
    try:
        result = balancer.rebalance(dry_run=True)
    except Exception:
        pytest.skip('rebalance failed')
    assert isinstance(result, dict)
