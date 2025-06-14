"""Image-based table extractor for scanned PDF pages.

This helper is invoked **only** when Camelot fails to detect any vector tables
and the environment variable ``ENABLE_IMAGE_TABLE_OCR`` is set to ``"1"``.

Algorithm (classic CV, no external services):
1.  Receive a PyMuPDF pixmap and convert to OpenCV BGR matrix.
2.  Adaptive threshold to binary; extract horizontal and vertical line masks
    via morphological operations to detect the table grid.
3.  Combine masks, find contours ⇒ candidate table bounding boxes.
4.  For each box:
    a. Build refined grid of cell intersections using projection profiles.
    b. Crop each cell, OCR with Tesseract (PSM 7).
5.  Assemble the cell text into a 2-D list and emit a dict compatible with the
    structure produced by Camelot in our pipeline.

The logic is deliberately simple and fast (≈ 0.2–0.4 s per page on a laptop).
A future ML model can replace the grid detection without changing the API.
"""
from __future__ import annotations

import os
import uuid
from typing import List, Dict
import re

import cv2  # type: ignore
import numpy as np  # type: ignore
import pytesseract  # type: ignore
from PIL import Image
from pathlib import Path
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# New: configurable Tesseract config string for cell OCR
TESS_CONFIG = os.getenv(
    "TESSERACT_OCR_TABLE_CONFIG",
    # PSM 7: treat the image as a single text line; OEM 3: default LSTM OCR engine.
    "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz%()[]{}-+.,/"
)

# Global tuneables ----------------------------------------------------------
GAP_THRESH_FACTOR = float(os.getenv("TABLE_GAP_THRESH", "0.3"))  # tighter gap detection

# Secondary configs ---------------------------------------------------------
NUMERIC_CONFIG = os.getenv(
    "TESSERACT_OCR_NUMERIC_CONFIG",
    "--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.,-E%"
)

