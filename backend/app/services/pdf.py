from io import BytesIO

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF: software libraries first, tesseract OCR as last resort."""
    extractors = [
        _extract_with_pymupdf,
        _extract_with_pdfplumber,
        _extract_with_pdfminer,
        _extract_with_pypdf,
    ]

    best_non_empty = ""
    for extractor in extractors:
        text = extractor(file_bytes)
        if _is_clean(text):
            return text.strip()
        stripped = text.strip()
        if stripped and len(stripped) > len(best_non_empty):
            best_non_empty = stripped

    ocr_text = _extract_with_tesseract(file_bytes).strip()
    if _is_clean(ocr_text):
        return ocr_text
    if ocr_text:
        return ocr_text
    return best_non_empty


def _is_clean(text: str) -> bool:
    """Check if extracted text is readable (no CID codes, sufficient alphabetic content)."""
    stripped = text.strip()
    if not stripped or len(stripped) < 50:
        return False
    if "(cid:" in stripped.lower():
        return False
    alpha_ratio = sum(c.isalpha() for c in stripped) / len(stripped)
    return alpha_ratio >= 0.35


def _pdf_to_images(file_bytes: bytes, scale: float = 2.0) -> list[Image.Image]:
    images: list[Image.Image] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        mat = fitz.Matrix(scale, scale)
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    return images


def _extract_with_tesseract(file_bytes: bytes) -> str:
    """Tesseract OCR — fallback for PDFs with broken font encodings."""
    full_text = ""
    try:
        images = _pdf_to_images(file_bytes, scale=2.0)
        for img in images:
            full_text += pytesseract.image_to_string(img, lang="pol+eng") + "\n"
    except Exception as exc:
        print(f"[pdf] Tesseract OCR failed: {exc}")
    return full_text


def _extract_with_pymupdf(file_bytes: bytes) -> str:
    """PyMuPDF — fastest, best at standard fonts."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts: list[str] = []
    for page in doc:
        page_text = page.get_text() or ""
        if page_text:
            texts.append(page_text)
    doc.close()
    return "\n".join(texts)


def _extract_with_pdfplumber(file_bytes: bytes) -> str:
    """pdfplumber — good layout reconstruction, handles tables."""
    texts: list[str] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                texts.append(page_text)
    return "\n".join(texts)


def _extract_with_pdfminer(file_bytes: bytes) -> str:
    """pdfminer.six — most thorough font encoding handling."""
    return pdfminer_extract_text(BytesIO(file_bytes)) or ""


def _extract_with_pypdf(file_bytes: bytes) -> str:
    """pypdf — fallback."""
    reader = PdfReader(BytesIO(file_bytes))
    texts: list[str] = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)
