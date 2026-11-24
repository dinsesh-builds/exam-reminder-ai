import io

import pdfplumber
import pytesseract
from PIL import Image, ImageOps

MIN_PDF_CHARS = 80
TESSERACT_CONFIG = "--oem 3 --psm 6"


def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()
    try:
        if name.endswith(".pdf"):
            return extract_from_pdf(file_bytes)
        if any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            return extract_from_image(file_bytes)
        return file_bytes.decode("utf-8", errors="backslashreplace")
    except ValueError:
        raise
    except Exception:
        raise ValueError("This file could not be read. Check that it is not damaged or encrypted.")


def extract_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True) or ""
            if len(page_text.strip()) >= 20:
                text += page_text + "\n"

    if len(text.strip()) >= MIN_PDF_CHARS:
        return text.strip()
    return ocr_scanned_pdf(file_bytes)


def ocr_scanned_pdf(file_bytes: bytes) -> str:
    try:
        import fitz
    except ImportError:
        raise ValueError(
            "This PDF has no text layer. Install pymupdf to enable scanned PDF OCR."
        )

    document = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page in document:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csGRAY)
        image = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)
        pages.append(pytesseract.image_to_string(image, config=TESSERACT_CONFIG))
    return "\n".join(pages).strip()


def extract_from_image(file_bytes: bytes) -> str:
    image = ImageOps.grayscale(Image.open(io.BytesIO(file_bytes)))
    return pytesseract.image_to_string(image, config=TESSERACT_CONFIG).strip()
