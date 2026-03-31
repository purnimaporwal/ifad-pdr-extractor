"""
Manual PDF Page Extractor — Simple Backup Tool
Use this when the automatic extract_components.py gets wrong pages.
Just change the 4 settings below and run it.

Author: Purnima Porwal
Built for: IFAD Office of Development Effectiveness — taxonomy project (2026)
GitHub:    github.com/purnimaporwal/ifad-pdr-extractor
"""

import os
import pdfplumber
from pypdf import PdfReader, PdfWriter


# ─────────────────────────────────────────────
# CHANGE THESE 4 SETTINGS FOR EACH FILE
# ─────────────────────────────────────────────

# ── CHANGE THIS ONE PATH TO MATCH YOUR COMPUTER ──────
# Mac / Linux users — use this format:
BASE_FOLDER = "/Users/purnimaporwal/Downloads/pdf-extractor"

# Windows users — uncomment this line and comment out the one above:
# BASE_FOLDER = r"C:\Users\yourname\Downloads\pdf-extractor"
# ─────────────────────────────────────────────────────

INPUT_FILE  = "RAPID Final Design April 2018 final copy.pdf"  # filename only — no folder prefix
# ↑ Put the exact filename here (copy paste from your input folder)
# ↑ Just the filename — do NOT include "input/" here

START_PAGE  = 11  # change start page (printed page number)
# ↑ The PRINTED page number where Components section starts
# (the number you see printed on the page itself, like in the TOC)

END_PAGE    = 22  # change end page (printed page number)
# ↑ The PRINTED page number where Components section ends
# (the LAST page you want — this page WILL be included)


# ─────────────────────────────────────────────
# NO CHANGES BELOW THIS LINE
# ─────────────────────────────────────────────

INPUT_PATH    = os.path.join(BASE_FOLDER, "input", INPUT_FILE)
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "output")


def find_pdf_page_index(pdf_path, printed_number):
    """
    Plain English: Searches the PDF footer/header to find which
    actual PDF page corresponds to the printed page number you gave.
    Returns the 0-based page index.
    """
    total = len(PdfReader(pdf_path).pages)

    for i in range(total):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text  = pdf.pages[i].extract_text() or ""
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                footer_header = lines[-4:] + lines[:2] if lines else []
                for line in footer_header:
                    if line == str(printed_number):
                        return i
        except:
            pass

    # Fallback: page number not found in footer —
    # use the number directly (minus 1 for 0-based index)
    print(f"  Warning: Could not find printed page {printed_number} in footers.")
    print(f"  Using page {printed_number} directly as position.")
    return printed_number - 1


def manual_extract():
    """
    Plain English: Extracts a specific page range from one PDF and saves
    it as a new file. The original PDF is never modified.
    """
    # Check the input file actually exists before doing anything
    if not os.path.exists(INPUT_PATH):
        print(f"\n File not found: {INPUT_PATH}")
        print(f" Check that BASE_FOLDER and INPUT_FILE are correct!")
        return

    filename     = os.path.basename(INPUT_PATH)
    name_no_ext  = os.path.splitext(filename)[0]
    output_file  = os.path.join(OUTPUT_FOLDER, f"{name_no_ext}_components.pdf")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print(f"\n File:       {filename}")
    print(f" Start page: {START_PAGE} (printed)")
    print(f" End page:   {END_PAGE} (printed)")

    # Find the actual PDF page positions for our printed page numbers
    print(f"\n Searching for pages in PDF...")
    start_index = find_pdf_page_index(INPUT_PATH, START_PAGE)
    end_index   = find_pdf_page_index(INPUT_PATH, END_PAGE)

    print(f" Start → PDF page {start_index + 1}")
    print(f" End   → PDF page {end_index + 1}")

    # Extract the pages and save as a new PDF
    reader = PdfReader(INPUT_PATH)
    writer = PdfWriter()

    # end_index + 1 because we INCLUDE the end page
    for i in range(start_index, end_index + 1):
        writer.add_page(reader.pages[i])

    page_count = end_index - start_index + 1

    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"\n Done → {output_file}  ({page_count} pages extracted)")
    print(f" Check your output folder!\n")


if __name__ == "__main__":
    manual_extract()
