import os
import re
import sys
from pathlib import Path
from datetime import datetime
import glob
import json

def normalize_title(title):
    return re.sub(r'[^\w\s]', '', title.lower()).strip()

def main(corpus_dir, output_dir):
    meta_files = glob.glob(os.path.join(corpus_dir, '**', '*.meta'), recursive=True)
    titles = set()
    for meta_path in meta_files:
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            title = meta.get('title')
            if title:
                titles.add(normalize_title(title))
        except Exception as e:
            print(f"[WARN] Could not process {meta_path}: {e}")
    date_str = datetime.now().strftime('%Y%m%d')
    output_file = Path(output_dir) / f'existing_titles_{date_str}.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for t in sorted(titles):
            f.write(t + '\n')
    print(f"Extracted {len(titles)} normalized titles to {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generate_title_cache.py <corpus_dir> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2]) 