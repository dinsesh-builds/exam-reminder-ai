import io
import pdfplumber
import pytesseract
from PIL import Image

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Detect file type and extract text.
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        return extract_from_pdf(file_bytes)
    
    elif any(filename_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]):
        return extract_from_image(file_bytes)
    
    elif filename_lower.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")
    
    else:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file type: {filename}")

def extract_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_from_image(file_bytes: bytes) -> str:
    """Extract text from image using Tesseract OCR."""
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return text.strip()