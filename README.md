# MedSift AI — Discharge Summary Agent

An agentic system that reads messy clinical source-note PDFs and produces a structured discharge summary **draft for clinician review**. The design prioritizes clinical safety: the agent plans, uses tools, recovers from failures, and refuses to invent facts.

---

## Agent Loop Design

The pipeline is orchestrated by `DischargeSummaryAgent` and runs in four stages per patient:

```
PDFs → Document Preprocessing → Planning Agent (tool loop) → Writer Agent → Saved outputs
```

### Stage 1 — Document preprocessing

`DocumentContextBuilder` lists all PDFs in the patient's notes folder, renders each page to an image, and calls the **Summary Agent** (LLaVA via Ollama) once per page. Page summaries are assembled into a single `document_context.md` artifact. Page summarization runs in parallel (`ThreadPoolExecutor`, 2 workers) to reduce latency on multi-page charts.

The Summary Agent is intentionally narrow: it extracts what is visible on each page and does not perform discharge-level reasoning or conflict resolution.

### Stage 2 — Planning Agent (real agent loop)

The **Clinical Planning & Orchestration Agent** receives the page-wise summaries and available document list. It runs as a LangChain `AgentExecutor` with a hard cap of **20 iterations** (`PLANNING_MAX_ITERATIONS`).

Available tools (the agent decides when to call each):

| Tool | Purpose |
|---|---|
| `READ_PDF_TOOL` | Re-read raw text from specific PDF pages when summaries are unclear or conflicting |
| `DRUG_INTERACTION_TOOL` | Mock drug–drug interaction check on discharge medications |
| `ESCALATE_CLINICIAN_TOOL` | Formally record a safety concern for clinician review |

The planner iterates: **reason → choose tool → observe result → re-plan**. It does not emit the final clinician-facing summary. Instead it produces a structured content plan with fixed sections (demographics, diagnoses, hospital course, medications, conflicts, safety flags, evidence references, etc.).

Each step is captured in `planning_trace.md` in the format: reasoning → tool → inputs → result.

### Stage 3 — Writer Agent (single pass, no tools)

The **Discharge Summary Writer Agent** receives **only** the structured plan. It has no access to source PDFs and cannot call tools. It converts the plan into a Pydantic-validated JSON object (`DischargeSummaryOutput`), which is then rendered deterministically into markdown.

This separation keeps clinical reasoning and evidence gathering in the planner, and keeps the writer constrained to faithful formatting.

### Stage 4 — Persistence

`ResultHandler` writes five artifacts per patient under `output/discharge_summaries/{patient_id}/`:

- `document_context.md` — page summaries
- `structured_plan.md` — planner output
- `planning_trace.md` — step-by-step agent trace
- `discharge_summary.json` — structured draft
- `discharge_summary.md` — clinician-readable draft with a review disclaimer

---

## No-Fabrication Guardrail

Fabrication is blocked at multiple layers rather than relying on a single prompt instruction.

**1. Architectural separation.** The Writer Agent cannot read source documents or invoke tools. It can only copy or rephrase what the planner already extracted. If a fact is not in the plan, it cannot appear in the draft except as an explicit missing/pending marker.

**2. Prompt-enforced markers.** Both agents are instructed to mark unknowns explicitly:
- `[MISSING - Clinician Review Required]` for undocumented required fields
- `[PENDING]` for incomplete results
- `[CONFLICT]` for unresolved disagreements between documents
- `[FLAG: Reason not documented — Clinician Reconciliation Required]` for unexplained medication changes

**3. Planner validation step.** Before finishing, the planner must verify every clinical fact is evidence-backed, remove unsupported information, and list gaps in `MISSING INFORMATION`.

**4. Structured output schema.** The writer's Pydantic schema requires fields for `missing_information`, `document_conflicts`, `safety_flags`, and `evidence_references`. The markdown renderer adds a prominent **DRAFT FOR CLINICIAN REVIEW** header and never presents output as finalized.

**5. Preprocessing discipline.** The Summary Agent is told to summarize only what is visible, flag illegible content, and never infer missing values.

Together, these layers make "say missing instead of guessing" the path of least resistance at every stage.

---

## Failure Handling and Conflicts

### Failures

The system uses a **print-and-raise** pattern: errors are logged with context, then propagated so nothing downstream silently treats a failure as success.

- **LLM calls** — `@retry_llm_call()` wraps all agent invocations with Tenacity: up to 3 attempts, exponential backoff (1–32 s), retrying on connection timeouts, JSON decode errors, and related transient failures.
- **PDF ingestion** — Missing files, empty page images, and unreadable PDFs raise explicit exceptions with the document name and page number.
- **Agent parsing** — `handle_parsing_errors=True` on the planning executor prevents a malformed tool call from crashing the loop.
- **Iteration cap** — The planner stops after 20 tool steps, preventing runaway loops.

If preprocessing or planning fails for a patient, the run stops for that patient rather than producing a partial draft from incomplete evidence.

### Conflicts

When two source documents disagree, the planner records both values and their sources in a dedicated `DOCUMENT CONFLICTS` section. The writer copies this into `document_conflicts` without choosing a side. Conflicts in safety-relevant fields can additionally trigger `ESCALATE_CLINICIAN_TOOL`, which surfaces the concern in `SAFETY FLAGS`.

Medication reconciliation follows the same principle: changes are listed with documented reasons when available; undocumented changes are flagged rather than silently resolved.

---

## Part 2 — Learning from Doctor Edits (Stretch)

**Status: not implemented.** Part 1 is complete; Part 2 (the learning loop) is documented here as design only. No reward metrics or before/after results were run.

