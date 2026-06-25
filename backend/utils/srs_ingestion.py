# backend/utils/srs_ingestion.py
"""Utility module for safe extraction of text from supported SRS file formats.
Supported extensions: .txt, .md, .docx, .pdf, .xlsx, .csv
The function returns a path to a cleaned UTF-8 text file suitable for downstream processing.
"""
import os
import re
from typing import List

ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".xlsx", ".csv"}


def _sanitize_text(text: str) -> str:
    """Remove control characters and ensure printable output."""
    # Replace null bytes and other non-printable characters
    return re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", " ", text)


def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from a supported SRS file.

    Parameters
    ----------
    file_path: str
        Absolute path to the uploaded file.

    Returns
    -------
    str
        Path to a temporary ``.txt`` file containing the extracted text.
    """
    if not os.path.isabs(file_path):
        raise ValueError("File path must be absolute.")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed types are: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # Extraction logic per type
    if ext in {".txt", ".md"}:
        
        # ---------------------------------------------
        # INGESTION VALIDATION: BINARY DETECTION
        # ---------------------------------------------
        # Prevent binary files (e.g. ZIP/DOCX masquerading as TXT)
        # from bypassing normal parsers and corrupting downstream payload.
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk or chunk.startswith(b"PK\x03\x04"):
                raise ValueError("Uploaded file appears to be binary but has a text extension.")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    elif ext == ".docx":
        import docx2txt
        text = docx2txt.process(file_path)
    elif ext == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages: List[str] = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n".join(pages)
    elif ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        rows: List[str] = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                # Convert each cell to string, ignore None
                cells = [str(cell) for cell in row if cell is not None]
                if cells:
                    rows.append("\t".join(cells))
        text = "\n".join(rows)
    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)
    else:
        # Fallback – should never happen due to earlier check
        raise ValueError("Unhandled file extension")

    # Sanitize and write to a new temporary txt file
    clean_text = _sanitize_text(text)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_dir = os.path.dirname(file_path)
    out_path = os.path.join(out_dir, f"{base_name}_clean.txt")
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write(clean_text)
    return out_path
