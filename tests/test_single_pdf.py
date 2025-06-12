#!/usr/bin/env python3
"""
Test script to extract text from a specific PDF file
"""

import sys
import glob
from pathlib import Path

# Add the project to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to root
sys.path.insert(0, str(project_root))

def test_pdf_extraction(custom_pdf_path=None):
    # Use custom path if provided, otherwise find one from test_data
    if custom_pdf_path:
        pdf_path = custom_pdf_path
    else:
        # Look for PDFs in test_data directory
        test_pdfs = glob.glob("G:/test_data/*.pdf")
        if test_pdfs:
            pdf_path = test_pdfs[0]  # Use first available PDF
            print(f"🔍 Auto-selected PDF from test_data: {Path(pdf_path).name}")
        else:
            # Fallback to the original hardcoded path
            pdf_path = r"G:\test_data\10_1111_cyt_12104_pdf -- Dudding, N_ ;Crossley, J_ -- Cytopathology, #5, 24, pages 283-288, 2013 sep 18 -- John Wiley and Sons; Wiley (Blackwell -- 10_1111_cyt_12104 -- 059a0d666db (1 - Copy.pdf"
    
    print(f"🔍 Testing PDF: {pdf_path}")
    print(f"📁 File exists: {Path(pdf_path).exists()}")
    
    if not Path(pdf_path).exists():
        print("❌ File not found!")
        return False
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_text_from_pdf
        
        print("🔧 Starting text extraction...")
        result = extract_text_from_pdf(pdf_path)
        
        if result:
            print(f"✅ Extraction successful!")
            print(f"📊 Extracted {len(result)} characters")
            print(f"📝 First 200 characters: {result[:200]}...")
            return True
        else:
            print("❌ Extraction returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_table_extraction(custom_pdf_path=None):
    """Test table extraction specifically"""
    print("\n" + "="*50)
    print("📊 TESTING TABLE EXTRACTION")
    print("="*50)
    
    # Use same PDF selection logic
    if custom_pdf_path:
        pdf_path = custom_pdf_path
    else:
        test_pdfs = glob.glob("G:/test_data/*.pdf")
        if test_pdfs:
            pdf_path = test_pdfs[0]
            print(f"🔍 Auto-selected PDF: {Path(pdf_path).name}")
        else:
            pdf_path = r"G:\test_data\10_1111_cyt_12104_pdf -- Dudding, N_ ;Crossley, J_ -- Cytopathology, #5, 24, pages 283-288, 2013 sep 18 -- John Wiley and Sons; Wiley (Blackwell -- 10_1111_cyt_12104 -- 059a0d666db (1 - Copy.pdf"
    
    print(f"📁 File exists: {Path(pdf_path).exists()}")
    
    if not Path(pdf_path).exists():
        print("❌ File not found!")
        return False
    
    try:
        from CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor import extract_tables_from_pdf
        
        print("🔧 Starting table extraction...")
        tables = extract_tables_from_pdf(pdf_path, timeout_seconds=30, verbose=True)
        
        print(f"✅ Table extraction completed!")
        print(f"📊 Found {len(tables)} tables")
        
        for i, table in enumerate(tables):
            print(f"📋 Table {i+1}: {table.shape if hasattr(table, 'shape') else 'Unknown shape'}")
            
        return True
            
    except Exception as e:
        print(f"❌ Error during table extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Allow custom PDF path as command line argument
    custom_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🧪 PDF PROCESSING TEST")
    print("="*50)
    
    # Test text extraction
    success1 = test_pdf_extraction(custom_path)
    
    # Test table extraction
    success2 = test_table_extraction(custom_path)
    
    overall_success = success1 and success2
    print(f"\n🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    sys.exit(0 if overall_success else 1) 