import re
import unicodedata

def safe_filename(filename: str):
    filename = unicodedata.normalize("NFC", filename)
    return re.sub(r'[^\w\-.]', '_', filename)