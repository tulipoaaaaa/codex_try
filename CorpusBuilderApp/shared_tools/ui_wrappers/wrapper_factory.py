from typing import Type, Union
from shared_tools.project_config import ProjectConfig
from .base_wrapper import BaseWrapper

def create_collector_wrapper(collector_name: str, config: Union[str, ProjectConfig]) -> BaseWrapper:
    """Factory function to create collector wrappers"""
    
    # Import all collector wrappers
    from .collectors.isda_wrapper import ISDAWrapper
    from .collectors.annas_archive_wrapper import AnnasArchiveWrapper
    from .collectors.github_wrapper import GitHubWrapper
    from .collectors.quantopian_wrapper import QuantopianWrapper
    from .collectors.arxiv_wrapper import ArxivWrapper
    from .collectors.fred_wrapper import FREDWrapper
    from .collectors.bitmex_wrapper import BitMEXWrapper
    from .collectors.scidb_wrapper import SciDBWrapper
    from .collectors.web_wrapper import WebWrapper
    
    wrapper_map = {
        "isda": ISDAWrapper,
        "annas_archive": AnnasArchiveWrapper,
        "github": GitHubWrapper,
        "quantopian": QuantopianWrapper,
        "arxiv": ArxivWrapper,
        "fred": FREDWrapper,
        "bitmex": BitMEXWrapper,
        "scidb": SciDBWrapper,
        "web": WebWrapper
    }
    
    if collector_name.lower() not in wrapper_map:
        raise ValueError(f"Unknown collector: {collector_name}")
        
    wrapper_class = wrapper_map[collector_name.lower()]
    return wrapper_class(config)

def create_processor_wrapper(processor_name: str, config: Union[str, ProjectConfig]) -> BaseWrapper:
    """Factory function to create processor wrappers"""
    
    # Import all processor wrappers
    from .processors.pdf_extractor_wrapper import PDFExtractorWrapper
    from .processors.text_extractor_wrapper import TextExtractorWrapper
    from .processors.corpus_balancer_wrapper import CorpusBalancerWrapper
    
    wrapper_map = {
        "pdf": PDFExtractorWrapper,
        "text": TextExtractorWrapper,
        "balancer": CorpusBalancerWrapper
    }
    
    if processor_name.lower() not in wrapper_map:
        raise ValueError(f"Unknown processor: {processor_name}")
        
    wrapper_class = wrapper_map[processor_name.lower()]
    return wrapper_class(config) 