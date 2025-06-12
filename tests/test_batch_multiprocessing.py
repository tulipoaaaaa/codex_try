#!/usr/bin/env python3
"""
Test script to verify batch multiprocessing functionality works with Ghostscript integration.
This tests the actual parallel processing of multiple PDFs.
"""
import pytest

pytest.skip("Requires Ghostscript", allow_module_level=True)

import os
import sys
import glob
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import logging
from typing import Dict, Any, List
import json

# Add the project to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import (
    BatchTextExtractorEnhancedPrerefactor,
    run_with_project_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pdf_in_worker(pdf_path: str) -> Dict[str, Any]:
    """Function to run in worker process for PDF text extraction"""
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_text_from_pdf
        text = extract_text_from_pdf(pdf_path)
        return {
            'success': True,
            'chars': len(text) if text else 0,
            'worker_pid': os.getpid(),
            'ghostscript_path': os.environ.get('GHOSTSCRIPT_PATH', 'NOT_SET')
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'worker_pid': os.getpid(),
            'ghostscript_path': os.environ.get('GHOSTSCRIPT_PATH', 'NOT_SET')
        }

def extract_tables_worker(pdf_path: str) -> Dict[str, Any]:
    """Extract tables in worker process"""
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_tables_from_pdf
        start_time = time.time()
        tables = extract_tables_from_pdf(pdf_path, timeout_seconds=30, verbose=False)
        end_time = time.time()
        
        return {
            'success': True,
            'pdf': Path(pdf_path).name,
            'tables_found': len(tables),
            'processing_time': end_time - start_time,
            'worker_pid': os.getpid()
        }
    except Exception as e:
        return {
            'success': False,
            'pdf': Path(pdf_path).name,
            'error': str(e),
            'worker_pid': os.getpid()
        }

def setup_test_environment() -> Path:
    """Set up test environment with temporary directories"""
    temp_dir = Path(tempfile.mkdtemp())
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    return temp_dir

def cleanup_test_environment(temp_dir: Path) -> None:
    """Clean up test environment"""
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

