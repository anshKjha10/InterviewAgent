from pypdf import PdfReader


def extract_text_from_pdf(filepath: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()
