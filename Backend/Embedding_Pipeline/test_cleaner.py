from processing.cleaner import clean_text

# Sample messy text
raw_text = """
Visit https://example.com !!!

This is    a sample text with @@ noise ###
and    multiple     spaces.

AI is amazing!!! AI is powerful!!!
"""

# Run cleaner
cleaned = clean_text(raw_text)

print("===== ORIGINAL TEXT =====")
print(raw_text)

print("\n===== CLEANED TEXT =====")
print(cleaned)