def test_batch_processing():
    """Test batch processing with Ghostscript integration"""
    print("🔄 BATCH MULTIPROCESSING TEST")
    print("=" * 50)
    
    try:
        # Initialize Qt application
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Find available PDFs
        test_pdfs = glob.glob("G:/test_data/*.pdf")
        if not test_pdfs:
            print("❌ No test PDFs found in G:/test_data/")
            return False
        
        # Use first few PDFs (or duplicate if only one)
        pdfs_to_process = test_pdfs[:3] if len(test_pdfs) >= 3 else test_pdfs * 3
        pdfs_to_process = pdfs_to_process[:5]  # Max 5 for testing
        
        print(f"📁 Found {len(test_pdfs)} PDFs, testing with {len(pdfs_to_process)} files")
        for i, pdf in enumerate(pdfs_to_process, 1):
            print(f"   {i}. {Path(pdf).name}")
        
        # Set up output directory on G: drive
        output_dir = Path("G:/processed_output")
        output_dir.mkdir(exist_ok=True)
        
        # Create _extracted subdirectory
        extracted_dir = output_dir / "_extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        print(f"📂 Output directory: {output_dir}")
        
        # Import the wrapper
        from CorpusBuilderApp.shared_tools.ui_wrappers.processors.batch_text_extractor_enhanced_prerefactor_wrapper import BatchTextExtractorEnhancedPrerefactorWrapper
        
        # Initialize the wrapper with default config
        wrapper = BatchTextExtractorEnhancedPrerefactorWrapper(config={})
        
        print(f"🔧 Starting batch processing with multiprocessing...")
        start_time = time.time()
        
        # Run batch processing through the wrapper
        results = wrapper.process_directory("G:/test_data", str(output_dir))
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
        print(f"📊 Results: {results}")
        
        # Check if output files were created in _extracted directory
        output_files = list(extracted_dir.glob("*.txt"))
        json_files = list(extracted_dir.glob("*.json"))
        
        print(f"📄 Output text files: {len(output_files)}")
        print(f"📋 Output JSON files: {len(json_files)}")
        
        # Show the exact output structure
        print("\n📁 Output Structure:")
        print("=" * 50)
        if extracted_dir.exists():
            print(f"\n📂 _extracted/")
            for file in extracted_dir.glob("*"):
                print(f"   {'📄' if file.suffix == '.txt' else '📋'} {file.name}")
        
        if output_files and json_files:
            print("\n✅ Batch processing successful!")
            return True
        else:
            print("\n❌ No output files generated")
            return False
            
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiprocessing_worker_isolation():
    """Test that worker processes properly initialize Ghostscript independently"""
    print("\n👥 MULTIPROCESSING WORKER ISOLATION TEST")
    print("=" * 50)
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import worker_initializer
        
        # Find a test PDF
        test_pdfs = glob.glob("G:/test_data/*.pdf")
        if not test_pdfs:
            print("❌ No test PDFs found")
            return False
        
        test_pdf = test_pdfs[0]
        print(f"📁 Testing with: {Path(test_pdf).name}")
        
        print("🔧 Testing with 3 worker processes...")
        
        # Test with multiple workers
        with ProcessPoolExecutor(max_workers=3, initializer=worker_initializer) as executor:
            # Submit same PDF to multiple workers
            futures = [executor.submit(process_pdf_in_worker, test_pdf) for _ in range(3)]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                status = "✅" if result['success'] else "❌"
                print(f"  {status} Worker PID {result['worker_pid']}: "
                      f"{'SUCCESS' if result['success'] else 'FAILED'}")
                
                if result['success']:
                    print(f"     Characters extracted: {result['chars']}")
                else:
                    print(f"     Error: {result.get('error', 'Unknown')}")
                
                print(f"     Ghostscript path: {result['ghostscript_path']}")
        
        successful_workers = sum(1 for r in results if r['success'])
        print(f"\n📊 Summary: {successful_workers}/{len(results)} workers successful")
        
        if successful_workers == len(results):
            print("✅ All workers successfully initialized Ghostscript!")
            return True
        else:
            print("❌ Some workers failed to initialize properly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing worker isolation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_table_extraction():
    """Test concurrent table extraction (most Ghostscript-intensive operation)"""
    print("\n📊 CONCURRENT TABLE EXTRACTION TEST")
    print("=" * 50)
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import worker_initializer
        
        # Find test PDFs
        test_pdfs = glob.glob("G:/test_data/*.pdf")
        if not test_pdfs:
            print("❌ No test PDFs found")
            return False
        
        # Use up to 3 PDFs
        pdfs_to_test = test_pdfs[:3] if len(test_pdfs) >= 3 else test_pdfs * 3
        pdfs_to_test = pdfs_to_test[:3]
        
        print(f"📁 Testing table extraction on {len(pdfs_to_test)} PDFs concurrently")
        
        print("🔧 Starting concurrent table extraction...")
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=3, initializer=worker_initializer) as executor:
            futures = [executor.submit(extract_tables_worker, pdf) for pdf in pdfs_to_test]
            
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['pdf']} (PID {result['worker_pid']})")
                
                if result['success']:
                    print(f"     Tables found: {result['tables_found']}")
                    print(f"     Time: {result['processing_time']:.2f}s")
                else:
                    print(f"     Error: {result.get('error', 'Unknown')}")
        
        total_time = time.time() - start_time
        successful_extractions = sum(1 for r in results if r['success'])
        
        print(f"\n📊 Summary:")
        print(f"   Total time: {total_time:.2f} seconds")
        print(f"   Successful extractions: {successful_extractions}/{len(results)}")
        
        if successful_extractions == len(results):
            print("✅ Concurrent table extraction successful!")
            return True
        else:
            print("❌ Some table extractions failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in concurrent table extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all multiprocessing tests"""
    print("🧪 MULTIPROCESSING & BATCH FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Batch Processing", test_batch_processing),
        ("Worker Isolation", test_multiprocessing_worker_isolation),
        ("Concurrent Table Extraction", test_concurrent_table_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 MULTIPROCESSING TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for i, (test_name, result) in enumerate(results, 1):
        status = "✅" if result else "❌"
        print(f"Test {i}: {test_name} - {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED")
    else:
        print("\n⚠️  SOME MULTIPROCESSING TESTS FAILED")
        print("   Check the output above for details")

if __name__ == "__main__":
    main() 