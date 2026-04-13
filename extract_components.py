"""
PDR Component Section Extractor — for IFAD Project Design Reports
Extracts the Components/Outcomes section and saves as [filename]_components.pdf

Strategy 1: Find it via the Table of Contents
Strategy 2: Scan pages for section title keywords (fallback)

Supports: English, French, Spanish, Arabic, Portuguese

Author: Purnima Porwal
Built for: IFAD Office of Development Effectiveness — taxonomy project (2026)
GitHub:    github.com/purnimaporwal/pdf-component-extractor
"""

# ─────────────────────────────────────────────────────
# PART 1: Import tools
# ─────────────────────────────────────────────────────
import os          # lets Python work with folders on your computer
import re          # lets Python search for patterns like page numbers
import pdfplumber  # reads text inside PDFs (the magnifying glass)
from pypdf import PdfReader, PdfWriter  # opens and creates PDF files


# ─────────────────────────────────────────────────────
# PART 2: Settings — only change BASE_FOLDER to match your computer
#         Everything else adjusts automatically.
# ─────────────────────────────────────────────────────

# ── CHANGE THIS ONE PATH TO MATCH YOUR COMPUTER ──────
# Mac / Linux users — use this format:
BASE_FOLDER = "/Users/purnimaporwal/Downloads/pdf-extractor"

# Windows users — uncomment this line and comment out the one above:
# BASE_FOLDER = r"C:\Users\yourname\Downloads\pdf-extractor"
# ─────────────────────────────────────────────────────

INPUT_FOLDER  = os.path.join(BASE_FOLDER, "input")   # folder where you put your PDR PDFs
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "output")  # folder where results will be saved


# Words that mean "Component section STARTS here"
# The script checks ALL of these across all languages simultaneously
COMPONENT_KEYWORDS = [
    # English — specific headings (with and without colon)
    "Outcome",
    "Programme Outcomes",
    "component 1:",
    "component 2:",
    "component 3:",
    "component 1 ",       # no colon version
    "component 2 ",       # no colon version
    "component 3 ",       # no colon version
    "components/outcomes",
    "k. components",
    # French — specific headings (with colon, space+colon, no colon)
    "composante 1:",
    "composante 2:",
    "composante 3:",
    "composante1:",
    "composante2:",
    "composante3:",
    "composante 1 :",     # space before colon version
    "composante 2 :",
    "composante 3 :",
    "composantes et résultats",
    "d. composantes",
    "volet 1",
    "volet 2",
    "volet 3",
    # Generic fallbacks
    "component",
    "composante",
    "composantes",
    "volet",
    "volets",
    "sous-composante",
    "les composantes",
    # Spanish
    "componente 1",
    "componente 2",
    "componente",
    "componentes",
    # Arabic
    "مكون",
    "المكونات",
    # Portuguese
    "componentes do projeto",
]

# Words that mean "Component section has ENDED, stop here"
# These are section titles that come AFTER Components in PDR documents
END_SECTION_KEYWORDS = [
    # English
    "lessons learned",
    "l. lessons",
    "project implementation",
    "iii. project",
    "implementation arrangements",
    "annex",
    "appendix",
    "procurement",
    "sustainability",
    "innovation",
    "financing",
    # French
    "mise en oeuvre",
    "mise en œuvre",
    "enseignements",
    "annexe",
    "passation des marchés",
    "durabilité",
    "dispositifs",
    "financement",
    "exécution du projet",
    "iii. exécution",
    # Spanish
    "ejecución",
    "anexo",
    "lecciones aprendidas",
    "sostenibilidad",
    # Arabic
    "ملحق",
    "التنفيذ",
    # Portuguese
    "execução",
    "lições aprendidas",
]

MIN_PAGES = 3    # warn if fewer than 3 pages found (probably something went wrong)
MAX_PAGES = 30   # never extract more than 30 pages (safety limit)


# ─────────────────────────────────────────────────────
# HELPER 1: Find where the main body of the report starts
# ─────────────────────────────────────────────────────

def find_main_body_start(pdf):
    """
    Plain English: Many PDRs have two sets of page numbers:
      - Front matter: Cover, TOC, Acronyms (first ~15 pages)
      - Main body: The actual report starting at printed page 1
    This finds the main body by looking for the FIRST printed "1"
    after page 15 — avoiding the front matter and appendices.
    """
    total = len(pdf.pages)
    main_body_start = 0  # default: treat whole document as main body

    # Skip first 15 pages (front matter) — look for first printed "1" after that
    for i in range(15, total):
        text = pdf.pages[i].extract_text() or ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # Check footer (last 3 lines) and header (first 2 lines)
        footer_header = lines[-3:] + lines[:2] if lines else []
        for line in footer_header:
            if line == "1":
                main_body_start = i
                print(f"     Main body detected starting at PDF page {i + 1}")
                return main_body_start  # stop at first match after front matter

    print("     Could not detect main body start — using page 1 as default")
    return main_body_start


