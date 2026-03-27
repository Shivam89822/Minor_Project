import fitz  # PyMuPDF
from docx import Document
import os


def extract_text_from_pdf(file_path):
    text = ""
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text += page_text + "\n"
        doc.close()
    except Exception as e:
        raise Exception(f"Error extracting PDF: {str(e)}")

    return text.strip()


def extract_text_from_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        raise Exception(f"Error extracting DOCX: {str(e)}")

    return text.strip()


def extract_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("File does not exist")

    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)

    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")