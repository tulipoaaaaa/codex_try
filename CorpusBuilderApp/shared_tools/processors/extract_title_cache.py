import pandas as pd
import re
import datetime
import os

# Normalization function: lowercase, remove punctuation, trim whitespace
def normalize_title(title):
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()

# Paths
csv_path = os.path.join('data', 'corpus_1', 'corpus_all.csv')
timestamp = datetime.datetime.now().strftime('%Y%m%d')
cache_file = os.path.join('data', f'title_cache_{timestamp}.txt')

# Extract and normalize titles from CSV
df = pd.read_csv(csv_path)
titles = set(normalize_title(title) for title in df['id'] if not pd.isna(title))

# Save to cache file
with open(cache_file, 'w', encoding='utf-8') as f:
    for title in sorted(titles):
        f.write(f"{title}\n")

print(f"Created cache with {len(titles)} unique titles at {cache_file}") 