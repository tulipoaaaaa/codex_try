import json
from pathlib import Path
import argparse
from collections import defaultdict
import os
import shutil
import csv

def export_corpus(metadata_path, output_path, filter_priority=None, min_tokens=100, min_chars=1000, include_fields=None):
    metadata_path = Path(metadata_path)
    output_path = Path(output_path)
    include_fields = include_fields or []

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    documents = metadata.get("documents", {})
    exported = 0
    tmp_path = output_path.with_suffix('.tmp')

    # Backup if output exists
    if output_path.exists():
        backup_path = output_path.with_suffix('.bak.jsonl')
        shutil.copy2(output_path, backup_path)
        print(f"🗂️  Backed up existing output to {backup_path}")

    with open(tmp_path, 'w', encoding='utf-8') as out:
        for doc_id, doc in documents.items():
            if not doc.get("extracted_text_path"):
                continue
            # Only export if both high priority AND canonical if filter_priority is 'high'
            if filter_priority == 'high':
                if doc.get("priority") != 'high' or not doc.get("canonical"):
                    continue
            elif filter_priority and doc.get("priority") != filter_priority:
                continue
            try:
                text = Path(doc["extracted_text_path"]).read_text(encoding='utf-8')
                if len(text.strip()) < min_chars or len(text.split()) < min_tokens:
                    continue
                export_obj = {
                    "id": doc_id,
                    "domain": doc.get("domain"),
                    "text": text.strip(),
                    "priority": doc.get("priority", "medium"),
                    "source": doc.get("source", "unknown")
                }
                # Add extra fields if requested
                for field in include_fields:
                    if field in doc:
                        export_obj[field] = doc[field]
                out.write(json.dumps(export_obj) + "\n")
                exported += 1
            except Exception as e:
                print(f"[ERROR] Skipped {doc_id}: {e}")
    # Atomic move
    os.replace(tmp_path, output_path)
    print(f"✅ Exported {exported} documents to {output_path}")

def print_token_stats(metadata_path):
    metadata_path = Path(metadata_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    stats = defaultdict(lambda: {"count": 0, "tokens": 0})
    for doc in metadata.get("documents", {}).values():
        domain = doc.get("domain", "unknown")
        priority = doc.get("priority", "medium")
        key = f"{domain} | {priority}"
        stats[key]["count"] += 1
        stats[key]["tokens"] += doc.get("token_count", 0)

    print("\n📊 Token and Document Counts by Domain + Priority:")
    for k, v in sorted(stats.items()):
        print(f"{k:60} | Docs: {v['count']:4} | Tokens: {v['tokens']:,}")

def generate_metadata_audit(metadata_path, report_path):
    metadata_path = Path(metadata_path)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    report = {
        "total_documents": len(metadata.get("documents", {})),
        "priority_distribution": defaultdict(int),
        "source_distribution": defaultdict(int),
        "extracted_only_count": 0,
        "missing_fields_count": 0,
        "flagged": []
    }

    for doc_id, doc in metadata.get("documents", {}).items():
        report["priority_distribution"][doc.get("priority", "medium")] += 1
        report["source_distribution"][doc.get("source", "unknown")] += 1
        if doc.get("extracted_only"):
            report["extracted_only_count"] += 1
        if not doc.get("token_count") or not doc.get("filename"):
            report["missing_fields_count"] += 1
            report["flagged"].append(doc_id)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"🧾 Metadata audit report saved to {report_path}")

