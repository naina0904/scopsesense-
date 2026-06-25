import os
import re

class SRSParser:

    ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf", ".xlsx"}

    def _sanitize_text(self, text: str) -> str:
        """Remove control characters and ensure printable output."""
        return re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", " ", text)

    # =================================================
    # PARSE SRS DOCUMENT
    # =================================================

    def parse(

        self,

        file_path
    ):
        filename = os.path.basename(file_path)
        # Extract original filename from the stored file format: srs_<uuid>_<original_filename>
        # uuid is 32 hex chars, srs_ is 4 chars, _ is 1 char, total 37 chars prefix.
        if filename.startswith("srs_") and len(filename) > 37:
            original_filename = filename[37:]
        else:
            original_filename = filename

        # Determine file extension and extract plain text accordingly
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 1. Extension Whitelisting Protection
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {ext}. Allowed types are: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # 2. Binary Masquerading Protection (prevent binary file masquerading as txt/md)
        if ext in {".txt", ".md"}:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk or chunk.startswith(b"PK\x03\x04"):
                    raise ValueError("Uploaded file appears to be binary but has a text extension.")

        parser_selected = "Text (UTF-8 / latin-1 fallback)"
        if ext == ".docx":
            parser_selected = "docx2txt"
        elif ext == ".pdf":
            parser_selected = "PyPDF2"
        elif ext == ".xlsx":
            parser_selected = "openpyxl"
        elif ext == ".md":
            parser_selected = "Text (Markdown)"
        elif ext == ".txt":
            parser_selected = "Text (Plain)"

        print(f"[SRSParser] Original filename : {original_filename}")
        print(f"[SRSParser] Saved filename    : {filename}")
        print(f"[SRSParser] Detected extension: {ext}")
        print(f"[SRSParser] Parser selected   : {parser_selected}")

        if ext == ".docx":
            try:
                import docx2txt
                raw_content = docx2txt.process(file_path)
            except Exception as e:
                raise ValueError(f"Failed to parse DOCX file: {e}")
        elif ext == ".pdf":
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                raw_content = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                raise ValueError(f"Failed to parse PDF file: {e}")
        elif ext == ".xlsx":
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
                rows = []

                for ws in wb.worksheets:
                    sheet_name = (ws.title or "").strip()
                    sheet_content = [f"## Sheet: {sheet_name}"]
                    
                    ws_rows = list(ws.iter_rows(values_only=True))
                    for row_idx, row in enumerate(ws_rows):
                        # Construct a list of stringified values, keeping empty cells to preserve columns
                        cells = [str(c).strip() if c is not None and str(c).strip().lower() != "none" else "" for c in row]
                        
                        # Check if the row is entirely empty
                        if not any(c for c in cells if c):
                            continue
                        
                        # Format as markdown table row
                        row_str = "| " + " | ".join(cells) + " |"
                        sheet_content.append(row_str)
                        
                        # If this is the first data row (potential header), insert a separator
                        if len(sheet_content) == 2:
                            num_cols = len(cells)
                            separator = "|" + "|".join(["---"] * num_cols) + "|"
                            sheet_content.append(separator)

                    if len(sheet_content) > 1:
                        rows.append("\n".join(sheet_content))

                raw_content = "\n\n".join(rows)
                print(f"[SRSParser] XLSX extracted {len(rows)} sheets as Markdown tables.")
            except Exception as e:
                raise ValueError(f"Failed to parse XLSX file: {e}")
        else:
            # Default: read as UTF-8 text, fallback to latin-1 on decode error
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    raw_content = file.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as file:
                    raw_content = file.read()

        # 3. Control Character Sanitization Protection
        raw_content = self._sanitize_text(raw_content)

        lines = raw_content.split("\n")

        cleaned_lines = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            cleaned_lines.append(line)

        return {

            "raw_content":
                raw_content,

            "cleaned_lines":
                cleaned_lines
        }