import json
from pathlib import Path
import shutil
import time

HIGH_PRIORITY_KEYS = [
    "crypto_derivatives_Advances_in_Financial_Machine_Learning_by_López_de_Prado_2018",
    "crypto_derivatives_Machine_learning_for_asset_managers_by__Marcos_M_López_de_Prado",
    "market_microstructure_Empirical_Market_Microstructure-_The_Institutions_Economics_and_Econometrics_of_Securities_Trading_Joel_Hasbrouck_2007",
    "market_microstructure_Flow_Toxicity_and_Liquidity_in_a_High_Frequency_World_by_Easley_Lopez_de_Prado_OHara_2012",
    "crypto_derivatives_Order_Flow_and_the_Formation_of_Prices_by_Cont_Kukanov_Stoikov_2014",
    "crypto_derivatives_Reinforcement_Learning_An_Introduction_by__Richard_S_Sutton_Andrew_G_Barto",
    "market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell",
    "market_microstructure_Trading_and_Exchanges_-_Market_Microstructure_for_Practitioners_by_Larry_Harris",
    "decentralized_finance_Stochastic_Calculus_for_Finance_II_-_Continuous-Time_Models_by_Steven_E_Shreve_2004",
    "decentralized_finance_Machine_Learning_in_Finance_-_From_Theory_to_Practice_by_Matthew_F_Dixon_Igor_Halperin_Paul_A_Bilokon",
    "market_microstructure_Market_Microstructure_Theory_by_Maureen_OHara",
    "market_microstructure_Models_of_Market_Liquidity-_Applications_to_Traditional_Markets_and_Automated_Market_Makers",
    "crypto_derivatives_Option_Volatility_and_Pricing_Advanced_Trading_Strategies_by_Sheldon_Natenberg_2014",
    "risk_management_Active_Portfolio_Management_by_Richard_C_Grinold_Ronald_N_Kahn_2nd_edition_2000",
    "market_microstructure_The_LP_Forward_Contract-_Quantifying_liquidity_position_risks_in_decentralized_finance",
    "market_microstructure_Market_Liquidity_Theory_evidence_Policy_Alisa_Roel_Foucault_Marco_Pagano"
]

def tag_high_priority_and_canonical(metadata_path, dry_run=False):
    metadata_path = Path(metadata_path)
    # Backup
    if not dry_run:
        backup_path = metadata_path.with_suffix('.json.bak')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path_ts = metadata_path.with_name(f"{metadata_path.stem}_{timestamp}.bak")
        shutil.copy2(metadata_path, backup_path)
        shutil.copy2(metadata_path, backup_path_ts)
        print(f"🗂️  Backed up metadata to {backup_path} and {backup_path_ts}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    documents = metadata.get("documents", {})
    tagged = 0
    canonical_tagged = 0
    # First, tag all HIGH_PRIORITY_KEYS as high
    for key in HIGH_PRIORITY_KEYS:
        if key in documents:
            if documents[key].get("priority") != "high":
                tagged += 1
            if not dry_run:
                documents[key]["priority"] = "high"
        else:
            print(f"[WARN] Key not found: {key}")
    # Now, tag every high-priority doc as canonical
    for doc_id, doc in documents.items():
        if doc.get("priority") == "high" and not doc.get("canonical"):
            if not dry_run:
                doc["canonical"] = True
            canonical_tagged += 1
    if not dry_run:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"✅ Tagged {tagged} documents as high priority (from list).")
        print(f"🏷️  Tagged {canonical_tagged} documents as canonical (all high-priority).")
    else:
        print(f"[DRY RUN] Would tag {tagged} documents as high priority (from list).")
        print(f"[DRY RUN] Would tag {canonical_tagged} documents as canonical (all high-priority).")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tag a list of document keys as high priority and tag all high-priority docs as canonical in corpus metadata.")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to file')
    args = parser.parse_args()
    tag_high_priority_and_canonical(args.metadata, dry_run=args.dry_run)

if __name__ == "__main__":
    main() 