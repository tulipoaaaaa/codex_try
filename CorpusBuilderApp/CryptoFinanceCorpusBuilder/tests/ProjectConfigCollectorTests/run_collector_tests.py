import os
import sys
import pytest
from pathlib import Path

def main():
    """Run all collector tests using pytest"""
    # Get the directory containing this script
    test_dir = Path(__file__).parent
    
    # Add the project root to Python path
    project_root = test_dir.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Run all tests in the directory
    pytest_args = [
        str(test_dir),  # Directory containing tests
        "-v",           # Verbose output
        "--tb=short",   # Shorter traceback format
        "--capture=no", # Show print statements
        "--durations=10" # Show 10 slowest tests
    ]
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    # Exit with the same code as pytest
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 