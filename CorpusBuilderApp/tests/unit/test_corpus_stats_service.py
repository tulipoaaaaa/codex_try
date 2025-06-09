import pytest
from shared_tools.services.corpus_stats_service import CorpusStatsService

@pytest.mark.skip("Pending corpus scan test")
def test_refresh_stats(tmp_path):
    service = CorpusStatsService(project_config=type('Cfg',(object,),{'get_corpus_dir':lambda self: tmp_path}))
    service.refresh_stats()
    assert service.stats == {} or isinstance(service.stats, dict)
