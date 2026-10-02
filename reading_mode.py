# Reading Mode (V1)
#
#  1. find_document(frame)   -> cheap check: is a paper / menu / page in view?
#  2. scan_document(frame)   -> crop + straighten the page, run OCR, keep the text
#  3. get_document_context() -> the last scanned text (for the future LLM step)
#
# Nothing is saved to disk. The captured image is thrown away after OCR and
# the text only lives in memory for CONTEXT_LIFETIME seconds.

import time
import cv2
import numpy as np

DETECT_WIDTH = 500          # frame is shrunk to this width before looking for a page
MIN_AREA_RATIO = 0.15       # page must cover at least 15% of the frame
CONTEXT_LIFETIME = 10 * 60  # scanned text is forgotten after 10 minutes

_reader = None              # EasyOCR reader, created on the first scan (slow to load)
_document_context = None    # {"text": ..., "created_at": ...} or None


# ---------------- Document detection ----------------
def find_document(frame):
    """Returns the 4 corner points of a large page-like shape, or None."""
    if frame is None:
        return None

    # Work on a small copy so this stays fast
    scale = DETECT_WIDTH / frame.shape[1]
    small = cv2.resize(frame, (DETECT_WIDTH, int(frame.shape[0] * scale)))

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, None, iterations=1)  # closes small gaps in the outline

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = MIN_AREA_RATIO * small.shape[0] * small.shape[1]

    # Check the biggest shapes first; the first good 4-corner one wins
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        if cv2.contourArea(contour) < min_area:
            break  # everything after this is even smaller
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            return (approx.reshape(4, 2) / scale).astype(np.float32)

    return None


def crop_document(frame, corners):
    """Cuts out the page and straightens it into a flat, top-down image."""
    # Order corners: top-left, top-right, bottom-right, bottom-left
    s = corners.sum(axis=1)
    d = np.diff(corners, axis=1).ravel()
    tl, br = corners[np.argmin(s)], corners[np.argmax(s)]
    tr, bl = corners[np.argmin(d)], corners[np.argmax(d)]

    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if width < 10 or height < 10:
        return frame

    src = np.array([tl, tr, br, bl], dtype=np.float32)
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(frame, matrix, (width, height))


# ---------------- OCR ----------------
def read_text(image):
    """Runs OCR on an image and returns the text as one string ("" if none)."""
    global _reader
    if _reader is None:
        import easyocr  # imported here so the app still starts without it
        # Model files download once to ~/.EasyOCR (outside the project folder)
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)

    lines = _reader.readtext(image, detail=0, paragraph=True)
    return "\n".join(line.strip() for line in lines if line.strip())


def scan_document(frame):
    """Crops the page (if found), runs OCR, and stores the text in memory.
    Returns the text, or "" if nothing readable was found. May raise on OCR errors."""
    corners = find_document(frame)
    image = crop_document(frame, corners) if corners is not None else frame
    text = read_text(image)
    del image  # image is not kept anywhere

    if text:
        set_document_context(text)  # new scan replaces the old one
    return text


# ---------------- Temporary reading context ----------------
def set_document_context(text):
    global _document_context
    _document_context = {"text": text, "created_at": time.time()}


def get_document_context():
    """Returns the last scanned text, or None if there is none or it expired."""
    global _document_context
    context = _document_context
    if context is None:
        return None
    if time.time() - context["created_at"] > CONTEXT_LIFETIME:
        _document_context = None
        return None
    return context["text"]


def clear_document_context():
    global _document_context
    _document_context = None
