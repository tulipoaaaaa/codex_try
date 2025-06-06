import os
import csv
import re
import unicodedata
import argparse
from typing import List, Set

def generate_title_cache(corpus_dir: str, output_dir: str) -> None:
    """
    Generate a cache of document titles from the corpus metadata.
    This function scans the corpus directory for metadata files, normalizes titles,
    and writes a cache file of unique titles to the output directory.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all metadata files
    metadata_files = []
    for root, _, files in os.walk(corpus_dir):
        for file in files:
            if file.endswith('_metadata.csv'):
                metadata_files.append(os.path.join(root, file))
    
    if not metadata_files:
        print("No metadata files found.")
        return
    
    # Process each metadata file
    all_titles: Set[str] = set()
    for metadata_file in metadata_files:
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'title' in row and row['title']:
                        # Normalize title
                        title = row['title'].strip()
                        title = unicodedata.normalize('NFKC', title)
                        title = re.sub(r'\s+', ' ', title)
                        all_titles.add(title)
        except Exception as e:
            print(f"Error processing {metadata_file}: {e}")
    
    # Write cache file
    cache_file = os.path.join(output_dir, 'title_cache.txt')
    with open(cache_file, 'w', encoding='utf-8') as f:
        for title in sorted(all_titles):
            f.write(f"{title}\n")
    
    print(f"Title cache generated: {cache_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a cache of document titles from corpus metadata.")
    parser.add_argument("corpus_dir", help="Directory containing the corpus metadata files")
    parser.add_argument("output_dir", help="Directory to write the title cache file")
    args = parser.parse_args()
    generate_title_cache(args.corpus_dir, args.output_dir) 