# ─────────────────────────────────────────────────────
# HELPER 2: Convert a printed page number to actual PDF page index
# ─────────────────────────────────────────────────────

def find_pdf_page_for_printed_number(pdf, printed_number, total_pages, search_from=0):
    """
    Plain English: Looks for the page where the footer/header shows
    exactly the printed page number we want. Starts from the main body.
    """
    search_start = search_from
    search_end   = min(total_pages, search_from + printed_number + 30)

    for i in range(search_start, search_end):
        text = pdf.pages[i].extract_text() or ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        footer_header = lines[-3:] + lines[:2] if lines else []
        for line in footer_header:
            if line == str(printed_number):
                return i

    return None


# ─────────────────────────────────────────────────────
# PART 3: Strategy 1 — Find the section via Table of Contents
# ─────────────────────────────────────────────────────

def find_via_table_of_contents(pdf_path):
    """
    Plain English: Open the PDF, find the Table of Contents page,
    look for the "Component" line, read the page number next to it,
    find where the next section starts, and return both page numbers.
    """
    print("  [Strategy 1] Searching Table of Contents...")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        # Step A: Find the main body start (handles dual page numbering)
        main_body_start = find_main_body_start(pdf)

        # Step B: Find the Table of Contents (usually in first 10 pages)
        toc_lines = []
        toc_found = False

        for i in range(min(10, total_pages)):
            text  = pdf.pages[i].extract_text() or ""
            lower = text.lower()

            # Check if this page looks like a TOC
            is_toc = (
                "table of contents" in lower or
                "table des matieres" in lower or
                "table des matières" in lower or
                "tabla de contenidos" in lower or
                "indice" in lower or
                ("contents" in lower and lower.count("..") >= 2) or
                ("mati" in lower and lower.count("..") >= 2)
            )

            if is_toc:
                toc_found = True
                # Collect lines from this page + next 3 pages
                # (TOC sometimes spans multiple pages)
                for j in range(i, min(i + 4, total_pages)):
                    page_text = pdf.pages[j].extract_text() or ""
                    toc_lines.extend(page_text.splitlines())
                print(f"     Found Table of Contents on PDF page {i + 1}")
                break

        if not toc_found:
            print("     No Table of Contents found.")
            return None

        # Step C: Find the Component keyword in the TOC and read the page number
        component_page_num = None
        component_line_idx = None

        for idx, line in enumerate(toc_lines):
            lower_line = line.lower()
            if any(kw in lower_line for kw in COMPONENT_KEYWORDS):
                # Read the last number on that line — that's the page number
                numbers = re.findall(r'\d+', line)
                if numbers:
                    component_page_num = int(numbers[-1])
                    component_line_idx = idx
                    print(f"     Found Component entry in TOC → printed page {component_page_num}")
                    break

        if component_page_num is None:
            print("     Component section not found in Table of Contents.")
            return None

        # Step D: Find the NEXT section's page number (where to stop)
        next_section_page_num = None
        if component_line_idx is not None:
            for line in toc_lines[component_line_idx + 1:]:
                lower_line = line.lower()
                if any(kw in lower_line for kw in END_SECTION_KEYWORDS):
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        next_section_page_num = int(numbers[-1])
                        print(f"     Next section starts at printed page {next_section_page_num}")
                        break

        # Step E: Convert printed page numbers → actual PDF page positions
        # NOTE: This stays inside the "with pdfplumber" block so it can use "pdf"

        # Find the START page
        start_index = find_pdf_page_for_printed_number(
            pdf, component_page_num, total_pages, search_from=main_body_start
        )
        if start_index is None:
            start_index = main_body_start + component_page_num - 1
            print("     (Used fallback for start page)")

        # Find the END page
        if next_section_page_num:
            end_index = find_pdf_page_for_printed_number(
                pdf, next_section_page_num, total_pages, search_from=main_body_start
            )
            if end_index is None:
                end_index = main_body_start + next_section_page_num - 1
                print("     (Used fallback for end page)")
            else:
                # Include the transition page because the last component
                # often shares a page with the start of the next section
                end_index = end_index + 1
                print(f"     (End page found at PDF page {end_index})")
        else:
            end_index = min(start_index + MAX_PAGES, total_pages)
            print("     (No end section in TOC — using page limit)")

        if end_index <= start_index:
            print("     Page range does not make sense. Skipping.")
            return None

        print(f"     Will extract PDF pages {start_index + 1} to {end_index} "
              f"({end_index - start_index} pages total)")
        return (start_index, end_index)


# ─────────────────────────────────────────────────────
# PART 4: Strategy 2 — Scan every page (backup plan)
# ─────────────────────────────────────────────────────

