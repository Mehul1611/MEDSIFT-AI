import base64
import fitz
from pathlib import Path
from PyPDF2 import PdfReader
from typing import List


class PdfPageReader:

    def list_pdf_files(self, notes_dir: str) -> List[str]:
        try:
            notes_path = Path(notes_dir)
            return sorted([str(p) for p in notes_path.glob('*.pdf')])
        except Exception as e:
            print(f'Failed to list PDF files in {notes_dir}: {e}')
            raise e

    def get_page_count(self, pdf_path: str) -> int:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                return len(reader.pages)
        except Exception as e:
            print(f'Failed to get page count for {pdf_path}: {e}')
            raise e

    def _extract_pages_raw_text(self, pdf_path: str, start_page: int, end_page: int) -> str:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                total = len(reader.pages)
                start_idx = max(0, start_page - 1)
                end_idx = min(total, end_page)
                pages_text = []
                for i in range(start_idx, end_idx):
                    text = reader.pages[i].extract_text() or ''
                    pages_text.append(f'[Page {i + 1}]\n{text}')
                return '\n\n'.join(pages_text)
        except Exception as e:
            print(f'Failed to extract text from {pdf_path} (pages {start_page}-{end_page}): {e}')
            raise e

    def extract_page_text(self, pdf_path: str, start_page: int, end_page: int) -> str:
        try:
            return self._extract_pages_raw_text(pdf_path, start_page, end_page)
        except Exception as e:
            print(f'Error extracting text from {pdf_path}: {e}')
            raise e

    def extract_page_as_image(self, pdf_path: str, page_num: int) -> str:
        try:
            doc = fitz.open(pdf_path)
            page_idx = page_num - 1
            if page_idx < 0 or page_idx >= len(doc):
                doc.close()
                raise ValueError(f'Page {page_num} is out of range for {pdf_path} ({len(doc)} pages)')
            page = doc[page_idx]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes('png')
            doc.close()
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            print(f'Error converting page {page_num} to image from {pdf_path}: {e}')
            raise e
