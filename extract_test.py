import sys
from pathlib import Path

import pymupdf as fitz
OUT = Path(__file__).parent / "extract_test_output.txt"


def count(text, lo, hi):
    return sum(1 for c in text if lo <= ord(c) <= hi)


pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"File: {pdf_path}\nPages: {len(doc)}\n\n")
    for i, page in enumerate(doc):
        text = page.get_text()
        n = len(text.strip())
        arabic = count(text, 0x0600, 0x06FF)   # normal Urdu/Arabic letters
        presform = count(text, 0xFB50, 0xFDFF) + count(text, 0xFE70, 0xFEFF)  # unshaped glyph forms
        latin = count(text, 0x41, 0x7A)
        f.write(f"--- Page {i+1}: chars={n} urdu={arabic} presentation_forms={presform} latin={latin}\n")
        if i < 3:
            f.write(text[:400].strip() + "\n")
        f.write("\n")

print("Done. Open", OUT)