import fitz
from docx import Document
import os

def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text() + "\n"

    doc.close()
    return text.strip()


def extract_text_from_docx(file_path):
    text = ""
    doc = Document(file_path)

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text.strip()


def extract_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("File does not exist")

    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)

    else:
        raise ValueError("Unsupported file format")