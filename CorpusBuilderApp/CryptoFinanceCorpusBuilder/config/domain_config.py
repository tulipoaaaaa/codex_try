"""
CONFIGURATION FILE: EXTRACTOR DOMAIN CONFIGURATION
Purpose: Defines domain classifications and source mappings for extractors
Used by: PDF and Non-PDF extractors, domain classifier
Not used by: Corpus balancer (uses balancer_config.py instead)

This file contains:
1. DOMAINS: Domain definitions with allocations and search terms
2. SOURCES: Source-specific configurations and domain mappings

IMPORTANT: This file is used by extractors through domain_utils.py
DO NOT modify without updating domain_utils.py wrapper
"""

# config/domain_config.py

DOMAINS = {'crypto_derivatives': {'allocation': 0.2,
                        'min_documents': 100,
                        'priority': 'high',
                        'quality_threshold': 0.8,
                        'search_terms': ['cryptocurrency derivatives',
                                         'bitcoin futures',
                                         'crypto options',
                                         'perpetual swap',
                                         'funding rate',
                                         'basis trading',
                                         'crypto derivatives pricing'],
                        'target_weight': 0.2},
 'decentralized_finance': {'allocation': 0.12,
                           'min_documents': 70,
                           'priority': 'medium',
                           'quality_threshold': 0.75,
                           'search_terms': ['defi protocols',
                                            'automated market maker design',
                                            'yield optimization strategies',
                                            'liquidity mining'],
                           'target_weight': 0.12},
 'high_frequency_trading': {'allocation': 0.15,
                            'min_documents': 80,
                            'priority': 'high',
                            'quality_threshold': 0.85,
                            'search_terms': ['high frequency trading cryptocurrency',
                                             'algorithmic crypto trading',
                                             'low latency trading blockchain',
                                             'market making algorithms crypto'],
                            'target_weight': 0.15},
 'market_microstructure': {'allocation': 0.15,
                           'min_documents': 60,
                           'priority': 'medium',
                           'quality_threshold': 0.75,
                           'search_terms': ['crypto market microstructure',
                                            'order book dynamics',
                                            'liquidity provision blockchain',
                                            'market impact crypto'],
                           'target_weight': 0.15},
 'portfolio_construction': {'allocation': 0.1,
                            'min_documents': 50,
                            'priority': 'medium',
                            'quality_threshold': 0.75,
                            'search_terms': ['crypto portfolio construction',
                                             'bitcoin asset allocation',
                                             'digital asset correlation',
                                             'crypto diversification'],
                            'target_weight': 0.1},
 'regulation_compliance': {'allocation': 0.05,
                           'min_documents': 30,
                           'priority': 'medium',
                           'quality_threshold': 0.9,
                           'search_terms': ['cryptocurrency regulation',
                                            'crypto compliance framework',
                                            'digital asset taxation',
                                            'crypto KYC AML'],
                           'target_weight': 0.05},
 'risk_management': {'allocation': 0.15,
                     'min_documents': 90,
                     'priority': 'high',
                     'quality_threshold': 0.8,
                     'search_terms': ['cryptocurrency risk models',
                                      'crypto portfolio hedging',
                                      'defi risk management',
                                      'crypto VaR'],
                     'target_weight': 0.15},
 'valuation_models': {'allocation': 0.08,
                      'min_documents': 40,
                      'priority': 'low',
                      'quality_threshold': 0.7,
                      'search_terms': ['token valuation models',
                                       'cryptocurrency fundamental analysis',
                                       'on-chain metrics valuation',
                                       'crypto DCF'],
                      'target_weight': 0.08}}


