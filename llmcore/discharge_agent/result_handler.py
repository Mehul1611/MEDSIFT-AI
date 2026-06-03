import json
import os
from pathlib import Path
from typing import Any
from llmcore.constants import LLMConstants
from llmcore.discharge_agent.output_templates.output_templates import render_markdown
from llmcore.discharge_agent.patient_state import PatientState


class ResultHandler:

    def __init__(self, patient_id: str) -> None:
        self.patient_id = patient_id
        self.output_dir = Path(LLMConstants.OUTPUT_BASE_DIR) / patient_id
        os.makedirs(self.output_dir, exist_ok=True)

    def _save_text_file(self, content: str, filename: str) -> Path:
        path = self.output_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Saved {filename} at {path}')
        return path

    def _save_json_file(self, data: dict[str, Any], filename: str) -> Path:
        path = self.output_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f'Saved {filename} at {path}')
        return path

    def save_results(
        self,
        patient: PatientState,
        writer_output: dict[str, Any],
        structured_plan: str,
        document_context: str,
        planning_trace: str,
    ) -> PatientState:
        try:
            self._save_text_file(document_context, 'document_context.md')
            self._save_text_file(structured_plan, 'structured_plan.md')
            self._save_text_file(planning_trace, 'planning_trace.md')
            self._save_json_file(writer_output, 'discharge_summary.json')
            md_content = render_markdown(writer_output)
            self._save_text_file(md_content, 'discharge_summary.md')
            patient['output'] = writer_output
            patient['output_dir'] = str(self.output_dir)
            return patient
        except Exception as e:
            print(f'Failed to save results for patient {self.patient_id}: {e}')
            raise
