import os
import subprocess
import sys
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
NONPDF_PROCESSOR = PROJECT_ROOT / 'shared_tools' / 'processors' / 'batch_nonpdf_extractor_enhanced.py'
NONPDF_TEST_CONFIG = PROJECT_ROOT / 'config' / 'project_config_nonpdf_test.yaml'
NONPDF_TEST_INPUT = 'G:/ai_trading_dev/data/test_collect/test_fourfiles'
NONPDF_TEST_OUTPUT = 'G:/ai_trading_dev/data/test_output/nonpdf_extractor_test'

# Ensure test output directory exists
os.makedirs(NONPDF_TEST_OUTPUT, exist_ok=True)

def run_nonpdf_processor_with_project_config():
    cmd = [
        sys.executable,
        str(NONPDF_PROCESSOR),
        '--project-config', str(NONPDF_TEST_CONFIG)
    ]
    print(f"Running non-PDF processor with ProjectConfig: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def run_nonpdf_processor_with_legacy_args():
    cmd = [
        sys.executable,
        str(NONPDF_PROCESSOR),
        '--input-dir', NONPDF_TEST_INPUT,
        '--output-dir', NONPDF_TEST_OUTPUT
    ]
    print(f"Running non-PDF processor with legacy args: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def verify_output_files():
    # Check if output files exist in the test output directory
    output_files = list(Path(NONPDF_TEST_OUTPUT).glob('**/*.txt'))
    if not output_files:
        raise AssertionError(f"No output files found in {NONPDF_TEST_OUTPUT}")
    print(f"Output files found: {len(output_files)}")

if __name__ == '__main__':
    run_nonpdf_processor_with_project_config()
    run_nonpdf_processor_with_legacy_args()
    verify_output_files()
    print("Non-PDF processor test completed successfully.") 