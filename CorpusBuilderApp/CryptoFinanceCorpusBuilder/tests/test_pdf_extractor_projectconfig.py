import os
import subprocess
import sys
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
PDF_PROCESSOR = PROJECT_ROOT / 'shared_tools' / 'processors' / 'batch_text_extractor_enhanced_prerefactor.py'
PDF_TEST_CONFIG = PROJECT_ROOT / 'config' / 'project_config_pdf_test.yaml'
PDF_TEST_INPUT = 'G:/ai_trading_dev/data/test_collect/portfolio_construction'
PDF_TEST_OUTPUT = 'G:/ai_trading_dev/data/test_output/pdf_extractor_test'

# Ensure test output directory exists
os.makedirs(PDF_TEST_OUTPUT, exist_ok=True)

def run_pdf_processor_with_project_config():
    cmd = [
        sys.executable,
        str(PDF_PROCESSOR),
        '--project-config', str(PDF_TEST_CONFIG),
        '--verbose'
    ]
    print(f"Running PDF processor with ProjectConfig: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def run_pdf_processor_with_legacy_args():
    cmd = [
        sys.executable,
        str(PDF_PROCESSOR),
        '--input-dir', PDF_TEST_INPUT,
        '--output-dir', PDF_TEST_OUTPUT,
        '--verbose'
    ]
    print(f"Running PDF processor with legacy args: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def verify_output_files():
    # Check if output files exist in the test output directory
    output_files = list(Path(PDF_TEST_OUTPUT).glob('**/*.txt'))
    if not output_files:
        raise AssertionError(f"No output files found in {PDF_TEST_OUTPUT}")
    print(f"Output files found: {len(output_files)}")

if __name__ == '__main__':
    run_pdf_processor_with_project_config()
    run_pdf_processor_with_legacy_args()
    verify_output_files()
    print("PDF processor test completed successfully.") 