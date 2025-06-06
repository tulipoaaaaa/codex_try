import os
import shutil
from pathlib import Path
import yaml
from shared_tools.project_config import ProjectConfig

def setup_test_environment():
    """Set up the test environment with all necessary directories and configurations"""
    
    # Load test configuration
    config_path = Path("config/test_config.yaml")
    with open(config_path, 'r') as f:
        test_config = yaml.safe_load(f)
    
    # Create ProjectConfig instance
    config = ProjectConfig.from_dict(test_config)
    
    # Create necessary directories
    directories = [
        config.get_corpus_dir(),
        config.get_cache_dir(),
        config.get_log_dir(),
        Path(config.get_corpus_dir()) / "scidb_test",
        Path(config.get_corpus_dir()) / "arxiv_test",
        Path(config.get_corpus_dir()) / "github_test",
        Path(config.get_corpus_dir()) / "pdf_extractor_test",
        Path(config.get_corpus_dir()) / "nonpdf_extractor_test",
        Path(config.get_corpus_dir()) / "corpus_test",
        Path(config.get_corpus_dir()) / "reports",
        Path(config.get_corpus_dir()) / "backups"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Set up environment variables
    os.environ["TEST_MODE"] = "true"
    os.environ["TEST_DATA_DIR"] = str(config.get_corpus_dir())
    os.environ["TEST_CONFIG"] = str(config_path)
    
    print("\nTest environment setup complete!")
    print("Environment variables set:")
    print(f"  TEST_MODE: {os.environ.get('TEST_MODE')}")
    print(f"  TEST_DATA_DIR: {os.environ.get('TEST_DATA_DIR')}")
    print(f"  TEST_CONFIG: {os.environ.get('TEST_CONFIG')}")

def cleanup_test_environment():
    """Clean up the test environment"""
    
    # Load test configuration
    config_path = Path("config/test_config.yaml")
    with open(config_path, 'r') as f:
        test_config = yaml.safe_load(f)
    
    # Create ProjectConfig instance
    config = ProjectConfig.from_dict(test_config)
    
    # Remove test directories
    test_dirs = [
        config.get_corpus_dir(),
        config.get_cache_dir(),
        config.get_log_dir()
    ]
    
    for directory in test_dirs:
        if Path(directory).exists():
            shutil.rmtree(directory)
            print(f"Removed directory: {directory}")
    
    # Clear environment variables
    for var in ["TEST_MODE", "TEST_DATA_DIR", "TEST_CONFIG"]:
        if var in os.environ:
            del os.environ[var]
    
    print("\nTest environment cleanup complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up or clean up the test environment")
    parser.add_argument("--cleanup", action="store_true", help="Clean up the test environment")
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_environment()
    else:
        setup_test_environment() 