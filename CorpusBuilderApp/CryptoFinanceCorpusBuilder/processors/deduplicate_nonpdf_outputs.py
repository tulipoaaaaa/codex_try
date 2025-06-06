import os
import json
from pathlib import Path
from datetime import datetime
from CryptoFinanceCorpusBuilder.processors.deduplicator import Deduplicator
import argparse

def get_token_count(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return meta.get('token_count', 0)
    except Exception:
        return 0

def update_metadata(json_path, group_id, deduplication_date, kept_file_path, is_kept, group_type, token_loss):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        meta['deduplicated'] = True
        meta['duplicate_group_id'] = group_id
        meta['deduplication_date'] = deduplication_date
        meta['kept_file'] = is_kept
        meta['is_duplicate_of'] = None if is_kept else str(kept_file_path)
        meta['token_loss'] = token_loss if not is_kept else 0
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Could not update metadata for {json_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Deduplicate non-PDF extracted outputs and update metadata only.")
    parser.add_argument('--corpus-dir', required=True, help='Path to non-PDF output directory (should contain _extracted/ and/or low_quality/)')
    parser.add_argument('--strategy', default='keep_first', choices=['keep_first', 'keep_largest'], help='Deduplication strategy (metadata only)')
    parser.add_argument('--minhash', action='store_true', help='Enable MinHash/LSH near-duplicate detection')
    parser.add_argument('--similarity-threshold', type=float, default=0.8, help='MinHash similarity threshold')
    parser.add_argument('--report', default='deduplication_report.json', help='Path to save deduplication report (JSON)')
    args = parser.parse_args()

    dedup = Deduplicator(
        corpus_dir=args.corpus_dir,
        similarity_threshold=args.similarity_threshold,
        use_minhash=args.minhash
    )
    duplicates = dedup.find_duplicates()
    deduplication_date = datetime.utcnow().isoformat()
    total_token_loss = 0
    total_duplicates = 0
    duplicate_groups = []
    group_id_counter = 1
    for group in duplicates:
        files = group.get('files', [])
        if len(files) <= 1:
            continue
        group_id = f"dg-{group_id_counter:03d}"
        group_id_counter += 1
        # Find all .json metadata files for group members
        file_jsons = []
        for file_path in files:
            p = Path(file_path)
            for subdir in ['_extracted', 'low_quality']:
                meta_path = p.parent.parent / subdir / (p.stem + '.json')
                if meta_path.exists():
                    file_jsons.append((file_path, meta_path))
                    break
        if not file_jsons:
            continue
        # Determine kept file
        if args.strategy == 'keep_first':
            kept_file, kept_json = file_jsons[0]
        elif args.strategy == 'keep_largest':
            kept_file, kept_json = max(file_jsons, key=lambda x: get_token_count(x[1]))
        else:
            kept_file, kept_json = file_jsons[0]
        # Calculate token loss for this group
        kept_tokens = get_token_count(kept_json)
        group_token_loss = 0
        duplicates_list = []
        for file_path, json_path in file_jsons:
            is_kept = (file_path == kept_file)
            file_tokens = get_token_count(json_path)
            loss = 0 if is_kept else file_tokens
            if not is_kept:
                group_token_loss += loss
                duplicates_list.append(file_path)
            update_metadata(json_path, group_id, deduplication_date, kept_file, is_kept, group.get('type'), loss)
        total_token_loss += group_token_loss
        total_duplicates += len(duplicates_list)
        duplicate_groups.append({
            "group_id": group_id,
            "type": group.get('type'),
            "kept_file": kept_file,
            "duplicates": duplicates_list,
            "token_loss": group_token_loss
        })
    report = {
        "deduplication_date": deduplication_date,
        "strategy": args.strategy,
        "total_groups": len(duplicate_groups),
        "total_duplicates": total_duplicates,
        "token_loss": total_token_loss,
        "duplicate_groups": duplicate_groups
    }
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Deduplication complete. Groups: {len(duplicate_groups)}, Duplicates: {total_duplicates}, Token loss: {total_token_loss}")
    print(f"Report saved to {args.report}")

if __name__ == '__main__':
    main() 