# (SOURCES section unchanged)
SOURCES = {
    "arxiv": {
        "source_type": "api",
        "base_url": "http://export.arxiv.org/api/query",
        "categories": ["q-fin"],
        "domain_mapping": {
            "crypto_derivatives": ["crypto derivatives", "bitcoin futures", "options pricing"],
            "high_frequency_trading": ["high frequency trading", "algorithmic trading", "market making"],
            "market_microstructure": ["market microstructure", "order book", "liquidity"],
            "risk_management": ["risk management", "portfolio risk", "VaR", "hedging"],
            "decentralized_finance": ["decentralized finance", "defi"],
            "portfolio_construction": ["portfolio construction", "asset allocation"],
            "valuation_models": ["valuation models", "pricing model"],
            "regulation_compliance": ["regulation", "compliance", "tax"]
        }
    },
    "github": {
        "source_type": "repository",
        "topics": ["cryptocurrency-trading", "crypto-trading-bot", "algorithmic-trading",
                   "trading-strategies", "high-frequency-trading", "market-making"],
        "domain_mapping": {
            "high_frequency_trading": ["high-frequency-trading", "algo-trading", "market-making"],
            "crypto_derivatives": ["crypto-derivatives", "perpetual-swap", "futures-trading"],
            "market_microstructure": ["order-book", "market-microstructure"],
            "decentralized_finance": ["defi", "amm", "yield-farming"]
        }
    },
    "foss_trading": {
        "source_type": "web",
        "base_url": "https://fosstrading.com",
        "file_types": [".pdf", ".R", ".md"],
        "domain": "market_microstructure"
    },
    "cme_group": {
        "source_type": "web",
        "base_url": "https://www.cmegroup.com/education",
        "file_types": [".pdf"],
        "domain": "market_microstructure"
    },
    "fred": {
        "source_type": "api",
        "base_url": "https://api.stlouisfed.org/fred",
        "domain_mapping": {
            "market_microstructure": ["liquidity", "market depth", "trading volume"],
            "risk_management": ["volatility", "VIX", "risk"]
        }
    },
    "quantopian": {
        "source_type": "repository",
        "url": "https://github.com/quantopian/research_public",
        "domain": "high_frequency_trading"
    },
    "quantconnect": {
        "source_type": "web",
        "base_url": "https://www.quantconnect.com/tutorials",
        "file_types": [".py", ".ipynb", ".cs"],
        "domain": "high_frequency_trading"
    },
    "isda": {
        "source_type": "web",
        "base_url": "https://www.isda.org/category/documentation",
        "file_types": [".pdf"],
        "domain": "derivatives"
    },
    "occ": {
        "source_type": "web",
        "base_url": "https://www.theocc.com/Clearance-and-Settlement/Clearing",
        "file_types": [".pdf"],
        "domain": "derivatives"
    },
    "bitmex_research": {
        "source_type": "web",
        "base_url": "https://blog.bitmex.com/research",
        "file_types": [".pdf", ".html"],
        "domain": "derivatives"
    },
    "nber": {
        "source_type": "web",
        "base_url": "https://www.nber.org/papers?page=1&perPage=50&q=high+frequency+trading",
        "file_types": [".pdf"],
        "domain": "high_frequency_trading"
    },
    "virtu": {
        "source_type": "web",
        "base_url": "https://www.virtu.com/insights",
        "file_types": [".pdf"],
        "domain": "high_frequency_trading"
    },
    "ofr": {
        "source_type": "web",
        "base_url": "https://www.financialresearch.gov/working-papers",
        "file_types": [".pdf"],
        "domain": "risk_management"
    },
    "bis": {
        "source_type": "web",
        "base_url": "https://www.bis.org/list/research",
        "file_types": [".pdf"],
        "domain": "risk_management"
    },
    "crypto_research_report": {
        "source_type": "web",
        "base_url": "https://cryptoresearch.report",
        "file_types": [".pdf", ".html"],
        "domain": "macroeconomics"
    },
    "stlouisfed": {
        "source_type": "web",
        "base_url": "https://research.stlouisfed.org",
        "search_terms": ["cryptocurrency", "bitcoin", "blockchain"],
        "file_types": [".pdf"],
        "domain": "macroeconomics"
    },
    "imf": {
        "source_type": "web",
        "base_url": "https://www.imf.org/en/Publications/fintech-notes",
        "file_types": [".pdf"],
        "domain": "macroeconomics"
    }
}