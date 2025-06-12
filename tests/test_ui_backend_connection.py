#!/usr/bin/env python3
"""
Test script to verify UI-backend connection for PDF processing
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project to Python path
project_root = Path(__file__).parent.parent / "CorpusBuilderApp"
sys.path.insert(0, str(project_root))

def test_batch_extractor_class():
    """Test the BatchTextExtractorEnhancedPrerefactor class that the UI uses"""
    print("🔧 Test 1: Testing BatchTextExtractorEnhancedPrerefactor Class")
    print("-" * 50)
    
    try:
        from shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor
        
        # Initialize the class (like the UI does)
        extractor = BatchTextExtractorEnhancedPrerefactor()
        print("✅ BatchTextExtractorEnhancedPrerefactor initialized successfully")
        
        # Test with your PDF file
        pdf_path = r"G:\test_data\10_1111_cyt_12104_pdf -- Dudding, N_ ;Crossley, J_ -- Cytopathology, #5, 24, pages 283-288, 2013 sep 18 -- John Wiley and Sons; Wiley (Blackwell -- 10_1111_cyt_12104 -- 059a0d666db (1 - Copy.pdf"
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Using temp output dir: {temp_dir}")
            
            print("🔧 Testing process_file method...")
            result = extractor.process_file(pdf_path, temp_dir)
            
            if result:
                print(f"✅ process_file successful!")
                print(f"📊 Result keys: {result.keys()}")
                
                # Check if output files were created
                output_files = list(Path(temp_dir).glob("**/*"))
                print(f"📄 Output files created: {len(output_files)}")
                for f in output_files[:5]:  # Show first 5 files
                    print(f"   - {f.name}")
                
                return True
            else:
                print("❌ process_file returned None/empty result")
                return False
                
    except Exception as e:
        print(f"❌ Error testing BatchTextExtractorEnhancedPrerefactor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_directory_processing():
    """Test directory processing (what the UI batch processing uses)"""
    print("\n🔧 Test 2: Testing Directory Processing")
    print("-" * 50)
    
    try:
        from shared_tools.processors.batch_text_extractor_enhanced_prerefactor import BatchTextExtractorEnhancedPrerefactor
        
        extractor = BatchTextExtractorEnhancedPrerefactor()
        
        # Your test data directory
        input_dir = r"G:\test_data"
        
        print(f"📁 Input directory: {input_dir}")
        print(f"📁 Directory exists: {Path(input_dir).exists()}")
        
        if not Path(input_dir).exists():
            print("❌ Input directory not found, skipping directory test")
            return True
        
        # Count PDF files in the directory
        pdf_files = list(Path(input_dir).glob("*.pdf"))
        print(f"📄 Found {len(pdf_files)} PDF files")
        
        # Create a temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Using temp output dir: {temp_dir}")
            
            print("🔧 Testing process_directory method...")
            result = extractor.process_directory(input_dir, temp_dir)
            
            if result:
                print(f"✅ process_directory successful!")
                print(f"📊 Result keys: {result.keys()}")
                print(f"📊 Processed files: {result.get('processed_files', 0)}")
                print(f"📊 Successful files: {result.get('successful_files', 0)}")
                print(f"📊 Failed files: {result.get('failed_files', 0)}")
                
                return True
            else:
                print("❌ process_directory returned None/empty result")
                return False
                
    except Exception as e:
        print(f"❌ Error testing directory processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_wrapper_integration():
    """Test the REAL UI wrapper that processors_tab.py uses"""
    print("\n🔧 Test 3: Testing REAL UI Wrapper Integration")
    print("-" * 50)
    
    try:
        # Import the REAL wrapper that the UI uses
        from shared_tools.ui_wrappers.processors.pdf_extractor_wrapper import PDFExtractorWrapper
        from shared_tools.project_config import ProjectConfig
        print("✅ PDFExtractorWrapper imported successfully")
        
        # Create a basic config for testing
        config = ProjectConfig()
        
        # Try to initialize it (like the UI does)
        wrapper = PDFExtractorWrapper(config)
        print("✅ PDFExtractorWrapper initialized successfully")
        
        # Check if it has the methods that processors_tab.py actually calls
        expected_methods = ['start_batch_processing', 'set_ocr_enabled', 'set_table_extraction', 'set_worker_threads']
        for method in expected_methods:
            if hasattr(wrapper, method):
                print(f"✅ {method} method exists")
            else:
                print(f"❌ {method} method missing")
                return False
        
        # Test that it now uses the enhanced processor
        extractor = wrapper._create_target_object()
        if hasattr(extractor, 'process_file') and hasattr(extractor, 'process_directory'):
            print("✅ Uses enhanced processor with batch capabilities")
        else:
            print("❌ Not using enhanced processor")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing UI wrapper: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all UI-backend connection tests"""
    print("🧪 UI-BACKEND CONNECTION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_batch_extractor_class,
        test_directory_processing,
        test_ui_wrapper_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i}: {test.__name__} - {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - UI-backend connection should work!")
    else:
        print("⚠️  SOME TESTS FAILED - This might explain the UI issue")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 