### Proposed reward signal

Use a **section-weighted edit burden score** between the agent draft and a simulated "doctor-edited" version:

```
reward = Σ_section  w_s × (1 − normalized_edit_distance(draft_s, edited_s))
         − λ × safety_violations
```

- Compare each discharge section independently (medications, diagnoses, hospital course, etc.).
- Normalize edit distance (e.g., character-level Levenshtein or token-level) to `[0, 1]`.
- Apply higher weights `w_s` to high-risk sections (medications, allergies, diagnoses).
- Subtract a large penalty `λ` if the edited version had to **add back** a safety flag, conflict, or missing marker that the draft omitted or softened — this prevents the agent from gaming the score by being vague.

### Proposed simulated reviewer

Build a hidden **Simulated Clinician Editor** — an LLM with a fixed, undisclosed editing rubric applied consistently to every draft. Example policies: standardize medication formatting, tighten hospital-course chronology, expand abbreviated diagnoses, and enforce institutional phrasing — without adding facts not supported by the structured plan. This produces `(draft, edited)` pairs for training and evaluation without real clinicians in the loop.

### Proposed learning mechanism

**Correction-memory injection** (chosen for simplicity and safety compatibility):

1. After each simulated edit, diff draft vs. edited per section and store recurring correction patterns (e.g., "always list discharge meds as `Drug dose route frequency`").
2. Inject the top-k relevant corrections into the Planning Agent system prompt for similar cases.
3. Optionally layer a **contextual bandit** over prompt variants (concise vs. narrative hospital course, bullet vs. prose medications) using the section-weighted reward to select strategies.

This approach improves drafts without fine-tuning the base model or giving the writer access to source documents, so Part 1's separation rule stays intact.

### Expected evaluation (not yet run)

On a held-out patient set, track mean edit distance and section match rate over iterations. Target: monotonic decrease in edit burden while safety-violation penalty stays at zero.

### Part 2 limitations (anticipated)

- **Cold start** — Few edit pairs early on mean noisy reward estimates; bandit exploration could temporarily worsen drafts.
- **Reward hacking** — Optimizing only for low edit distance could encourage vagueness or style mimicry rather than clinical accuracy. The safety-violation penalty and plan-only constraint for the simulated editor mitigate this.
- **Sim-to-real gap** — A simulated reviewer may not match real clinician preferences; production would need gradual blending with real edit data.

---

## Limitations of the Current Approach

- **Local open-weight models** — The stack runs on Ollama (`llava` for page OCR/summary, `llama3.2` for planning and writing). These models are slower and less reliable on dense clinical text than frontier API models, especially for medication parsing and conflict detection.
- **Vision-based PDF ingestion** — Pages are summarized from rendered images rather than structured EHR data. OCR errors and layout complexity can lose or misread details.
- **Mock safety tools** — Drug interaction checking is mocked; it records the check but does not query a real formulary or interaction database.
- **Sequential patient processing** — Patients are processed one at a time; only page summarization is parallelized today.
- **No automated evaluation harness** — Quality is assessed by inspecting traces and output artifacts, not by a regression test suite with gold-standard summaries.
- **Part 2 not built** — No edit loop, reward computation, or learning mechanism exists in the codebase yet.

---

## What Is Done vs. Not Done

| Area | Status |
|---|---|
| Multi-agent architecture (planner + writer) | Done |
| PDF ingestion and page-wise summarization | Done |
| Planning agent tool loop with iteration cap | Done |
| No-fabrication guardrails and conflict flagging | Done |
| Failure retries and print-and-raise handling | Done |
| Observability (planning trace + saved artifacts) | Done |
| Part 2 edit signal, simulated reviewer, learning loop | **Not done** |
| Automated before/after metrics | **Not done** |

---

## With More Time

**1. Frontier models via paid API.** Moving preprocessing, planning, and writing to capable hosted models (e.g., GPT-4o, Claude) would substantially improve extraction accuracy on messy PDFs and reduce reasoning errors in medication reconciliation. Inference would also be roughly **10× faster** than local Ollama on CPU-bound hardware, making multi-patient batches practical.

**2. Structured logging and observability.** Replace ad-hoc `print` statements with structured JSON logging (patient ID, stage, latency, token usage, tool name, retry count). Add a run-level correlation ID, optional OpenTelemetry export, and a lightweight dashboard for failed steps and escalation counts.

**3. Parallel execution.** Extend the existing page-level parallelism to: (a) process multiple patients concurrently, (b) increase page worker pool size based on GPU/API rate limits, and (c) pipeline stages so planning can begin on early documents while later pages are still summarizing.

**4. Part 2 implementation (next steps).** In order: implement the simulated reviewer and edit-distance reward → collect `(draft, edited)` pairs on a small held-out set → build the correction-memory store → run 3–5 learning iterations and plot edit burden vs. iteration → add the safety-violation penalty to block reward gaming → validate that missing/conflict markers are never dropped.

**5. Evaluation and hardening.** Build a regression harness with expected section contents per patient, add integration tests for tool failure paths, and run end-to-end benchmarks before and after each change.

---

## Quick Start

**Prerequisites:** Python 3.12+, [Ollama](https://ollama.com) running locally with `llava` and `llama3.2` pulled.

```bash
pip install -r requirements.txt
python llmcore_test.py
```

Place patient PDFs in a folder (e.g., `sample_data/`) and set `source_notes_dir` in `llmcore_test.py`. Outputs appear under `output/discharge_summaries/{patient_id}/`.

Optional: set `OLLAMA_BASE_URL` in `.env` (see `.env.example`).
