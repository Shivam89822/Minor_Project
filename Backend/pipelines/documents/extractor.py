import os
import fitz
from docx import Document


def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text() + "\n"

    doc.close()
    return text.strip()



def extract_pages_from_pdf(file_path):
    pages = []
    doc = fitz.open(file_path)

    for page_index, page in enumerate(doc, start=1):
        pages.append(
            {
                "page": page_index,
                "text": page.get_text().strip(),
            }
        )

    doc.close()
    return pages



def extract_text_from_docx(file_path):
    text = ""
    doc = Document(file_path)

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text.strip()



def extract_sections_from_docx(file_path):
    sections = []
    doc = Document(file_path)
    current_section = "Document"
    current_lines = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        style_name = para.style.name.lower() if para.style and para.style.name else ""
        if "heading" in style_name:
            if current_lines:
                sections.append(
                    {
                        "page": None,
                        "section": current_section,
                        "text": "\n".join(current_lines).strip(),
                    }
                )
                current_lines = []
            current_section = text
            continue

        current_lines.append(text)

    if current_lines:
        sections.append(
            {
                "page": None,
                "section": current_section,
                "text": "\n".join(current_lines).strip(),
            }
        )

    if not sections:
        sections.append(
            {
                "page": None,
                "section": "Document",
                "text": "",
            }
        )

    return sections



def extract_document_units(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("File does not exist")

    if file_path.endswith(".pdf"):
        pages = extract_pages_from_pdf(file_path)
        return [
            {
                "page": page["page"],
                "section": None,
                "text": page["text"],
            }
            for page in pages
        ]

    if file_path.endswith(".docx"):
        return extract_sections_from_docx(file_path)

    raise ValueError("Unsupported file format")



def extract_text(file_path):
    units = extract_document_units(file_path)
    return "\n".join(unit["text"] for unit in units if unit["text"]).strip()
