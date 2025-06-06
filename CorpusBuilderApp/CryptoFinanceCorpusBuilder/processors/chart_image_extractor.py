# processors/chart_image_extractor.py
"""
Extract and analyze charts, graphs, and images from PDF documents.
Includes OCR for text within images and chart type classification.
"""

import os
import json
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import pytesseract
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import hashlib
import base64
from io import BytesIO
import re

class ChartImageExtractor:
    """Extract and analyze charts, graphs, and images from PDFs."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config_path)
        
        # Chart/graph detection keywords
        self.chart_keywords = {
            'chart', 'graph', 'plot', 'figure', 'diagram', 'visualization',
            'histogram', 'scatter', 'line chart', 'bar chart', 'pie chart',
            'boxplot', 'heatmap', 'candlestick', 'time series', 'regression'
        }
        
        # Financial chart specific keywords
        self.financial_keywords = {
            'price', 'return', 'volatility', 'volume', 'portfolio',
            'performance', 'risk', 'yield', 'correlation', 'distribution',
            'trend', 'forecast', 'backtest', 'sharpe', 'drawdown'
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'min_image_size': (100, 100),  # Minimum width, height
            'max_image_size': (4000, 4000),  # Maximum to prevent memory issues
            'dpi': 300,  # DPI for image extraction
            'ocr_enabled': True,
            'save_images': False,  # Whether to save extracted images
            'image_output_dir': 'extracted_images',
            'detect_chart_type': True,
            'extract_text_from_images': True,
            'image_quality_threshold': 0.7,
            'supported_formats': ['png', 'jpg', 'jpeg', 'tiff', 'bmp']
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def extract_from_pdf(self, pdf_path: str, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract all images and charts from a PDF."""
        images_data = []
        total_raster_images = 0
        total_vector_graphics = 0
        
        try:
            doc = fitz.open(pdf_path)
            
            # Setup output directory if saving images
            if self.config['save_images'] and output_dir:
                img_output_dir = Path(output_dir) / self.config['image_output_dir']
                img_output_dir.mkdir(parents=True, exist_ok=True)
            else:
                img_output_dir = None
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract images from page
                page_images = self._extract_page_images(page, page_num, pdf_path, img_output_dir)
                images_data.extend(page_images)
                total_raster_images += len(page.get_images())
                
                # Look for vector graphics that might be charts
                vector_graphics = self._extract_vector_graphics(page, page_num)
                images_data.extend(vector_graphics)
                total_vector_graphics += len(vector_graphics)
            
            doc.close()
            
            print(f"Total raster images found: {total_raster_images}")
            print(f"Total vector graphics detected: {total_vector_graphics}")
            
        except Exception as e:
            self.logger.error(f"Error extracting images from PDF {pdf_path}: {e}")
        
        # Post-process and enhance image data
        enhanced_images = []
        for img_data in images_data:
            enhanced = self._enhance_image_data(img_data)
            if enhanced:
                enhanced_images.append(enhanced)
        
        return enhanced_images
    
    def _extract_page_images(self, page, page_num: int, pdf_path: str, 
                           output_dir: Optional[Path]) -> List[Dict[str, Any]]:
        """Extract raster images from a page."""
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                # Get image data
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Convert to PIL Image
                pil_image = Image.open(BytesIO(image_bytes))
                
                # Check size constraints
                if not self._is_valid_image_size(pil_image.size):
                    continue
                
                # Calculate quality score
                quality_score = self._calculate_image_quality(pil_image)
                if quality_score < self.config['image_quality_threshold']:
                    continue
                
                # Generate unique image ID
                image_id = self._generate_image_id(pdf_path, page_num, img_index)
                
                # Save image if configured
                image_path = None
                if output_dir:
                    image_filename = f"{image_id}.{image_ext}"
                    image_path = output_dir / image_filename
                    pil_image.save(image_path)
                
                # Extract text from image using OCR
                ocr_text = ""
                if self.config['extract_text_from_images']:
                    ocr_text = self._extract_text_from_image(pil_image)
                
                # Detect if this is likely a chart/graph
                is_chart = self._detect_chart_type(pil_image, ocr_text)
                
                # Create image metadata
                image_data = {
                    'id': image_id,
                    'page': page_num + 1,
                    'index_on_page': img_index,
                    'type': 'raster_image',
                    'format': image_ext,
                    'size': pil_image.size,
                    'mode': pil_image.mode,
                    'quality_score': quality_score,
                    'file_size': len(image_bytes),
                    'saved_path': str(image_path) if image_path else None,
                    'ocr_text': ocr_text,
                    'is_chart': is_chart['is_chart'],
                    'chart_type': is_chart['chart_type'],
                    'chart_confidence': is_chart['confidence'],
                    'contains_financial_content': self._contains_financial_content(ocr_text),
                    'image_hash': hashlib.md5(image_bytes).hexdigest(),
                    'base64_thumbnail': self._create_thumbnail_base64(pil_image) if not output_dir else None,
                    'metadata': {
                        'source': 'raster_image',
                        'quality_score': quality_score,
                        'chart_type': is_chart['chart_type'],
                        'chart_confidence': is_chart['confidence']
                    }
                }
                
                images.append(image_data)
                
            except Exception as e:
                self.logger.warning(f"Error processing image {img_index} on page {page_num}: {e}")
                continue
        
        return images
    
    def _extract_vector_graphics(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extract vector graphics that might be charts, rasterize, OCR, and analyze."""
        vector_graphics = []
        try:
            # Convert page to image to analyze vector content
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better analysis
            pix = page.get_pixmap(matrix=mat)
            pil_image = Image.open(BytesIO(pix.tobytes("png")))
            # Look for chart-like patterns in the rendered page
            chart_detection = self._detect_chart_in_rendered_page(pil_image, page)
            if chart_detection['has_charts']:
                for chart_area in chart_detection['chart_areas']:
                    # Extract the chart area as a separate image
                    chart_image = pil_image.crop(chart_area['bbox'])
                    # Extract text from the chart area using OCR
                    ocr_text = self._extract_text_from_image(chart_image) if self.config['extract_text_from_images'] else ""
                    # Classify chart type
                    chart_type = chart_area.get('chart_type', 'unknown')
                    # Create unified metadata
                    vector_data = {
                        'id': f"vector_{page_num}_{chart_area['index']}",
                        'page': page_num + 1,
                        'type': 'vector_graphic',
                        'format': 'png',
                        'size': chart_image.size,
                        'bbox': chart_area['bbox'],
                        'quality_score': chart_area['confidence'],
                        'ocr_text': ocr_text,
                        'is_chart': True,
                        'chart_type': chart_type,
                        'chart_confidence': chart_area['confidence'],
                        'contains_financial_content': self._contains_financial_content(ocr_text),
                        'base64_thumbnail': self._create_thumbnail_base64(chart_image),
                        'metadata': {
                            'source': 'vector_graphic',
                            'quality_score': chart_area['confidence'],
                            'chart_type': chart_type,
                            'chart_confidence': chart_area['confidence']
                        }
                    }
                    vector_graphics.append(vector_data)
        except Exception as e:
            self.logger.warning(f"Error extracting vector graphics from page {page_num}: {e}")
        return vector_graphics
    
    def _is_valid_image_size(self, size: Tuple[int, int]) -> bool:
        """Check if image size is within acceptable bounds."""
        width, height = size
        min_w, min_h = self.config['min_image_size']
        max_w, max_h = self.config['max_image_size']
        
        return (min_w <= width <= max_w) and (min_h <= height <= max_h)
    
    def _calculate_image_quality(self, image: Image.Image) -> float:
        """Calculate a quality score for the image."""
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image.convert('RGB'))
            
            # Calculate various quality metrics
            # 1. Sharpness (using Laplacian variance)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(1.0, laplacian_var / 1000.0)
            
            # 2. Contrast (using standard deviation)
            contrast_score = min(1.0, np.std(gray) / 128.0)
            
            # 3. Information content (entropy)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten()
            hist = hist[hist > 0]  # Remove zeros
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            entropy_score = min(1.0, entropy / 8.0)
            
            # Combine scores
            quality_score = (sharpness_score * 0.4 + contrast_score * 0.3 + entropy_score * 0.3)
            return quality_score
            
        except Exception as e:
            self.logger.warning(f"Error calculating image quality: {e}")
            return 0.5  # Default medium quality
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        if not self.config['ocr_enabled']:
            return ""
        
        try:
            # Enhance image for better OCR
            enhanced_image = self._enhance_image_for_ocr(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(enhanced_image, config='--psm 6')
            
            # Clean up the text
            text = ' '.join(text.split())  # Normalize whitespace
            
            return text
            
        except Exception as e:
            self.logger.warning(f"Error extracting text from image: {e}")
            return ""
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Resize if too small (OCR works better on larger images)
            width, height = image.size
            if width < 300 or height < 300:
                scale_factor = max(300 / width, 300 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Error enhancing image for OCR: {e}")
            return image
    
    def _detect_chart_type(self, image: Image.Image, ocr_text: str) -> Dict[str, Any]:
        """Detect if image is a chart and classify its type."""
        is_chart = False
        chart_type = "unknown"
        confidence = 0.0
        
        try:
            # Text-based detection
            text_lower = ocr_text.lower()
            
            # Check for chart-related keywords
            chart_keywords_found = sum(1 for keyword in self.chart_keywords if keyword in text_lower)
            if chart_keywords_found > 0:
                is_chart = True
                confidence += 0.3
            
            # Check for axis labels and numerical data
            has_numbers = bool(re.search(r'\d+', ocr_text))
            has_axis_words = any(word in text_lower for word in ['x', 'y', 'axis', 'time', 'date', 'value'])
            
            if has_numbers and has_axis_words:
                is_chart = True
                confidence += 0.2
            
            # Visual analysis
            visual_analysis = self._analyze_chart_visually(image)
            if visual_analysis['is_chart']:
                is_chart = True
                confidence += visual_analysis['confidence']
                chart_type = visual_analysis['chart_type']
            
            # Specific chart type detection based on text
            if is_chart:
                chart_type = self._classify_chart_type(ocr_text, visual_analysis)
            
            confidence = min(1.0, confidence)
            
        except Exception as e:
            self.logger.warning(f"Error detecting chart type: {e}")
        
        return {
            'is_chart': is_chart,
            'chart_type': chart_type,
            'confidence': confidence
        }
    
    def _analyze_chart_visually(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image visually to detect chart characteristics."""
        try:
            # Convert to OpenCV format
            img_array = np.array(image.convert('RGB'))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect lines (common in charts)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            has_lines = lines is not None and len(lines) > 5
            
            # Detect rectangular regions (axes, legend boxes)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rectangular_contours = 0
            
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular
                if len(approx) == 4:
                    rectangular_contours += 1
            
            has_rectangles = rectangular_contours > 2
            
            # Calculate visual complexity (charts tend to have medium complexity)
            complexity = np.std(gray) / 255.0
            moderate_complexity = 0.1 < complexity < 0.8
            
            # Combine visual cues
            is_chart = has_lines and (has_rectangles or moderate_complexity)
            confidence = 0.0
            
            if has_lines:
                confidence += 0.3
            if has_rectangles:
                confidence += 0.2
            if moderate_complexity:
                confidence += 0.1
            
            # Guess chart type based on visual patterns
            chart_type = "unknown"
            if has_lines and rectangular_contours > 5:
                chart_type = "line_chart"
            elif rectangular_contours > 8:
                chart_type = "bar_chart"
            
            return {
                'is_chart': is_chart,
                'chart_type': chart_type,
                'confidence': confidence,
                'visual_features': {
                    'has_lines': has_lines,
                    'has_rectangles': has_rectangles,
                    'complexity': complexity,
                    'line_count': len(lines) if lines is not None else 0,
                    'rectangle_count': rectangular_contours
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Error in visual chart analysis: {e}")
            return {'is_chart': False, 'chart_type': 'unknown', 'confidence': 0.0}
    
    def _classify_chart_type(self, ocr_text: str, visual_analysis: Dict[str, Any]) -> str:
        """Classify the specific type of chart based on text and visual cues."""
        text_lower = ocr_text.lower()
        
        # Text-based classification
        if any(word in text_lower for word in ['pie', 'slice', 'percentage', '%']):
            return "pie_chart"
        elif any(word in text_lower for word in ['histogram', 'frequency', 'distribution']):
            return "histogram"
        elif any(word in text_lower for word in ['scatter', 'correlation']):
            return "scatter_plot"
        elif any(word in text_lower for word in ['box', 'quartile', 'median']):
            return "box_plot"
        elif any(word in text_lower for word in ['time', 'date', 'year', 'month']):
            return "time_series"
        elif any(word in text_lower for word in ['bar', 'column']):
            return "bar_chart"
        elif any(word in text_lower for word in ['line', 'trend']):
            return "line_chart"
        elif any(word in text_lower for word in ['heat', 'correlation matrix']):
            return "heatmap"
        
        # Fall back to visual analysis
        return visual_analysis.get('chart_type', 'unknown')
    
    def _contains_financial_content(self, text: str) -> bool:
        """Check if the text contains financial terminology."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.financial_keywords)
    
    def _generate_image_id(self, pdf_path: str, page_num: int, img_index: int) -> str:
        """Generate unique ID for an image."""
        pdf_name = Path(pdf_path).stem
        return f"{pdf_name}_p{page_num + 1}_img{img_index}"
    
    def _create_thumbnail_base64(self, image: Image.Image, size: Tuple[int, int] = (150, 150)) -> str:
        """Create a base64-encoded thumbnail of the image."""
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            thumbnail.save(buffer, format='PNG')
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            self.logger.warning(f"Error creating thumbnail: {e}")
            return ""
    
    def _detect_chart_in_rendered_page(self, page_image: Image.Image, page) -> Dict[str, Any]:
        """Detect chart areas in a rendered page image."""
        # This is a simplified implementation
        # In practice, you might use more sophisticated computer vision techniques
        
        try:
            # Look for rectangular regions that might contain charts
            img_array = np.array(page_image.convert('RGB'))
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Find contours
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            chart_areas = []
            for i, contour in enumerate(contours):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter based on size (charts are usually reasonably large)
                if w > 200 and h > 150 and w * h > 50000:
                    chart_areas.append({
                        'index': i,
                        'bbox': (x, y, x + w, y + h),
                        'chart_type': 'unknown',
                        'confidence': 0.5  # Default confidence for detected areas
                    })
            
            return {
                'has_charts': len(chart_areas) > 0,
                'chart_areas': chart_areas
            }
            
        except Exception as e:
            self.logger.warning(f"Error detecting charts in rendered page: {e}")
            return {'has_charts': False, 'chart_areas': []}
    
    def _enhance_image_data(self, img_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance and validate image data."""
        try:
            # Add additional metadata
            img_data['extraction_timestamp'] = time.time()
            img_data['is_financial_chart'] = (
                img_data['is_chart'] and 
                img_data['contains_financial_content']
            )
            
            # Calculate relevance score
            relevance_score = 0.0
            if img_data['is_chart']:
                relevance_score += 0.5
            if img_data['contains_financial_content']:
                relevance_score += 0.3
            if img_data['quality_score'] > 0.7:
                relevance_score += 0.2
            
            img_data['relevance_score'] = relevance_score
            
            return img_data
            
        except Exception as e:
            self.logger.warning(f"Error enhancing image data: {e}")
            return None

# Integration function for your existing pipeline
def integrate_chart_image_extraction(pdf_path: str, output_dir: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """Integration function for your existing pipeline."""
    extractor = ChartImageExtractor(config_path)
    images = extractor.extract_from_pdf(pdf_path, output_dir)
    
    # Calculate summary statistics
    total_images = len(images)
    charts = [img for img in images if img['is_chart']]
    financial_charts = [img for img in images if img.get('is_financial_chart', False)]
    
    return {
        'images': images,
        'statistics': {
            'total_images': total_images,
            'total_charts': len(charts),
            'financial_charts': len(financial_charts),
            'avg_quality': sum(img['quality_score'] for img in images) / total_images if total_images > 0 else 0,
            'chart_types': {chart['chart_type']: sum(1 for c in charts if c['chart_type'] == chart['chart_type']) 
                           for chart in charts},
        }
    }