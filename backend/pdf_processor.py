import pdfplumber
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def process_pdf(pdf_path: str) -> list:
    """Extract and chunk text from PDF"""
    print(f"Processing PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    print(f"Created {len(chunks)} chunks")
    return chunks