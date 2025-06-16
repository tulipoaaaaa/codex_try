import json, os
from pathlib import Path
from shared_tools.storage.corpus_manager import CorpusManager

base = Path(r'G:\codex\codex_try\corpus_1\processed\_extracted')
cm   = CorpusManager()

buckets = {}
for meta_file in base.glob('*.json'):
    try:
        meta      = json.loads(meta_file.read_text())
        domain    = (meta.get('domain') or 'unknown').lower()
        buckets.setdefault(domain, []).append(meta_file)
        buckets[domain].append(meta_file.with_suffix('.txt'))
    except Exception as e:
        print(f"⚠️  skip {meta_file}: {e}")

for domain, files in buckets.items():
    target = base.parent / domain            # processed\<domain>
    cm.move_files(files, target, overwrite=False, rename_conflicts=False)

# Optional: delete now-empty _extracted
try:
    base.rmdir()
except OSError:
    print("_extracted not empty (some low_quality files?) – leave it.")