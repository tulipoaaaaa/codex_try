import os
import json
from pathlib import Path
from collections import defaultdict

REQUIRED_FIELDS = [
    'domain',
    'file_type',
    'quality_flag',
    'token_count',
    'extraction_date',
    'language'
]

DEFAULTS = {
    'domain': 'unknown',
    'file_type': 'unknown',
    'quality_flag': 'unknown',
    'token_count': 0,
    'extraction_date': None,
    'language': 'unknown'
}

def find_json_files(base_dir):
    for subdir in ['_extracted', 'low_quality']:
        dir_path = Path(base_dir) / subdir
        if dir_path.exists():
            for file in dir_path.glob('*.json'):
                yield file

def extract_field(metadata, field):
    # Try top-level
    if field in metadata:
        return metadata[field]
    # Try known nested locations
    if field == 'quality_flag':
        qf = metadata.get('quality_metrics', {}).get('quality_flag')
        if qf is not None:
            return qf
        qf2 = metadata.get('quality_metrics', {}).get('extraction_quality', {}).get('quality_flag')
        if qf2 is not None:
            return qf2
    if field == 'token_count':
        tc = metadata.get('quality_metrics', {}).get('token_count')
        if tc is not None:
            return tc
        tc2 = metadata.get('quality_metrics', {}).get('extraction_quality', {}).get('token_count')
        if tc2 is not None:
            return tc2
    if field == 'language':
        lang = metadata.get('quality_metrics', {}).get('language_confidence', {}).get('language')
        if lang is not None:
            return lang
    return DEFAULTS[field]

def normalize_metadata_file(json_file, backup=True):
    with open(json_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    changed = False
    for field in REQUIRED_FIELDS:
        value = extract_field(metadata, field)
        if metadata.get(field) != value:
            metadata[field] = value
            changed = True
    if changed:
        if backup:
            backup_path = json_file.with_suffix(json_file.suffix + '.bak')
            os.rename(json_file, backup_path)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Normalized: {json_file}")
    else:
        print(f"No changes: {json_file}")

def main(base_dir):
    for json_file in find_json_files(base_dir):
        try:
            normalize_metadata_file(json_file)
        except Exception as e:
            print(f"ERROR processing {json_file}: {e}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python metadata_normalizer.py <corpus_base_dir>")
    else:
        main(sys.argv[1])