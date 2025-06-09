# File: scripts/clean_pycache_and_stubs.py

import os
import shutil

IGNORED_DIRS = {'.git', '.venv', '__pypackages__'}


def delete_pycache(base_dir):
    """Recursively delete all __pycache__ folders."""
    print("🔍 Searching for __pycache__ folders...")
    for root, dirs, files in os.walk(base_dir):
        if any(part in IGNORED_DIRS for part in root.split(os.sep)):
            continue
        for dirname in dirs:
            if dirname == '__pycache__':
                pycache_path = os.path.join(root, dirname)
                print(f"🧹 Deleting: {pycache_path}")
                shutil.rmtree(pycache_path, ignore_errors=True)


def report_stub_collisions():
    """Warn about any 'PDFExtractorWrapper' or 'TextExtractorWrapper' test stubs"""
    print("\n🔎 Checking for shadowed class stubs...")
    for root, _, files in os.walk('.'):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        if 'class PDFExtractorWrapper' in content or 'class TextExtractorWrapper' in content:
                            if 'def __init__(' not in content:
                                print(f"⚠️  Possible stub class in: {path}")
                except Exception:
                    continue


if __name__ == '__main__':
    print("🚀 Running cleanup script...")
    delete_pycache(".")
    report_stub_collisions()
    print("✅ Done.")
