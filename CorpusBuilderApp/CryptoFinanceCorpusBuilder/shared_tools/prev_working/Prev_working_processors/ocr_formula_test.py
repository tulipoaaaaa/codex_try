import fitz
from PIL import Image
import pytesseract
from io import BytesIO


def extract_formulas_via_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    formulas = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Render page as image
        pix = page.get_pixmap()
        img = Image.open(BytesIO(pix.tobytes("png")))
        # Run OCR
        ocr_text = pytesseract.image_to_string(img, config='--psm 6')
        # Simple heuristic: look for math symbols or patterns
        if any(sym in ocr_text for sym in ['=', '\\frac', '\\sum', '\\int', '+', '-', '*', '/', '^']):
            print(f"Page {page_num+1} - Mathematical content detected:")
            print(ocr_text[:500])  # Print first 500 chars for review
            formulas.append({
                'page': page_num + 1,
                'ocr_text': ocr_text,
                'confidence': 0.5,  # Placeholder
                'source': 'ocr_image'
            })
    doc.close()
    return formulas


if __name__ == "__main__":
    extract_formulas_via_ocr('data/test_collect/full_pipeline_short/high_frequency_trading/cryptocurrency-time-series-on-the-binary-complexity-entropy-plane-ranking-efficiency-from-the-perspective-of-complex-systems.pdf') 