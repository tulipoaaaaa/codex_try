# generate_targeted_config.py
"""
Generate targeted domain configuration based on gap analysis
"""

import json
import argparse
from pathlib import Path

# Original target allocations
TARGET_ALLOCATIONS = {
    "crypto_derivatives": 0.20,
    "high_frequency_trading": 0.15,
    "market_microstructure": 0.15,
    "risk_management": 0.15,
    "decentralized_finance": 0.12,
    "portfolio_construction": 0.10,
    "valuation_models": 0.08,
    "regulation_compliance": 0.05
}

# Domain search terms
DOMAIN_SEARCH_TERMS = {
    "portfolio_construction": [
        "portfolio optimization cryptocurrency", 
        "asset allocation digital assets",
        "efficient frontier crypto",
        "factor investing blockchain",
        "modern portfolio theory cryptocurrency",
        "mean variance optimization",
        "portfolio constraints crypto",
        "correlation matrix digital assets",
        "risk adjusted returns blockchain",
        "optimal weighing cryptocurrency"
    ],
    "risk_management": [
        "value at risk cryptocurrency", 
        "crypto risk models",
        "risk management blockchain",
        "portfolio hedging digital assets",
        "stress testing crypto",
        "monte carlo simulation blockchain",
        "downside risk cryptocurrency",
        "risk metrics digital assets",
        "volatility forecasting crypto",
        "tail risk blockchain"
    ],
    "regulation_compliance": [
        "cryptocurrency regulation", 
        "crypto compliance framework",
        "digital asset taxation",
        "aml kyc blockchain",
        "securities law cryptocurrency",
        "crypto exchange regulation",
        "defi regulation",
        "cross-border crypto compliance",
        "cryptocurrency legal framework",
        "crypto regulatory reporting"
    ],
    "decentralized_finance": [
        "defi protocol design", 
        "automated market maker mathematics",
        "liquidity pool dynamics",
        "yield farming strategies",
        "lending protocols defi",
        "decentralized exchange mechanisms",
        "defi governance models",
        "stablecoin mechanisms",
        "oracle design blockchain",
        "decentralized derivatives"
    ],
    "valuation_models": [
        "crypto token valuation", 
        "token economic models",
        "on-chain metrics valuation",
        "cryptocurrency dcf model",
        "network value crypto",
        "tokenomics valuation",
        "crypto intrinsic value",
        "digital asset pricing models",
        "cryptocurrency market cap",
        "token value metrics"
    ],
    "high_frequency_trading": [
        "crypto high frequency trading", 
        "algorithmic trading cryptocurrency",
        "low latency crypto infrastructure",
        "market making algorithms blockchain",
        "crypto execution algorithms",
        "hft signal processing",
        "microstructure trading strategies",
        "order book imbalance trading",
        "statistical arbitrage cryptocurrency",
        "high frequency crypto data"
    ],
    "market_microstructure": [
        "crypto market microstructure", 
        "order book dynamics blockchain",
        "liquidity provision cryptocurrency",
        "market impact digital assets",
        "price formation crypto",
        "bid-ask spread blockchain",
        "market maker behavior crypto",
        "price discovery digital assets",
        "transaction cost analysis blockchain",
        "market depth cryptocurrency"
    ],
    "crypto_derivatives": [
        "cryptocurrency derivatives", 
        "bitcoin futures pricing",
        "crypto options greeks",
        "perpetual swap mechanisms",
        "funding rate calculation",
        "basis trading cryptocurrency",
        "crypto derivatives hedging",
        "digital asset futures",
        "options market making crypto",
        "crypto volatility surface"
    ]
}

# Key authors by domain
DOMAIN_KEY_AUTHORS = {
    "portfolio_construction": [
        "Harry Markowitz", "William Sharpe", "Eugene Fama", "Kenneth French", 
        "Richard Grinold", "Ronald Kahn", "Andrew Ang", "Campbell Harvey"
    ],
    "risk_management": [
        "Philippe Jorion", "John Hull", "Carol Alexander", "Nassim Nicholas Taleb",
        "Paul Wilmott", "Emanuel Derman", "Aaron Brown", "Attilio Meucci"
    ],
    "regulation_compliance": [
        "Gary Gensler", "Hester Peirce", "Brian Brooks", "Chris Brummer",
        "Dan Berkovitz", "Timothy Massad", "Jay Clayton", "Christopher Giancarlo"
    ],
    "decentralized_finance": [
        "Vitalik Buterin", "Hayden Adams", "Robert Leshner", "Andre Cronje",
        "Stani Kulechov", "Fernando Martinelli", "Dan Robinson", "Rune Christensen"
    ],
    "valuation_models": [
        "Chris Burniske", "John Pfeffer", "Aswath Damodaran", "Kyle Samani",
        "Willy Woo", "Murad Mahmudov", "Nic Carter", "Pierre Rochard"
    ],
    "high_frequency_trading": [
        "Ernest Chan", "Michael Lewis", "Joel Hasbrouck", "Irene Aldridge",
        "Barry Johnson", "Andrew Pole", "Haim Bodek", "Manoj Narang"
    ],
    "market_microstructure": [
        "Maureen O'Hara", "Albert Menkveld", "Larry Harris", "Terrence Hendershott",
        "Robert Almgren", "Albert Kyle", "Bruno Biais", "Thierry Foucault"
    ],
    "crypto_derivatives": [
        "Carol Alexander", "Antoinette Schoar", "Igor Makarov", "Sam Bankman-Fried",
        "Arthur Hayes", "Su Zhu", "Hsiao-Wei Lee", "Yuval Rooz"
    ]
}

