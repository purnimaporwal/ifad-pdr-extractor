# IFAD PDR Component Extractor 📄

A Python tool that automatically extracts the Components/Outcomes section from IFAD Project Design Reports.

**Why I built this · How it works · How to use it · What I learned**

---

## The problem it solves

At IFAD, our taxonomy project required reviewing 70+ Project Design Reports. Each one was 200 pages or more, written in English, French, Spanish, or Arabic. The section we needed (the Components/Outcomes section) was buried at a different page number in every single file.

My consultant mentioned that Python had been tried before for this and had not worked well. The plan was to do it manually.

I said I would try to make it work.

---

## How I built it

I worked through it iteratively with Claude. I tried the automatic approach first, reading the Table of Contents, finding the page numbers, and extracting the right pages. It worked on some files but missed pages in others.

So I suggested trying a manual backup approach. Instead of automatically finding pages, you tell the tool the start and end page numbers directly. That worked better. I kept testing on different IFAD PDR files and refining until both approaches were reliable.

The problem design, the two-strategy approach, and all the decisions about what to build were mine. Claude helped me write Python syntax, which I was still learning at the time.

When the tool was working, my consultant said:

> *"Your work has been a great help to us. I'm sure when we move to other replenishment cycles, your Python code will bring even greater value."*

I completed a formal Python for Data Science workshop at Stellenbosch University on 1 April 2026, right after building this. The workshop gave me proper vocabulary and structure for things I had already been doing by instinct.

---

## What the tool does

```
Input:   A folder of IFAD PDR PDF files (any language)
Output:  One extracted PDF per file — Components section only
```

**Strategy 1 — Table of Contents detection (automatic)**

Finds the TOC page, reads the page number next to the Components entry, handles the mismatch between printed page numbers and actual PDF page positions, and identifies where the next section starts so it knows where to stop. Works across all four languages at once.

**Strategy 2 — Full keyword scan (fallback)**

If the TOC approach fails, it scans every page looking for the Components section headings near the top of the page. Stops when an end-section keyword appears. Same multilingual support.

**Manual backup tool**

For files where both automatic strategies get the wrong pages. You specify the printed start and end page numbers yourself, and the tool maps those to actual PDF positions and extracts cleanly.

---

## Language support

| Language | Keywords detected |
|---|---|
| English | Component 1/2/3, Outcomes, Programme Outcomes |
| French | Composante 1/2/3, Volet 1/2/3, Composantes et résultats |
| Spanish | Componente 1/2/3 |
| Arabic | مكون, المكونات |

---

## Files in this repository

```
pdf-component-extractor/
│
├── extract_components.py    # Main tool — processes entire folder automatically
├── manual_extract.py        # Backup tool — specify page range manually
└── requirements.txt         # Python dependencies (2 libraries)
```

---

## How to use it

### Install dependencies
```bash
pip install -r requirements.txt
```

### Automatic extraction

Open `extract_components.py` and change one line at the top:

```python
# Mac/Linux:
BASE_FOLDER = "/Users/yourname/Downloads/pdf-component-extractor"

# Windows — uncomment this line instead:
# BASE_FOLDER = r"C:\Users\yourname\Downloads\pdf-component-extractor"
```

Put your PDR PDFs in the `input/` folder inside that base folder, then run:

```bash
python3 extract_components.py
```

Extracted sections appear in `output/` as `[filename]_components.pdf`

### Manual extraction (when automatic gets wrong pages)

Open `manual_extract.py` and change four settings at the top:

```python
BASE_FOLDER = "/Users/yourname/Downloads/ifad-pdr-extractor"
INPUT_FILE  = "your_pdr_filename.pdf"   # filename only, no folder prefix
START_PAGE  = 14                         # printed page number where Components starts
END_PAGE    = 28                         # printed page number where Components ends
```

Then run:

```bash
python3 manual_extract.py
```
---

## The trickiest part: dual page numbering

PDR documents have two sets of page numbers. The front matter (cover page, table of contents, acronyms list) is often unnumbered or uses Roman numerals. Then the main body restarts at printed page 1.

If you just use the printed page number directly, you get the wrong pages. The current tool solves this by scanning for the first "1" in page headers or footers after page 15, which is where the main body actually starts.

```python
def find_main_body_start(pdf):
    # Skip first 15 pages (front matter)
    # Look for first printed "1" in footer/header after that
    for i in range(15, total):
        footer_header = lines[-3:] + lines[:2]
        if "1" in footer_header:
            return i   # main body starts here
```
**Known issue with this approach:** In some files, the correct "1" is skipped, and the function returns a very large, incorrect page number. A more robust approach is in development: instead of scanning for page numbers, the improved version will locate the exact section title from the TOC and search the full document body for that string directly, avoiding page number detection entirely. This also handles cases where the TOC contains the full section title, which can then be used to set both the start and end boundaries precisely.

---
## Known limitations and workarounds

The automatic tool works well for most PDR files, but there are cases where it struggles.

**PDFs with page numbers formatted as "3 of 28" or "3/28"**

The tool looks for a standalone page number and cannot read this format, so automatic page detection fails for these files. The manual extraction tool works reliably for these cases.

**Section title position**

An earlier version of the tool only searched the first 8 rows of each page for section headings. This constraint has been removed. The tool now searches the full page, which handles files where section titles appear lower down.

**End-section keywords**

The current end-section keyword list is broad. Words like "innovation" can appear within a Component paragraph and incorrectly trigger an early cutoff. Narrower, more specific end-section patterns are being tested and will replace the current list in a future update.

**When even the manual tool did not work**

A small number of files have formatting issues that make Python extraction unreliable regardless of the approach. For those using the print/export function in the PDF reader directly, selecting only the required pages produces the same output. Not elegant, but it
works.

The tool is most reliable on standard IFAD PDR files from replenishment cycles 9-13 with clean footer page numbers. Earlier project files may require adaptation of the detection logic.
---

## Requirements

```
pdfplumber >= 0.9.0
pypdf >= 3.0.0
Python >= 3.8
```
---

## A note on AI-assisted development

I want to be transparent about this because I think it matters.

I used Claude to help build these scripts while I was still learning Python. The problem design, the two-strategy approach, the decision to add a manual backup tool, and the multilingual keyword structure were all my decisions based on testing and understanding what was failing. Claude helped me write the Python to implement them. 

I think using AI tools well is a legitimate skill worth naming rather than hiding. Knowing when to use them, how to direct them, and how to check what they produce is something I am actively developing alongside my technical skills.

---

## Built for: IFAD Office of Development Effectiveness, Rome — Impact Assessment Taxonomy Project (2026)

**Status:** Active development — improvements to TOC-based section detection and keyword matching in progress.

Part of my research portfolio: [github.com/purnimaporwal](https://github.com/purnimaporwal)

*Author: Purnima Porwal | porwal.purnima18@gmail.com*
