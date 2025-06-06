import os
import shutil
from pathlib import Path
import requests
import subprocess
import sys

# Settings
TEST_ROOT = Path('data/test_monitoring/')
DOMAIN = 'test_domain'
DOMAIN_DIR = TEST_ROOT / DOMAIN
EXTRACTED_DIR = TEST_ROOT / f'{DOMAIN}_extracted'
MONITOR_OUT = TEST_ROOT / 'monitoring_test'

VALID_PDF_URL = 'https://arxiv.org/pdf/2106.14834.pdf'  # Public arXiv PDF
VALID_PDF_PATH = DOMAIN_DIR / 'valid.pdf'
CORRUPT_PDF_PATH = DOMAIN_DIR / 'corrupt.pdf'
EMPTY_TXT_PATH = EXTRACTED_DIR / 'empty.txt'

# 1. Setup test folders
for d in [DOMAIN_DIR, EXTRACTED_DIR, MONITOR_OUT]:
    d.mkdir(parents=True, exist_ok=True)

# 2. Download a valid PDF
if not VALID_PDF_PATH.exists():
    print(f'Downloading valid PDF to {VALID_PDF_PATH}...')
    r = requests.get(VALID_PDF_URL)
    with open(VALID_PDF_PATH, 'wb') as f:
        f.write(r.content)
else:
    print(f'Valid PDF already exists at {VALID_PDF_PATH}')

# 3. Create a corrupted PDF (actually a text file with .pdf extension)
with open(CORRUPT_PDF_PATH, 'w') as f:
    f.write('This is not a real PDF file.')
print(f'Corrupted PDF created at {CORRUPT_PDF_PATH}')

# 4. Create an empty .txt file in the extracted folder
with open(EMPTY_TXT_PATH, 'w') as f:
    pass
print(f'Empty .txt file created at {EMPTY_TXT_PATH}')

# 5. (Optional) Run batch extractor if available (skipped for this test)
# You can uncomment and adapt the following if you want to run extraction:
# subprocess.run([sys.executable, 'CryptoFinanceCorpusBuilder/processors/batch_text_extractor.py'])

# 6. Run the monitoring script in report-only mode
print('Running monitoring script...')
subprocess.run([
    sys.executable, 'monitor_progress.py',
    '--corpus-dir', str(TEST_ROOT),
    '--output-dir', str(MONITOR_OUT),
    '--report-only'
])

print('\nTest complete! Check the following for results:')
print(f'- Error log: {MONITOR_OUT / "error_log.json"}')
print(f'- Redownload queue: {MONITOR_OUT / "redownload_queue.json"}')
print(f'- Dashboard: {MONITOR_OUT / "extraction_dashboard.json"}')
print(f'- Report: {MONITOR_OUT}') 