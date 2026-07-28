# AIVOA Application Screenshot Specifications

This document defines the exact visual screenshot requirements for academic evaluation, showcase presentations, and portfolio demonstrations of the **AIVOA Complaint Management System**.

---

## Required Screenshot Index

| ID | Title | Purpose | Recommended Filename | README / Doc Target |
| --- | --- | --- | --- | --- |
| `SHOT-01` | Initial Application State | Showcase clean dual-panel layout prior to data entry. | `docs/images/01_initial_state.png` | `README.md` (Application Screenshots) |
| `SHOT-02` | Document Drag-and-Drop | Demonstrate PDF/TXT document intake capability. | `docs/images/02_document_upload.png` | `README.md` (Document Extraction) |
| `SHOT-03` | Automated Field Extraction | Show form fields populated with pulse highlight effect. | `docs/images/03_extracted_form.png` | `README.md` (Key Features) |
| `SHOT-04` | AI Risk Assessment Card | Display critical severity evaluation & recommendations. | `docs/images/04_risk_assessment.png` | `README.md` (Risk Assessment Pipeline) |
| `SHOT-05` | Conversational Correction | Demonstrate non-destructive patch update via chat. | `docs/images/05_conversational_edit.png` | `docs/workflow.md` (Correction Workflow) |
| `SHOT-06` | Transactional Save Success | Show persistence confirmation banner with database UUID. | `docs/images/06_database_save.png` | `README.md` (Database Schema) |

---

## Detailed Visual Specifications

### `SHOT-01`: Initial Application State

- **Title**: Initial Dual-Panel QMS Workspace
- **Purpose**: Demonstrates the baseline dual-panel UI architecture.
- **Filename**: `docs/images/01_initial_state.png`
- **Location in README**: [Application Screenshots section](file:///C:/Users/harsh/Projects/aivoa-complaint-management/README.md#application-screenshots)
- **Visual Composition**:
  - **Header**: Wordmark `AIVOA | Complaint Management System`.
  - **Left Panel**: Form fields displaying placeholder text (`"Awaiting AI extraction..."`), initial triage badge set to `"Incomplete Intake"`, and empty Risk Assessment card.
  - **Right Panel**: Copilot intake assistant showing upload drop zone, supported format badges (`PDF`, `TXT`, `EML`), and empty prompt textarea.

---

### `SHOT-02`: Document Drag-and-Drop Intake

- **Title**: Document Intake & Processing Chip
- **Purpose**: Illustrates PDF file ingestion and metadata validation.
- **Filename**: `docs/images/02_document_upload.png`
- **Location in README**: [Document Extraction Pipeline](file:///C:/Users/harsh/Projects/aivoa-complaint-management/README.md#document-extraction-pipeline)
- **Visual Composition**:
  - **Right Panel Upload Zone**: Green document chip displaying file metadata: `metformin_complaint.pdf (1.1 KB)`.
  - **Action Button**: "Process Document" button highlighted.
  - **Left Panel**: Unchanged pending extraction.

---

### `SHOT-03`: Automated Field Extraction & Visual Pulse

- **Title**: Automated Form Field Extraction
- **Purpose**: Highlights extracted complaint facts and UI pulse animations.
- **Filename**: `docs/images/03_extracted_form.png`
- **Location in README**: [Key Features](file:///C:/Users/harsh/Projects/aivoa-complaint-management/README.md#key-features)
- **Visual Composition**:
  - **Left Panel Form**: Populated fields including Customer Name (`"Metro General Hospital"`), Product (`"Metformin"`), Strength (`"500 mg"`), Batch (`"MTF-2026-089"`), Quantity (`"120"`), and Complaint Date (`"2026-07-20"`).
  - **Pulse Highlights**: Visual green border pulse glow on newly changed input fields.
  - **Copilot Chat**: Assistant response bulleting extracted fields and missing fields.

---

### `SHOT-04`: AI Risk Assessment Panel

- **Title**: AI Risk Triaging & Decision Support
- **Purpose**: Demonstrates real-time severity classification and recommendation generation.
- **Filename**: `docs/images/04_risk_assessment.png`
- **Location in README**: [Risk Assessment Pipeline](file:///C:/Users/harsh/Projects/aivoa-complaint-management/README.md#risk-assessment-pipeline)
- **Visual Composition**:
  - **Risk Card**: Severity pill set to **`HIGH`** (red/orange theme).
  - **Rationale Box**: Text explaining physical crumbling and dissolution risks.
  - **Confidence Gauge**: Displays confidence score (e.g., `94%`).
  - **Recommended Action**: Suggested next steps (`"Issue immediate batch hold on MTF-2026-089..."`).

---

### `SHOT-05`: Conversational Correction & Non-Destructive Merging

- **Title**: Conversational Editing via Copilot
- **Purpose**: Validates non-destructive state refinement.
- **Filename**: `docs/images/05_conversational_edit.png`
- **Location in Documentation**: [docs/workflow.md](file:///C:/Users/harsh/Projects/aivoa-complaint-management/docs/workflow.md)
- **Visual Composition**:
  - **Copilot Chat**: User prompt: `"Correct the quantity affected to 150 units."`
  - **Assistant Response**: `"Updated complaint details: Quantity Affected: 150"`.
  - **Left Form**: `quantity_affected` field dynamically updates to `150` while all other previously extracted fields remain intact.

---

### `SHOT-06`: Transactional Database Save Confirmation

- **Title**: Database Save Confirmation Banner
- **Purpose**: Verifies single-commit transaction persistence.
- **Filename**: `docs/images/06_database_save.png`
- **Location in README**: [Database Schema Overview](file:///C:/Users/harsh/Projects/aivoa-complaint-management/README.md#database-schema-overview)
- **Visual Composition**:
  - **Form Top**: Green alert banner displaying: `✓ Complaint persisted successfully! (ID: c7a8b9e0-1234-4567-89ab-cdef01234567)`.
  - **Action Button**: "Save Complaint" button in disabled/saving state.
