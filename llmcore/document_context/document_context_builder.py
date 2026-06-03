from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
from llmcore.document_context.pdf_reader import PdfPageReader
from llmcore.summary_agent.summary_agent import SummaryAgent


class DocumentContextBuilder:

    def __init__(self, patient_id: str, notes_dir: str) -> None:
        self.patient_id = patient_id
        self.notes_dir = notes_dir
        self.reader = PdfPageReader()
        self.summary_agent = SummaryAgent()

    def _process_single_page(
        self,
        pdf_path: str,
        document_name: str,
        page_number: int,
        total_pages: int,
    ) -> Tuple[str, int, str]:
        base64_image = self.reader.extract_page_as_image(pdf_path, page_number)
        if not base64_image:
            print(f'Empty image for {document_name} page {page_number} — cannot summarise')
            raise ValueError(f'Empty image returned for {document_name} page {page_number}')
        
        summary = self.summary_agent.summarise_page(
            document_name=document_name,
            page_number=page_number,
            total_pages=total_pages,
            base64_image=base64_image,
        )
        return (document_name, page_number, summary)

    def _append_page_summary(
        self,
        lines: List[str],
        document_name: str,
        page_number: int,
        summary: str,
        current_doc: str | None,
    ) -> str:
        if document_name != current_doc:
            lines.append(f'## {document_name}')
            lines.append('')
            current_doc = document_name
        lines.append(f'### Page {page_number}')
        lines.append('')
        lines.append(summary)
        lines.append('')
        return current_doc

    def _format_document_context(self, page_summaries: List[Tuple[str, int, str]]) -> str:
        lines = ['# Clinical Notes Summary', '']
        current_doc = None
        for document_name, page_number, summary in sorted(page_summaries, key=lambda x: (x[0], x[1])):
            current_doc = self._append_page_summary(lines, document_name, page_number, summary, current_doc)
        return '\n'.join(lines).strip() + '\n'

    def _collect_pdf_page_jobs(self, pdf_files: List[str]) -> List[Tuple[str, str, int, int]]:
        jobs: List[Tuple[str, str, int, int]] = []
        for pdf_path in pdf_files:
            doc_name = Path(pdf_path).name
            try:
                total_pages = self.reader.get_page_count(pdf_path)
            except Exception as e:
                print(f'Could not read page count for {doc_name}: {e}')
                raise
            for page_num in range(1, total_pages + 1):
                jobs.append((pdf_path, doc_name, page_num, total_pages))
        return jobs

    def _process_pages_parallel(self, jobs: List[Tuple[str, str, int, int]]) -> List[Tuple[str, int, str]]:
        page_summaries: List[Tuple[str, int, str]] = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    self._process_single_page, 
                    pdf_path, 
                    doc_name, 
                    page_num, 
                    total_pages
                ): (doc_name, page_num)
                for pdf_path, doc_name, page_num, total_pages in jobs
            }
            for future in as_completed(futures):
                doc_name, page_num = futures[future]
                try:
                    page_summaries.append(future.result())
                except Exception as e:
                    print(f'Page summarization failed for {doc_name} page {page_num}: {e}')
                    raise
        return page_summaries

    def generate_document_context(self) -> Tuple[str, List[str]]:
        pdf_files = self.reader.list_pdf_files(self.notes_dir)
        if not pdf_files:
            print(f'No PDF files found in {self.notes_dir} for patient {self.patient_id}')
            raise FileNotFoundError(f'No PDF files found in {self.notes_dir} for patient {self.patient_id}')

        available_documents = [Path(p).name for p in pdf_files]
        print(f'''Building document context from {len(pdf_files)} documents 
            for patient {self.patient_id}: {available_documents}''')

        jobs = self._collect_pdf_page_jobs(pdf_files)
        page_summaries = self._process_pages_parallel(jobs)
        document_context = self._format_document_context(page_summaries)

        print(f'''Document context complete for patient {self.patient_id}
            {len(page_summaries)} pages processed''')
        return (document_context, available_documents)
