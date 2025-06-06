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

def find_json_files(base_dir):
    for subdir in ['_extracted', 'low_quality']:
        dir_path = Path(base_dir) / subdir
        if dir_path.exists():
            for file in dir_path.glob('*.json'):
                yield file

def check_fields(metadata):
    mapping = {}
    missing = []
    for field in REQUIRED_FIELDS:
        if field in metadata:
            mapping[field] = field
        else:
            # Check common nested locations
            if field == 'quality_flag':
                # Check quality_metrics
                qf = metadata.get('quality_metrics', {}).get('quality_flag')
                if qf is not None:
                    mapping[field] = 'quality_metrics.quality_flag'
                    continue
                # Check quality_metrics.extraction_quality
                qf2 = metadata.get('quality_metrics', {}).get('extraction_quality', {}).get('quality_flag')
                if qf2 is not None:
                    mapping[field] = 'quality_metrics.extraction_quality.quality_flag'
                    continue
            if field == 'token_count':
                tc = metadata.get('quality_metrics', {}).get('token_count')
                if tc is not None:
                    mapping[field] = 'quality_metrics.token_count'
                    continue
                tc2 = metadata.get('quality_metrics', {}).get('extraction_quality', {}).get('token_count')
                if tc2 is not None:
                    mapping[field] = 'quality_metrics.extraction_quality.token_count'
                    continue
            if field == 'language':
                lang = metadata.get('quality_metrics', {}).get('language_confidence', {}).get('language')
                if lang is not None:
                    mapping[field] = 'quality_metrics.language_confidence.language'
                    continue
            missing.append(field)
    return mapping, missing

def main(base_dir):
    report = []
    field_mappings = defaultdict(set)
    for json_file in find_json_files(base_dir):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            mapping, missing = check_fields(metadata)
            report.append({
                'file': str(json_file),
                'missing_fields': missing,
                'field_mapping': mapping
            })
            for k, v in mapping.items():
                field_mappings[k].add(v)
        except Exception as e:
            report.append({
                'file': str(json_file),
                'error': str(e)
            })
    # Output summary
    print("=== Metadata Audit Report ===")
    for entry in report:
        print(f"File: {entry['file']}")
        if 'error' in entry:
            print(f"  ERROR: {entry['error']}")
        else:
            if entry['missing_fields']:
                print(f"  Missing fields: {entry['missing_fields']}")
            print(f"  Field mapping: {entry['field_mapping']}")
    print("\n=== Field Mapping Summary ===")
    for field, locations in field_mappings.items():
        print(f"{field}: {locations}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python metadata_validator.py <corpus_base_dir>")
    else:
        main(sys.argv[1]) 