import json
from pathlib import Path

# Define missing domains
missing_domains = [
    "portfolio_construction",
    "valuation_models", 
    "regulation_compliance"
]

# Secondary priority domains
medium_priority_domains = [
    "risk_management",
    "decentralized_finance",
    "high_frequency_trading"
]

# Define high-quality books per domain
domain_books = {
    "portfolio_construction": [
        {"title": "Modern Portfolio Theory and Investment Analysis", "author": "Edwin J. Elton, Martin J. Gruber", "domain": "portfolio_construction", "format": "pdf"},
        {"title": "Portfolio Selection: Efficient Diversification of Investments", "author": "Harry Markowitz", "domain": "portfolio_construction", "format": "pdf"},
        {"title": "Active Portfolio Management", "author": "Richard C. Grinold, Ronald N. Kahn", "domain": "portfolio_construction", "format": "pdf"},
        {"title": "Cryptocurrency Portfolio Management", "author": "", "domain": "portfolio_construction", "format": "pdf"},
        {"title": "The Intelligent Asset Allocator", "author": "William Bernstein", "domain": "portfolio_construction", "format": "pdf"}
    ],
    "valuation_models": [
        {"title": "Valuation: Measuring and Managing the Value of Companies", "author": "McKinsey & Company", "domain": "valuation_models", "format": "pdf"},
        {"title": "Cryptoassets: The Innovative Investor's Guide", "author": "Chris Burniske, Jack Tatar", "domain": "valuation_models", "format": "pdf"},
        {"title": "Investment Valuation: Tools and Techniques", "author": "Aswath Damodaran", "domain": "valuation_models", "format": "pdf"},
        {"title": "Token Economy", "author": "Shermin Voshmgir", "domain": "valuation_models", "format": "pdf"},
        {"title": "Financial Modeling and Valuation", "author": "Paul Pignataro", "domain": "valuation_models", "format": "pdf"}
    ],
    "regulation_compliance": [
        {"title": "Blockchain Regulation and Governance in Europe", "author": "Michèle Finck", "domain": "regulation_compliance", "format": "pdf"},
        {"title": "The Law of Bitcoin", "author": "Jerry Brito", "domain": "regulation_compliance", "format": "pdf"},
        {"title": "Cryptocurrency Compliance", "author": "", "domain": "regulation_compliance", "format": "pdf"},
        {"title": "Blockchain and the Law", "author": "Primavera De Filippi, Aaron Wright", "domain": "regulation_compliance", "format": "pdf"},
        {"title": "Cryptocurrency Taxation", "author": "", "domain": "regulation_compliance", "format": "pdf"}
    ],
    "risk_management": [
        {"title": "Financial Risk Management for Cryptocurrency", "author": "", "domain": "risk_management", "format": "pdf"},
        {"title": "Risk Management and Financial Institutions", "author": "John C. Hull", "domain": "risk_management", "format": "pdf"},
        {"title": "Value at Risk", "author": "Philippe Jorion", "domain": "risk_management", "format": "pdf"}
    ],
    "decentralized_finance": [
        {"title": "How to DeFi", "author": "Coingecko", "domain": "decentralized_finance", "format": "pdf"},
        {"title": "DeFi and the Future of Finance", "author": "Campbell R. Harvey", "domain": "decentralized_finance", "format": "pdf"},
        {"title": "Decentralized Finance (DeFi): The Innovative Investor's Guide", "author": "", "domain": "decentralized_finance", "format": "pdf"}
    ],
    "high_frequency_trading": [
        {"title": "High-Frequency Trading", "author": "Irene Aldridge", "domain": "high_frequency_trading", "format": "pdf"},
        {"title": "Algorithmic and High-Frequency Trading", "author": "Álvaro Cartea", "domain": "high_frequency_trading", "format": "pdf"}
    ]
}

# Create download list prioritizing missing domains
download_list = []

# First add all high-priority (missing) domains
for domain in missing_domains:
    if domain in domain_books:
        download_list.extend(domain_books[domain])

# Then add medium-priority domains
for domain in medium_priority_domains:
    if domain in domain_books:
        download_list.extend(domain_books[domain])

# Save to configs/crypto_finance_list.json
output_path = Path("./configs/crypto_finance_list.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(download_list, f, indent=2)

print(f"Created download list with {len(download_list)} books")
print(f"Prioritizing missing domains: {', '.join(missing_domains)}")
print(f"Secondary priority: {', '.join(medium_priority_domains)}")
print(f"Download list saved to {output_path}") 