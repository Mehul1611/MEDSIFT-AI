from typing import Any, List, Tuple
from llmcore.discharge_agent.patient_state import PatientState
from llmcore.discharge_agent.result_handler import ResultHandler
from llmcore.document_context.document_context_builder import DocumentContextBuilder
from llmcore.planning_agent.planning_agent import PlanningAgent
from llmcore.writer_agent.writer_agent import WriterAgent


class DischargeSummaryAgent:

    def __init__(self, patients: List[PatientState]) -> None:
        self.patients = patients

    def _build_document_context(self, patient: PatientState) -> Tuple[str, List[str]]:
        patient_id = patient.get('patient_id')
        try:
            builder = DocumentContextBuilder(patient_id=patient_id, notes_dir=patient.get('source_notes_dir'))
            document_context, available_documents = builder.generate_document_context()
            patient['document_context'] = document_context
            return document_context, available_documents
        except Exception as e:
            print(f'Document context failed for patient {patient_id}: {e}')
            raise

    def _run_planning_agent(
        self,
        patient: PatientState,
        document_context: str,
        available_documents: List[str],
    ) -> Tuple[str, str]:
        patient_id = patient.get('patient_id')
        try:
            planning_agent = PlanningAgent(patient_id=patient_id, notes_dir=patient.get('source_notes_dir'))
            structured_plan, planning_trace = planning_agent.invoke_planning_agent(
                document_context=document_context,
                available_documents=available_documents,
            )
            patient['structured_plan'] = structured_plan
            return structured_plan, planning_trace
        except Exception as e:
            print(f'Planning agent failed for patient {patient_id}: {e}')
            raise

    def _run_writer_agent(self, patient: PatientState, structured_plan: str) -> dict[str, Any]:
        patient_id = patient.get('patient_id')
        try:
            writer_agent = WriterAgent()
            return writer_agent.invoke_writer_agent(structured_plan=structured_plan)
        except Exception as e:
            print(f'Writer agent failed for patient {patient_id}: {e}')
            raise

    def _save_patient_results(
        self,
        patient: PatientState,
        writer_output: dict[str, Any],
        structured_plan: str,
        document_context: str,
        planning_trace: str,
    ) -> PatientState:
        patient_id = patient.get('patient_id')
        try:
            result_handler = ResultHandler(patient_id=patient_id)
            return result_handler.save_results(
                patient=patient,
                writer_output=writer_output,
                structured_plan=structured_plan,
                document_context=document_context,
                planning_trace=planning_trace,
            )
        except Exception as e:
            print(f'Result save failed for patient {patient_id}: {e}')
            raise

    def _run_single_patient(self, patient: PatientState) -> PatientState:
        patient_id = patient.get('patient_id')
        print(f'Starting discharge analysis for patient {patient_id}')

        document_context, available_documents = self._build_document_context(patient)
        print(f'Document context generation complete for patient {patient_id}')

        structured_plan, planning_trace = self._run_planning_agent(patient, document_context, available_documents)
        print(f'Planning agent complete for patient {patient_id}')

        writer_output = self._run_writer_agent(patient, structured_plan)
        print(f'Writer agent complete for patient {patient_id}')

        patient = self._save_patient_results(patient, writer_output, structured_plan, document_context, planning_trace)
        patient['status'] = 'COMPLETED'
        print(f'Discharge analysis complete for patient {patient_id}')
        return patient

    def run_agent(self) -> List[PatientState]:
        results = []
        for patient in self.patients:
            results.append(self._run_single_patient(patient))
        return results