def find_via_keyword_scan(pdf_path):
    """
    Plain English: If Strategy 1 failed, read every page one by one.
    When a page heading contains a Component keyword, that is the start.
    When the next major section heading appears, that is the end.
    Starts from PDF page 3 to skip cover and TOC only.
    """
    print("  [Strategy 2] Scanning all pages for Component heading...")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        start_index = None
        end_index   = None

        # Start from page 3 (index 2) — skips cover and TOC only
        for i in range(2, total_pages):
            text  = pdf.pages[i].extract_text() or ""
            lines = text.splitlines()

            # Only look at top 8 lines (headings are always at the top)
            top_text = " ".join(lines[:8]).lower()

            if start_index is None:
                # Look for Component section START
                for kw in COMPONENT_KEYWORDS:
                    if kw in top_text:
                        matching_lines = [
                            l for l in lines[:8]
                            if kw in l.lower() and len(l.strip()) < 80
                        ]
                        if matching_lines:
                            start_index = i
                            print(f"     Found Component section on PDF page {i + 1}")
                            break
            else:
                # Already found start — look for END
                pages_so_far = i - start_index
                for kw in END_SECTION_KEYWORDS:
                    if kw in top_text:
                        end_index = i
                        print(f"     Section ends before PDF page {i + 1}")
                        break
                if end_index is not None:
                    break
                if pages_so_far >= MAX_PAGES:
                    end_index = i + 1
                    print(f"     Reached {MAX_PAGES} page limit. Stopping.")
                    break

        if start_index is None:
            print("     Component section not found by scanning either.")
            return None

        if end_index is None:
            end_index = min(start_index + MAX_PAGES, total_pages)

        print(f"     Will extract PDF pages {start_index + 1} to {end_index} "
              f"({end_index - start_index} pages total)")
        return (start_index, end_index)


# ─────────────────────────────────────────────────────
# PART 5: Cut and save the pages as a new PDF
# ─────────────────────────────────────────────────────

def save_pages_as_pdf(source_pdf_path, start_index, end_index, output_path):
    """
    Plain English: Take the original PDF, copy only the pages we want,
    and save them as a brand new PDF file in the output folder.
    The original file is never modified.
    """
    reader = PdfReader(source_pdf_path)
    writer = PdfWriter()

    for i in range(start_index, end_index):
        writer.add_page(reader.pages[i])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


# ─────────────────────────────────────────────────────
# PART 6: Process one PDF file end to end
# ─────────────────────────────────────────────────────

def process_one_pdf(pdf_path):
    """
    Plain English: This handles ONE PDF file from start to finish.
    Tries Strategy 1 (TOC), falls back to Strategy 2 (Keyword Scan).
    Saves result as [filename]_components.pdf in the output folder.
    """
    filename        = os.path.basename(pdf_path)
    name_no_ext     = os.path.splitext(filename)[0]
    output_filename = f"{name_no_ext}_components.pdf"
    output_path     = os.path.join(OUTPUT_FOLDER, output_filename)

    print(f"\n{'─' * 60}")
    print(f"  File: {filename}")
    print(f"{'─' * 60}")

    # Try Strategy 1 first
    result = find_via_table_of_contents(pdf_path)

    # If Strategy 1 failed, try Strategy 2
    if result is None:
        result = find_via_keyword_scan(pdf_path)

    # If both failed, skip this file
    if result is None:
        print("  Could not find Component section. Skipping.")
        print("  Use manual_extract.py to specify the page range manually.")
        return

    start_index, end_index = result
    page_count = end_index - start_index

    # Warn if result looks unusual
    if page_count < MIN_PAGES:
        print(f"  Warning: Only {page_count} pages — please check the output file!")
    elif page_count > MAX_PAGES:
        print(f"  Warning: {page_count} pages — please check the output file!")

    save_pages_as_pdf(pdf_path, start_index, end_index, output_path)
    print(f"  Done → {output_path}  ({page_count} pages extracted)")


# ─────────────────────────────────────────────────────
# PART 7: Main — processes all PDFs in the input folder
# ─────────────────────────────────────────────────────

def main():
    """
    Plain English: Finds ALL PDFs in the input folder
    and processes them one by one.
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Find all PDF files in the input folder
    pdf_files = [
        f for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"\n No PDF files found in '{INPUT_FOLDER}/' folder.")
        print(f" Please put your PDR PDFs there and run again.\n")
        return

    print(f"\n Found {len(pdf_files)} PDF file(s) to process.")

    for filename in sorted(pdf_files):
        pdf_path = os.path.join(INPUT_FOLDER, filename)
        process_one_pdf(pdf_path)

    print(f"\n{'═' * 60}")
    print(f"  All done! Check your output folder:")
    print(f"  {OUTPUT_FOLDER}")
    print(f"{'═' * 60}\n")


# This line means: only run when YOU start it manually
# (not accidentally when imported by another script)
if __name__ == "__main__":
    main()