def generate_targeted_config(gap_analysis, output_file):
    """
    Generate targeted domain configuration based on coverage gaps
    
    Args:
        gap_analysis (str): Path to gap analysis JSON file
        output_file (str): Path to output configuration file
    """
    # Load gap analysis
    with open(gap_analysis, 'r') as f:
        analysis = json.load(f)
    
    # Extract coverage gaps
    coverage_gaps = analysis.get('coverage_gaps', {})
    
    # Calculate normalized allocation based on gaps
    total_positive_gap = 0
    positive_gaps = {}
    
    for domain, gap_info in coverage_gaps.items():
        gap = gap_info.get('gap', 0)
        if gap > 0:
            positive_gaps[domain] = gap
            total_positive_gap += gap
    
    # Calculate new allocations (normalize positive gaps)
    new_allocations = {}
    
    if total_positive_gap > 0:
        for domain, gap in positive_gaps.items():
            new_allocations[domain] = gap / total_positive_gap
    else:
        # If no positive gaps, use original allocations
        for domain, allocation in TARGET_ALLOCATIONS.items():
            new_allocations[domain] = allocation
    
    # For domains with negative gaps, set allocation to 0 or very small
    for domain in TARGET_ALLOCATIONS:
        if domain not in new_allocations:
            gap = coverage_gaps.get(domain, {}).get('gap', 0)
            if gap <= -0.05:  # Significantly overrepresented
                new_allocations[domain] = 0
            else:
                new_allocations[domain] = 0.01  # Small token allocation
    
    # Ensure allocations sum to 1
    total_allocation = sum(new_allocations.values())
    normalized_allocations = {domain: alloc/total_allocation for domain, alloc in new_allocations.items()}
    
    # Create domain configuration
    domain_config = {}
    for domain, allocation in normalized_allocations.items():
        domain_config[domain] = {
            "allocation": allocation,
            "search_terms": DOMAIN_SEARCH_TERMS.get(domain, []),
            "key_authors": DOMAIN_KEY_AUTHORS.get(domain, []),
            "min_file_size_mb": 0.5,
            "max_file_size_mb": 25
        }
    
    # Generate Python code for the configuration
    config_code = f"""# targeted_domain_config.py
\"\"\"
Dynamically generated domain configuration based on coverage gaps
Generated from: {gap_analysis}
\"\"\"

TARGETED_DOMAINS = {json.dumps(domain_config, indent=4)}

def get_download_allocation(total_downloads=400):
    \"\"\"Calculate how many downloads to allocate per domain based on percentages\"\"\"
    allocation = {{}}
    
    for domain, config in TARGETED_DOMAINS.items():
        percentage = config["allocation"]
        allocation[domain] = int(total_downloads * percentage)
    
    # Ensure all downloads are allocated by assigning any remainder to first domain
    assigned = sum(allocation.values())
    if assigned < total_downloads:
        active_domains = [d for d, config in TARGETED_DOMAINS.items() if config["allocation"] > 0]
        if active_domains:
            allocation[active_domains[0]] += (total_downloads - assigned)
    
    return allocation
"""
    
    # Save configuration
    with open(output_file, 'w') as f:
        f.write(config_code)
    
    print(f"Generated targeted configuration saved to {output_file}")
    
    # Print allocation summary
    print("\nTargeted Domain Allocation:")
    for domain, allocation in sorted(normalized_allocations.items(), key=lambda x: x[1], reverse=True):
        if allocation > 0:
            print(f"  {domain}: {allocation:.1%}")
    
    # Return the allocations
    return normalized_allocations

def main():
    parser = argparse.ArgumentParser(description='Generate targeted domain configuration')
    parser.add_argument('--gap-analysis', required=True, help='Path to gap analysis JSON file')
    parser.add_argument('--output', required=True, help='Output configuration file path')
    
    args = parser.parse_args()
    
    generate_targeted_config(args.gap_analysis, args.output)

if __name__ == '__main__':
    main()
