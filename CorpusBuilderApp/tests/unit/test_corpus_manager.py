import pytest
from CryptoFinanceCorpusBuilder.shared_tools.storage.corpus_manager import CorpusManager

@pytest.mark.skip("Audit stub – implement later")
def test_add_document_with_sample_metadata(tmp_path):
    """Ensure documents are added and metadata updated."""
    # TODO: create sample text/PDF file under tmp_path
    # TODO: initialize CorpusManager pointing to tmp_path
    # TODO: call add_document and assert metadata file updated
    pass

@pytest.mark.skip("Audit stub – implement later")
def test_get_corpus_stats_empty(tmp_path):
    """Verify stats structure when corpus is empty."""
    # TODO: initialize CorpusManager with empty dirs
    # TODO: call get_corpus_stats and compare to expected defaults
    pass
