# domain_config.py
# Configuration of domains for the crypto-finance corpus

DOMAINS = {
    "crypto_derivatives": {
        "allocation": 0.20,
        "search_terms": [
            "cryptocurrency derivatives", "bitcoin futures", "crypto options",
            "perpetual swap", "funding rate", "basis trading", "crypto derivatives pricing"
        ],
        "key_authors": ["Carol Alexander", "Antoinette Schoar", "Igor Makarov"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 25
    },
    "high_frequency_trading": {
        "allocation": 0.15,
        "search_terms": [
            "high frequency trading cryptocurrency", "algorithmic crypto trading",
            "low latency trading blockchain", "market making algorithms crypto"
        ],
        "key_authors": ["Ernest Chan", "Paraskevi Katsiampa", "Nikolaos Kyriazis"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "market_microstructure": {
        "allocation": 0.15,
        "search_terms": [
            "crypto market microstructure", "order book dynamics",
            "liquidity provision blockchain", "market impact crypto"
        ],
        "key_authors": ["Robert Almgren", "Terrence Hendershott", "Albert Menkveld"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "risk_management": {
        "allocation": 0.15,
        "search_terms": [
            "cryptocurrency risk models", "crypto portfolio hedging",
            "defi risk management", "crypto VaR"
        ],
        "key_authors": ["Philip Jorion", "John Hull", "René Stulz"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "decentralized_finance": {
        "allocation": 0.12,
        "search_terms": [
            "defi protocols", "automated market maker design",
            "yield optimization strategies", "liquidity mining"
        ],
        "key_authors": ["Vitalik Buterin", "Hayden Adams", "Robert Leshner"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "portfolio_construction": {
        "allocation": 0.10,
        "search_terms": [
            "crypto portfolio construction", "bitcoin asset allocation",
            "digital asset correlation", "crypto diversification"
        ],
        "key_authors": ["Harry Markowitz", "Andrew Ang", "Campbell Harvey"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "valuation_models": {
        "allocation": 0.08,
        "search_terms": [
            "token valuation models", "cryptocurrency fundamental analysis",
            "on-chain metrics valuation", "crypto DCF"
        ],
        "key_authors": ["Chris Burniske", "John Pfeffer", "Aswath Damodaran"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    },
    "regulation_compliance": {
        "allocation": 0.05,
        "search_terms": [
            "cryptocurrency regulation", "crypto compliance framework",
            "digital asset taxation", "crypto KYC AML"
        ],
        "key_authors": ["Gary Gensler", "Hester Peirce", "Brian Brooks"],
        "min_file_size_mb": 0.5,
        "max_file_size_mb": 20
    }
}

def get_download_allocation(total_downloads=1200):
    """Calculate how many downloads to allocate per domain based on percentages"""
    allocation = {}
    
    for domain, config in DOMAINS.items():
        percentage = config["allocation"]
        allocation[domain] = int(total_downloads * percentage)
    
    # Ensure all downloads are allocated by assigning any remainder to first domain
    assigned = sum(allocation.values())
    if assigned < total_downloads:
        first_domain = next(iter(allocation))
        allocation[first_domain] += (total_downloads - assigned)
    
    return allocation