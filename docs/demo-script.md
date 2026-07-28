# AIVOA Technical Demo Script & Academic Presentation Guide

## Overview

- **Target Audience**: Academic evaluators, software engineering reviewers, recruiters, and open-source maintainers.
- **Format**: Video demonstration with narrated screen recording.
- **Total Target Duration**: ~4 minutes (240 seconds).
- **Core Objective**: Demonstrate constrained AI field extraction, non-destructive state merging, PDF document intake, real-time risk assessment, and ACID database persistence.

---

## Technical Setup Checklist Before Recording

1. **Backend Server**: Running on `http://localhost:8000` (`uvicorn app.main:app --reload`).
2. **Frontend App**: Open in browser at `http://localhost:5173`.
3. **Screen Resolution**: 1920x1080 (1080p60) with 100% display scaling.
4. **Sample Document**: [`samples/metformin_complaint.pdf`](file:///C:/Users/harsh/Projects/aivoa-complaint-management/samples/metformin_complaint.pdf) ready on desktop.
5. **Database**: Reset or empty database state.

---

## Detailed Demo Timeline & Script

```mermaid
gantt
    title AIVOA Technical Demo Timeline (4 Minutes Total)
    dateFormat  m:s
    axisFormat %M:%S
    
    section Intro
    Architecture & Problem Statement :active, 0:00, 0:30
    
    section Intake & AI Pipeline
    Conversational Natural Language Intake :0:30, 1:15
    Document Ingestion (metformin_complaint.pdf) :1:15, 2:15
    
    section Editing & Risk
    Non-Destructive Conversational Correction :2:15, 3:00
    AI Risk Assessment Evaluation :3:00, 3:30
    
    section Persistence & Conclusion
    Database Persistence & Verification :3:30, 4:00
```

---

### Scene 1: System Overview & Problem Statement (0:00 - 0:30)

- **Duration**: 30 Seconds
- **Camera Focus**: Full screen view of the initial dual-panel AIVOA interface.
- **Screen Action**: Mouse hovers smoothly over the Left Panel (Complaint Form) and Right Panel (Copilot Assistant).

#### Voice-Over Transcript
> "Welcome to this demonstration of **AIVOA**, an AI-powered customer complaint management platform engineered for pharmaceutical quality management systems.
> In pharmaceutical manufacturing, complaint data arrives in unstructured formats such as emails or letters. Manually transcribing these into regulatory records is error-prone, while standard LLMs often hallucinate missing dates or corrupt numeric values.
> AIVOA solves this by combining Groq Structured Outputs in strict JSON mode with a LangGraph state engine to guarantee data integrity."

---

### Scene 2: Conversational Intake (0:30 - 1:15)

- **Duration**: 45 Seconds
- **Camera Focus**: Zoom to Copilot chat input box, then pan to the Complaint Form fields.
- **Screen Action**:
  1. Click "Try an example" chip: `"Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg."`
  2. Press Enter to submit.

#### Voice-Over Transcript
> "Let's begin by testing conversational intake. I'll click our example prompt reporting discolored capsules from Apollo Pharmacy.
> Behind the scenes, FastAPI routes the prompt to a four-node LangGraph pipeline. Groq's `openai/gpt-oss-120b` model extracts facts constrained by a strict JSON schema.
> Notice how Customer Name, Product Name, Strength, and Complaint Type instantly populate the form on the left with a smooth pulse animation. Unmentioned fields like Manufacturing Date remain strictly null, avoiding any AI guesswork."

---

### Scene 3: Document Upload & Augmentation (1:15 - 2:15)

- **Duration**: 60 Seconds
- **Camera Focus**: Drag-and-Drop upload zone, document processing chip, and form transition.
- **Screen Action**:
  1. Click 'Reset Form' to clear workspace.
  2. Drag and drop `samples/metformin_complaint.pdf` into the upload zone.
  3. Click "Process Document".

#### Voice-Over Transcript
> "Now let's demonstrate document intake. I'll drag and drop a formal quality report PDF from Metro General Hospital regarding Metformin 500mg.
> AIVOA's server-side document service validates file metadata, enforces a 10MB limit, extracts raw text with PyPDF, and wraps it in a prompt injection defense boundary.
> Upon clicking 'Process Document', the LangGraph engine extracts all 13 schema fields—including batch numbers, manufacturing dates, expiry dates, and affected quantities—directly from the document text. The interface animates all newly populated fields."

---

### Scene 4: Conversational Correction & Non-Destructive Merging (2:15 - 3:00)

- **Duration**: 45 Seconds
- **Camera Focus**: Split screen focusing on the Quantity Affected field and Chat Input.
- **Screen Action**:
  1. Type in Copilot input: `"Update the quantity affected to 150 bottles."`
  2. Press Enter.

#### Voice-Over Transcript
> "What happens when a user needs to correct an extracted value? Let's type: 'Update the quantity affected to 150 bottles.'
> LangGraph's `determine_intent` node detects an existing active complaint and sets intent to 'update'. The `merge_patch` node applies a non-destructive merge: the quantity updates to 150, while pre-existing batch numbers and dates remain completely preserved.
> This guarantees that conversational corrections never erase previously verified data."

---

### Scene 5: AI Risk Assessment & Decision Support (3:00 - 3:30)

- **Duration**: 30 Seconds
- **Camera Focus**: Zoom on the Risk Assessment Card (bottom left panel).
- **Screen Action**: Scroll down slightly to highlight the Risk Severity badge, Rationale, and Recommended Action.

#### Voice-Over Transcript
> "Below the complaint form, AIVOA provides an automated AI Risk Assessment.
> Based on the physical disintegration described in the report, the AI classifies severity as **HIGH**, provides a clear rationale grounded strictly in complaint facts, calculates confidence at 94%, and recommends an immediate batch hold.
> Risk assessments are kept structurally separate from complaint facts, ensuring decision support is never confused with extracted data."

---

### Scene 6: Database Persistence & Conclusion (3:30 - 4:00)

- **Duration**: 30 Seconds
- **Camera Focus**: "Save Complaint" button, top success banner.
- **Screen Action**:
  1. Click "Save Complaint".
  2. Highlight the green success banner displaying the generated UUID.

#### Voice-Over Transcript
> "Finally, the QA reviewer clicks 'Save Complaint'. The backend opens a database transaction, persisting both the Complaint entity and linked RiskAssessment entity atomically to PostgreSQL.
> The UI displays a success confirmation with the database primary key UUID.
> This concludes the technical demonstration of AIVOA—a robust, production-ready solution for pharmaceutical complaint management. Thank you."
