import re


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text
    """

    if not text:
        return ""

    # Convert to string (safety)
    text = str(text)

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove unwanted special characters (keep basic punctuation)
    text = re.sub(r"[^a-zA-Z0-9.,!?;:()\-\'\" ]", " ", text)

    # Normalize multiple spaces → single space
    text = re.sub(r"\s+", " ", text)

    # Remove repeated punctuation (!!! → !)
    text = re.sub(r"([!?.,])\1+", r"\1", text)

    # Strip leading/trailing spaces
    text = text.strip()

    return text