TESS_CONFIG_WIDE = os.getenv(
    "TESSERACT_OCR_TABLE_CONFIG_WIDE",
    TESS_CONFIG.replace("--psm 7", "--psm 6") if "--psm 7" in TESS_CONFIG else f"{TESS_CONFIG} --psm 6",
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _pixmap_to_cv2(pix) -> np.ndarray:
    """Convert a PyMuPDF pixmap to a BGR OpenCV image."""
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def _detect_table_boxes(bin_img: np.ndarray) -> List[np.ndarray]:
    """Return a list of bounding boxes (x, y, w, h) likely containing tables."""
    # ------------------------------------------------------------------
    # Primary line detection via morphology
    # ------------------------------------------------------------------
    horizontal = bin_img.copy()
    vertical = bin_img.copy()
    rows, cols = bin_img.shape

    # Use smaller kernels for faint lines
    h_size = max(1, cols // 80)
    v_size = max(1, rows // 80)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))

    horizontal = cv2.erode(horizontal, h_kernel, iterations=2)
    horizontal = cv2.dilate(horizontal, h_kernel, iterations=2)

    vertical = cv2.erode(vertical, v_kernel, iterations=2)
    vertical = cv2.dilate(vertical, v_kernel, iterations=2)

    mask = cv2.add(horizontal, vertical)

    boxes = _contour_boxes(mask)

    # ------------------------------------------------------------------
    # Fallback: Hough lines if morphology yielded <2 boxes
    # ------------------------------------------------------------------
    if len(boxes) < 2:
        edges = cv2.Canny(bin_img, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=cols * 0.3, maxLineGap=10)
        if lines is not None and len(lines) >= 2:
            xs, ys, xe, ye = [], [], [], []
            for l in lines[:500]:
                xs.append(l[0][0]); ys.append(l[0][1]); xe.append(l[0][2]); ye.append(l[0][3])
            x_min, y_min = int(min(xs + xe)), int(min(ys + ye))
            x_max, y_max = int(max(xs + xe)), int(max(ys + ye))
            w, h = x_max - x_min, y_max - y_min
            if w > 150 and h > 70:
                boxes.append((x_min, y_min, w, h))

    return boxes


def _contour_boxes(mask: np.ndarray):
    """Utility: extract bounding boxes from a binary mask."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 150 or h < 70:
            continue
        boxes.append((x, y, w, h))
    return boxes


def _extract_cells_from_box(gray: np.ndarray, box: tuple[int, int, int, int]):
    x, y, w, h = box
    roi = gray[y : y + h, x : x + w]
    # Project to find column separators --------------------------------------
    col_sum = cv2.reduce(255 - roi, 0, cv2.REDUCE_AVG)[0]
    row_sum = cv2.reduce(255 - roi, 1, cv2.REDUCE_AVG)[:, 0]
    # Thresholds to find gaps -------------------------------------------------
    col_thresh = np.percentile(col_sum, 95) * GAP_THRESH_FACTOR
    row_thresh = np.percentile(row_sum, 95) * GAP_THRESH_FACTOR
    col_idx = np.where(col_sum < col_thresh)[0]
    row_idx = np.where(row_sum < row_thresh)[0]
    # Cluster indices into bands --------------------------------------------
    def _clusters(indices):
        bands = []
        if len(indices) == 0:
            return bands
        start = indices[0]
        prev = indices[0]
        for idx in indices[1:]:
            if idx - prev > 3:  # gap
                bands.append((start, prev))
                start = idx
            prev = idx
        bands.append((start, prev))
        # convert to mid-points
        return [int((s + e) / 2) for s, e in bands]

    vert_lines = _clusters(col_idx)
    horiz_lines = _clusters(row_idx)
    if len(vert_lines) < 2 or len(horiz_lines) < 2:
        return []
    # Cell cropping -----------------------------------------------------------
    cells = []
    for r in range(len(horiz_lines) - 1):
        row_cells = []
        y0 = horiz_lines[r]
        y1 = horiz_lines[r + 1]
        for c in range(len(vert_lines) - 1):
            x0 = vert_lines[c]
            x1 = vert_lines[c + 1]
            # Crop slightly inside the cell to avoid grid lines (±2 px guard).
            cx0 = max(0, x0 + 2)
            cy0 = max(0, y0 + 2)
            cx1 = min(roi.shape[1], x1 - 2)
            cy1 = min(roi.shape[0], y1 - 2)
            if cx1 <= cx0 or cy1 <= cy0:
                cell_img = roi[y0:y1, x0:x1]
            else:
                cell_img = roi[cy0:cy1, cx0:cx1]
            row_cells.append(cell_img)
        cells.append(row_cells)
    return cells


def extract_tables_from_pixmap(pix, page: int) -> List[Dict]:
    """Detect and OCR tables on a scanned page.

    Args:
        pix: PyMuPDF pixmap object for the page.
        page: 1-based page number.

    Returns:
        List of table dictionaries compatible with existing pipeline.
    """
    img_bgr = _pixmap_to_cv2(pix)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Deskew page before thresholding ---------------------------------------
    gray = _deskew(gray)

    # Adaptive threshold to get clean binary ---------------------------------
    bin_img = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10
    )

    tables: List[Dict] = []
    for box in _detect_table_boxes(bin_img):
        cells = _extract_cells_from_box(gray, box)
        if not cells:
            continue
        data = []
        for row in cells:
            row_text = []
            for cell in row:
                # Preprocess the cell for better OCR ---------------------------------
                if cell.size == 0:
                    txt = ""
                else:
                    proc = _prepare_cell_for_ocr(cell)

                    # Dual-pass OCR with adaptive config ---------------------
                    aspect = proc.shape[1] / max(1, proc.shape[0])
                    base_cfg = TESS_CONFIG_WIDE if aspect > 2 else TESS_CONFIG

                    txt = pytesseract.image_to_string(proc, config=base_cfg).strip()

                    # Numeric fallback when no digits detected --------------
                    if not any(ch.isdigit() for ch in txt):
                        alt = pytesseract.image_to_string(proc, config=NUMERIC_CONFIG).strip()
                        # Use alt only if longer or contains digits
                        if len(alt) > len(txt):
                            txt = alt

                row_text.append(txt)
            data.append(row_text)
        if not data:
            continue
        table_id = f"img_table_{uuid.uuid4().hex[:8]}"
        tables.append(
            {
                "table_id": table_id,
                "page": page,
                "shape": (len(data), max(len(r) for r in data)),
                "data": [
                    {f"col_{j}": r[j] if j < len(r) else "" for j in range(len(data[0]))}
                    for r in data
                ],
                "extraction_method": "opencv_ocr",
                "accuracy": None,
            }
        )
    return tables


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Deskew an image using dominant line orientation (fast heuristic)."""
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180.0, 200)
    if lines is None:
        return gray
    angles = []
    for l in lines[:20]:
        rho, theta = l[0]
        angle = (theta * 180.0 / np.pi) - 90  # around horizontal axis
        if -15 < angle < 15:  # avoid vertical lines
            angles.append(angle)
    if not angles:
        return gray
    angle = np.median(angles)
    if abs(angle) < 0.5:  # already straight
        return gray
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=255)
    return rotated 

# ---------------------------------------------------------------------------
# Additional helpers
# ---------------------------------------------------------------------------

def _prepare_cell_for_ocr(cell: np.ndarray, target_min_height: int = 40) -> np.ndarray:
    """Invert, binarise, upscale and dilate a cell image for OCR."""
    if cell.size == 0:
        return cell

    img = cv2.bitwise_not(cell)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Upscale small cells for better OCR resolution
    h, w = img.shape[:2]
    if h < target_min_height:
        scale = target_min_height / h
        img = cv2.resize(img, (int(w * scale), target_min_height), interpolation=cv2.INTER_CUBIC)

    # Dilate to strengthen thin strokes
    kernel = np.ones((2, 2), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)

    # Add border
    img = cv2.copyMakeBorder(img, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=255)
    return img 