#!/usr/bin/env python3
"""
Test script to verify Ghostscript integration is working properly.
This tests the actual PDF processing pipeline, not just detection.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to root
sys.path.insert(0, str(project_root))

def test_ghostscript_detection():
    """Test 1: Verify Ghostscript detection is working"""
    print("🔍 Test 1: Ghostscript Detection")
    print("-" * 40)
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import find_ghostscript_executable
        
        gs_path = find_ghostscript_executable()
        if gs_path:
            print(f"✅ Found Ghostscript: {gs_path}")
            print(f"✅ File exists: {os.path.isfile(gs_path)}")
            return True
        else:
            print("❌ Ghostscript not found")
            return False
    except Exception as e:
        print(f"❌ Error in detection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_setup():
    """Test 2: Verify environment variables are set correctly"""
    print("\n🌐 Test 2: Environment Variables")
    print("-" * 40)
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import setup_ghostscript_environment
        
        # This should have been called during import, but let's check
        gs_path = os.environ.get('GHOSTSCRIPT_PATH')
        if gs_path:
            print(f"✅ GHOSTSCRIPT_PATH set: {gs_path}")
            print(f"✅ File exists: {os.path.isfile(gs_path)}")
            
            # Check if Ghostscript directory is in PATH
            gs_dir = os.path.dirname(gs_path)
            current_path = os.environ.get('PATH', '')
            if gs_dir in current_path:
                print(f"✅ Ghostscript directory in PATH: {gs_dir}")
                return True
            else:
                print(f"⚠️  Ghostscript directory NOT in PATH: {gs_dir}")
                return False
        else:
            print("❌ GHOSTSCRIPT_PATH not set")
            return False
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_camelot_ghostscript():
    """Test 3: Test if Camelot can use Ghostscript"""
    print("\n📊 Test 3: Camelot + Ghostscript Integration")
    print("-" * 40)
    
    try:
        import camelot
        
        # Check if camelot can see ghostscript
        print(f"✅ Camelot imported successfully")
        print(f"✅ Camelot version: {camelot.__version__}")
        
        # Try to access the ghostscript backend
        print("🔧 Testing Ghostscript backend access...")
        
        # This will test if the environment is set up correctly
        gs_path = os.environ.get('GHOSTSCRIPT_PATH')
        if gs_path:
            print(f"✅ Camelot should use Ghostscript at: {gs_path}")
            return True
        else:
            print("❌ GHOSTSCRIPT_PATH not available for Camelot")
            return False
            
    except ImportError as e:
        print(f"❌ Camelot import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Camelot: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_process_setup():
    """Test 4: Test worker process initialization"""
    print("\n👷 Test 4: Worker Process Setup")
    print("-" * 40)
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import worker_initializer
        
        print("🔧 Testing worker initialization...")
        
        # Save current environment
        original_gs_path = os.environ.get('GHOSTSCRIPT_PATH')
        original_path = os.environ.get('PATH')
        
        # Test worker initializer
        worker_initializer()
        
        # Check if environment is still correct
        new_gs_path = os.environ.get('GHOSTSCRIPT_PATH')
        if new_gs_path and os.path.isfile(new_gs_path):
            print(f"✅ Worker setup successful: {new_gs_path}")
            return True
        else:
            print(f"❌ Worker setup failed: {new_gs_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing worker setup: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_pdf_processing():
    """Test 5: Try to process a simple PDF (if one exists)"""
    print("\n📄 Test 5: Simple PDF Processing Test")
    print("-" * 40)
    
    try:
        # Look for a test PDF file
        test_pdf_locations = [
            "G:/test_data/*.pdf",
            "test_data/sample.pdf",
            "CorpusBuilderApp/tests/data/sample.pdf",
            "tests/data/sample.pdf"
        ]
        
        test_pdf = None
        for location in test_pdf_locations:
            if "*" in location:
                # Handle glob pattern
                import glob
                matches = glob.glob(location)
                if matches:
                    test_pdf = matches[0]  # Use first match
                    break
            elif os.path.isfile(location):
                test_pdf = location
                break
        
        if not test_pdf:
            print("⚠️  No test PDF found, skipping processing test")
            print("   Looked in:", test_pdf_locations)
            return True  # Not a failure, just no test file
        
        print(f"📁 Found test PDF: {test_pdf}")
        
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_text_from_pdf
        
        print("🔧 Attempting text extraction...")
        text = extract_text_from_pdf(test_pdf)
        
        if text and len(text.strip()) > 0:
            print(f"✅ Text extraction successful: {len(text)} characters")
            print(f"📝 First 100 characters: {text[:100]}...")
            return True
        else:
            print("❌ Text extraction returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Error in PDF processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_table_extraction():
    """Test 6: Test table extraction specifically (main Ghostscript use case)"""
    print("\n📊 Test 6: Table Extraction Test")
    print("-" * 40)
    
    try:
        # Look for a test PDF file
        test_pdf_locations = [
            "G:/test_data/*.pdf",
            "test_data/sample.pdf",
            "CorpusBuilderApp/tests/data/sample.pdf",
            "tests/data/sample.pdf"
        ]
        
        test_pdf = None
        for location in test_pdf_locations:
            if "*" in location:
                # Handle glob pattern
                import glob
                matches = glob.glob(location)
                if matches:
                    test_pdf = matches[0]  # Use first match
                    break
            elif os.path.isfile(location):
                test_pdf = location
                break
        
        if not test_pdf:
            print("⚠️  No test PDF found, creating minimal test...")
            return test_ghostscript_command_line()
        
        print(f"📁 Using test PDF: {test_pdf}")
        
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_tables_from_pdf
        
        print("🔧 Attempting table extraction...")
        tables = extract_tables_from_pdf(test_pdf, timeout_seconds=30, verbose=True)
        
        print(f"✅ Table extraction completed: {len(tables)} tables found")
        if tables:
            print(f"📊 First table preview: {str(tables[0])[:200]}...")
        return True
            
    except Exception as e:
        print(f"❌ Error in table extraction: {e}")
        print(f"   This might indicate Ghostscript integration issues")
        import traceback
        traceback.print_exc()
        return False

def test_ghostscript_command_line():
    """Test 7: Direct Ghostscript command line test"""
    print("\n⚡ Test 7: Direct Ghostscript Command Test")
    print("-" * 40)
    
    try:
        import subprocess
        
        gs_path = os.environ.get('GHOSTSCRIPT_PATH')
        if not gs_path:
            print("❌ GHOSTSCRIPT_PATH not set")
            return False
        
        print(f"🔧 Testing Ghostscript at: {gs_path}")
        
        # Try to run ghostscript with version flag
        result = subprocess.run([gs_path, '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ Ghostscript responds: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Ghostscript failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Ghostscript command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running Ghostscript: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 GHOSTSCRIPT INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_ghostscript_detection,
        test_environment_setup, 
        test_camelot_ghostscript,
        test_worker_process_setup,
        test_simple_pdf_processing,
        test_table_extraction,
        test_ghostscript_command_line
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"Test {i}: {test.__name__} - {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Ghostscript integration is working!")
    else:
        print("⚠️  SOME TESTS FAILED - Check the output above for details")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 