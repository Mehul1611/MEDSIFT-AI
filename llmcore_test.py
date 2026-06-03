import time
from llmcore.discharge_agent.discharge_agent import DischargeSummaryAgent
from llmcore.discharge_agent.patient_state import PatientState

patients: list[PatientState] = [
    {
        'patient_id': 'patient-001',
        'source_notes_dir': 'sample_data\patient 2 (1).pdf',
    }
]


def run() -> None:
    agent = DischargeSummaryAgent(patients=patients)
    results = agent.run_agent()

    for result in results:
        print(
            f'''Patient: {result.get('patient_id')}
            Status: {result.get('status')}
            Output dir: {result.get('output_dir')}'''
        )


def main():
    start = time.time()
    run()
    print(f'\nTotal time: {time.time() - start:.1f}s')


if __name__ == '__main__':
    main()
