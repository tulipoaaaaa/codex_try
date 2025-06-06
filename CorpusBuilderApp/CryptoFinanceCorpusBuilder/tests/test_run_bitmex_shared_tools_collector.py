from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_bitmex import run_bitmex_collector
import shutil
import os
from pathlib import Path

class Args:
    bitmex_clear_output_dir = True
    bitmex_keywords = None  # Collect all posts
    bitmex_max_pages = 10  # Increase if you want more pages
    existing_titles = None

if __name__ == "__main__":
    args = Args()
    source_config = None
    base_dir = "data/tests/bitmex_shared_tools_run"
    # Ensure a clean output directory
    output_dir = Path(base_dir) / "bitmex_research"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")
    run_bitmex_collector(args, source_config, base_dir) 