def export_high_canonical_to_csv(metadata_path, output_csv):
    metadata_path = Path(metadata_path)
    output_csv = Path(output_csv)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    documents = metadata.get("documents", {})
    high_canonical_keys = [
        "crypto_derivatives_Machine_Learning_for_Asset_Managers",
        "crypto_derivatives_Advances_in_Financial_Machine_Learning_by_López_de_Prado_2018",
        "crypto_derivatives_Option_Volatility_and_Pricing_Advanced_Trading_Strategies_by_Sheldon_Natenberg_2014",
        "crypto_derivatives_Reinforcement_Learning_An_Introduction_by__Richard_S_Sutton_Andrew_G_Barto",
        "market_microstructure_Market_Liquidity_Theory_evidence_Policy_Alisa_Roel_Foucault_Marco_Pagano",
        "market_microstructure_Flow_Toxicity_and_Liquidity_in_a_High_Frequency_World_by_Easley_Lopez_de_Prado_OHara_2012",
        "market_microstructure_Market_Microstructure_Theory_by_Maureen_OHara",
        "market_microstructure_Trading_and_Exchanges_-_Market_Microstructure_for_Practitioners_by_Larry_Harris",
        "market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell",
        "market_microstructure_Models_of_Market_Liquidity-_Applications_to_Traditional_Markets_and_Automated_Market_Makers",
        "market_microstructure_The_LP_Forward_Contract-_Quantifying_liquidity_position_risks_in_decentralized_finance",
        "market_microstructure_Empirical_Market_Microstructure-_The_Institutions_Economics_and_Econometrics_of_Securities_Trading_Joel_Hasbrouck_2007",
        "crypto_derivatives_Order_Flow_and_the_Formation_of_Prices_by_Cont_Kukanov_Stoikov_2014",
        "risk_management_Active_Portfolio_Management_by_Richard_C_Grinold_Ronald_N_Kahn_2nd_edition_2000",
        "decentralized_finance_Machine_Learning_in_Finance_-_From_Theory_to_Practice_by_Matthew_F_Dixon_Igor_Halperin_Paul_A_Bilokon",
        "decentralized_finance_Stochastic_Calculus_for_Finance_II_-_Continuous-Time_Models_by_Steven_E_Shreve_2004"
    ]
    with open(output_csv, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "domain", "priority", "canonical", "text"])
        writer.writeheader()
        for doc_id in high_canonical_keys:
            doc = documents.get(doc_id)
            if not doc or not doc.get("extracted_text_path"):
                print(f"[WARNING] Skipping {doc_id}: missing or no extracted_text_path")
                continue
            try:
                text = Path(doc["extracted_text_path"]).read_text(encoding='utf-8').strip()
            except Exception as e:
                print(f"[ERROR] Skipped {doc_id}: {e}")
                continue
            writer.writerow({
                "id": doc_id,
                "domain": doc.get("domain"),
                "priority": doc.get("priority"),
                "canonical": doc.get("canonical"),
                "text": text
            })
    print(f"✅ Exported {len(high_canonical_keys)} high+canonical docs to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corpus tools: export, stats, audit")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--output', help='Export output .jsonl path')
    parser.add_argument('--filter-priority', help='Optional priority filter (e.g., high). If set to high, only exports docs that are BOTH high priority AND canonical.')
    parser.add_argument('--min-tokens', type=int, default=100, help='Minimum number of tokens for export (default: 100)')
    parser.add_argument('--min-chars', type=int, default=1000, help='Minimum number of characters for export (default: 1000)')
    parser.add_argument('--include-fields', type=str, default='', help='Comma-separated list of extra fields to include (e.g., token_count,filename,extracted_only)')
    parser.add_argument('--stats', action='store_true', help='Print token stats by domain and priority')
    parser.add_argument('--audit', help='Path to save metadata audit report (JSON)')
    parser.add_argument('--export-high-canonical-csv', help='Export all high+canonical docs (from fixed list) to CSV, no token/char limits')
    args = parser.parse_args()

    include_fields = [f.strip() for f in args.include_fields.split(',') if f.strip()] if args.include_fields else []

    if args.output:
        export_corpus(args.metadata, args.output, args.filter_priority, args.min_tokens, args.min_chars, include_fields)
    if args.stats:
        print_token_stats(args.metadata)
    if args.audit:
        generate_metadata_audit(args.metadata, args.audit)
    if args.export_high_canonical_csv:
        export_high_canonical_to_csv(args.metadata, args.export_high_canonical_csv) 