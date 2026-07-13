import io
import os
import shutil

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


def _resolve_tesseract_cmd() -> None:
    """
    Point pytesseract at the Tesseract binary.

    In Docker/Linux the binary is on PATH, so nothing is needed. On Windows the
    UB-Mannheim installer drops it in Program Files but doesn't add it to PATH,
    so fall back to the standard install locations. An explicit TESSERACT_CMD
    env var overrides everything.
    """
    override = os.environ.get("TESSERACT_CMD")
    if override:
        pytesseract.pytesseract.tesseract_cmd = override
        return

    if shutil.which("tesseract"):
        return  # already on PATH (Docker, Linux, or PATH-configured Windows)

    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.exists(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return


_resolve_tesseract_cmd()


# Minimum characters a PDF text layer must yield before we trust it and skip
# OCR. Scanned reports have little or no embedded text, so anything below this
# threshold is treated as image-only and rendered for OCR instead.
_MIN_TEXT_LAYER_CHARS = 20

# Resolution to render PDF pages at before OCR. Tesseract accuracy improves
# sharply above the ~72 DPI default; 300 DPI is the usual sweet spot.
_OCR_RENDER_DPI = 300


def _ocr_pdf(doc: "fitz.Document") -> str:
    """Render each PDF page to an image and OCR it with Tesseract."""
    pages_text = []
    for page in doc:
        pix = page.get_pixmap(dpi=_OCR_RENDER_DPI)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        pages_text.append(pytesseract.image_to_string(image))
    return "\n".join(pages_text)


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a PDF or image file.

    PDFs are read via their embedded text layer when one is present; scanned
    PDFs with little or no text layer fall back to rendering each page to an
    image and running OCR. Image files are OCR'd directly.

    Supported extensions: .pdf, .jpg, .jpeg, .png
    Raises ValueError for any other extension.
    """
    lower = filename.lower()

    if lower.endswith(".pdf"):
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            text_layer = "\n".join(page.get_text() for page in doc)
            if len(text_layer.strip()) >= _MIN_TEXT_LAYER_CHARS:
                return text_layer
            # No usable text layer -> almost certainly a scan; OCR the pages.
            return _ocr_pdf(doc)
        finally:
            doc.close()

    if lower.endswith((".jpg", ".jpeg", ".png")):
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)

    ext = filename.rsplit(".", 1)[-1] if "." in filename else filename
    raise ValueError(
        f"Unsupported file format '.{ext}'. "
        "Please upload a PDF, JPG, JPEG, or PNG file."
    )
