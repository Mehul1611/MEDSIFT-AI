from functools import partial
from pathlib import Path
from langchain.tools import StructuredTool
from llmcore.document_context.pdf_reader import PdfPageReader
from llmcore.tools.tool_schemas.pdf_tool_schema import ReadPdfSchema

_READ_PDF_TOOL_NAME = 'READ_PDF_TOOL'
_READ_PDF_TOOL_DESCRIPTION = "Use this tool to read the raw text content from specific pages of a patient's clinical PDF document. Use it only when a page summary is unclear, when you need to verify a high-risk clinical fact, or when two summaries conflict and you need the original source text. Do not use this for every page — page-wise summaries are your primary source."

def _read_pdf_pages(reader: PdfPageReader, notes_dir: str, document_name: str, start_page: int, end_page: int) -> str:
    pdf_path = str(Path(notes_dir) / document_name)
    if not Path(pdf_path).exists():
        print(f"Document '{document_name}' not found in {notes_dir}")
        raise FileNotFoundError(f"Document '{document_name}' not found in {notes_dir}")
    return reader.extract_page_text(pdf_path, start_page, end_page)

def get_read_pdf_tool(notes_dir: str) -> StructuredTool:
    reader = PdfPageReader()
    configured_fn = partial(_read_pdf_pages, reader, notes_dir)
    return StructuredTool.from_function(func=configured_fn, name=_READ_PDF_TOOL_NAME, description=_READ_PDF_TOOL_DESCRIPTION, args_schema=ReadPdfSchema)
