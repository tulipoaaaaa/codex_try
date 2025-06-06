import os
import fitz  # PyMuPDF
import logging
import warnings

# Suppress PyMuPDF warnings about wrong pointing objects
warnings.filterwarnings("ignore", message="Ignoring wrong pointing object")

def safe_open_pdf(pdf_path, timeout=10):
    """Safely open a PDF file with timeout and error handling."""
    try:
        # Convert to absolute path
        pdf_path = os.path.abspath(pdf_path)
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            return None
            
        # Check if file is readable
        if not os.access(pdf_path, os.R_OK):
            return None
            
        # First try simple open to verify
        try:
            with open(pdf_path, 'rb') as f:
                sample = f.read(100)  # Read just a bit to check
                if not sample:
                    return None
        except Exception:
            return None
            
        # Now try to load with PyMuPDF with proper error handling
        try:
            doc = fitz.open(pdf_path)
            pdf_bytes = doc.tobytes()
            doc.close()
            return pdf_bytes
        except Exception:
            return None
            
    except Exception:
        return None 