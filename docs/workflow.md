# AIVOA End-to-End Workflow Documentation

This document explains the end-to-end operational workflows and state transition models within the **AIVOA Complaint Management System**.

---

## Workflow Overview

AIVOA processes incoming complaints through five distinct workflows:
1. **Conversational Intake Workflow**
2. **Correction & Refinement Workflow**
3. **Document Upload & Processing Workflow**
4. **"Ready to Commit" Triage State Machine**
5. **ACID Transaction Persistence Workflow**

---

## 1. Conversational Intake Workflow

The conversational intake workflow allows users to type unstructured complaint details directly into the Copilot chat input.

```mermaid
sequenceDiagram
    autonumber
    participant User as QA Reviewer
    participant UI as Copilot UI / Redux
    participant API as POST /api/ai/complaints/process
    participant Graph as LangGraph Engine
    participant Groq as Groq (gpt-oss-120b)

    User->>UI: Types: "Apollo Pharmacy reported discolored Amoxicillin 500mg capsules."
    UI->>UI: Dispatch addMessage(role="user") & setLoading(true)
    UI->>API: Send { message, current_complaint: null, current_risk: null }
    API->>Graph: run_complaint_agent(message, current_complaint=None)
    Graph->>Graph: determine_intent -> intent="create"
    Graph->>Groq: extract_fields() with COMPLAINT_EXTRACTION_SCHEMA
    Groq-->>Graph: Returns Extracted Patch JSON
    Graph->>Graph: merge_patch() -> Populate new fields
    Graph->>Groq: assess_risk() with RISK_ASSESSMENT_SCHEMA
    Groq-->>Graph: Returns Risk Assessment JSON
    Graph-->>API: Returns final ComplaintAgentState
    API-->>UI: 200 OK Response (complaint, risk, missing_fields, changed_fields)
    UI->>UI: Dispatch setComplaint, setRiskAssessment, setLastChangedFields
    UI->>User: UI animates field highlights & displays assistant summary
```

---

## 2. Correction & Refinement Workflow

When an active complaint record exists on the screen, subsequent chat messages trigger the **Correction & Refinement Workflow**.

```mermaid
flowchart TD
    UserMsg[User sends correction: 'Actually, the batch number was AMX-9002'] --> SendAPI[Call POST /api/ai/complaints/process with current_complaint]
    SendAPI --> IntentNode[Node: determine_intent]
    IntentNode -->|current_complaint contains facts| SetUpdate[Set intent = 'update']
    SetUpdate --> ExtractNode[Node: extract_fields]
    ExtractNode --> MergNode[Node: merge_patch]
    
    subgraph MergeLogic ["Non-Destructive Patch Merging"]
        MergNode --> InspectPatch[Inspect extracted patch: batch_number='AMX-9002']
        InspectPatch --> CompareFields[Compare with current_complaint fields]
        CompareFields -->|Value differs| ApplyUpdate[Update batch_number to 'AMX-9002']
        CompareFields -->|Patch value is null| PreserveOld[Preserve existing non-null values]
        ApplyUpdate --> RecalculateChanged[Add 'batch_number' to changed_fields]
    end

    RecalculateChanged --> RiskNode[Node: assess_risk]
    RiskNode --> CheckChanged{changed_fields > 0?}
    CheckChanged -- Yes --> CallGroqRisk[Re-query Groq for updated risk assessment]
    CheckChanged -- No --> KeepExistingRisk[Preserve current_risk without Groq call]
    CallGroqRisk --> ReturnClient[Return merged state to client]
    KeepExistingRisk --> ReturnClient
```

---

## 3. Document Upload Workflow

The Document Upload Workflow ingests `.pdf`, `.txt`, or `.eml` files without overwriting pre-existing complaint data.

```mermaid
sequenceDiagram
    autonumber
    participant User as QA Reviewer
    participant Client as Copilot Panel UI
    participant API as POST /api/ai/complaints/document
    participant DocSvc as Document Service
    participant Graph as LangGraph Engine

    User->>Client: Drag & drop PDF file (e.g. metformin_complaint.pdf)
    Client->>Client: Display document chip with file size
    User->>Client: Click "Process Document"
    Client->>API: Multipart Form Data (file + current_complaint_json)
    API->>DocSvc: validate_and_extract_document_text(bytes)
    DocSvc->>DocSvc: Check extension, file size (<=10MB), & extract text stream
    DocSvc->>DocSvc: Enforce prompt injection defense encapsulation
    DocSvc-->>API: Extracted raw text string
    API->>Graph: run_complaint_agent(extracted_text, is_document=True)
    Graph->>Graph: merge_patch(is_document=True)
    Note over Graph: Document Augmentation Rule:<br/>Fill NULL fields ONLY.<br/>DO NOT overwrite existing facts.
    Graph-->>API: Final State
    API-->>Client: 200 OK Response
    Client->>Client: Update Redux store & trigger field pulse animation
```

---

## 4. "Ready to Commit" Triage State Machine

The frontend calculates form completeness and triage status dynamically via Redux state.

```mermaid
stateDiagram-v2
    [*] --> EmptyState: Form empty / All fields null
    
    state EmptyState {
        SaveButton: Save Complaint Button Disabled
        StatusTag: Triage Status = "Incomplete Intake"
    }

    EmptyState --> PartialState: First extraction completed (>=1 field populated)

    state PartialState {
        SaveButtonP: Save Complaint Button Enabled
        StatusTagP: Triage Status = "Pending Review"
    }

    PartialState --> CompleteState: All required schema fields populated

    state CompleteState {
        SaveButtonC: Save Complaint Button Enabled
        StatusTagC: Triage Status = "Ready for Submission"
    }

    PartialState --> ResetState: User clicks "Reset Form"
    CompleteState --> ResetState: User clicks "Reset Form"
    CompleteState --> PersistedState: User clicks "Save Complaint"

    state PersistedState {
        SaveBanner: Displays "✓ Complaint persisted successfully! (ID: ...)"
    }

    ResetState --> EmptyState
    PersistedState --> EmptyState: User resets after save
```

---

## 5. Persistence Workflow

When the QA Reviewer verifies the form data and clicks **Save Complaint**, the record is committed to the database.

```mermaid
flowchart TD
    Click[Click Save Complaint Button] --> CheckState{At least 1 meaningful field?}
    CheckState -- No --> ShowErr[Display UI error banner: Cannot save empty complaint]
    CheckState -- Yes --> SetSaving[Set isSaving = true]
    SetSaving --> CallAPI[POST /api/complaints]
    CallAPI --> BeginTx[Backend: Begin DB Transaction]
    BeginTx --> InsertComp[Insert Complaint Entity]
    InsertComp --> CheckRisk{Risk Assessment Present?}
    CheckRisk -- Yes --> InsertRisk[Insert RiskAssessment with FK complaint_id]
    CheckRisk -- No --> CommitTx[Commit DB Transaction]
    InsertRisk --> CommitTx
    CommitTx --> SendRes[Return 201 Created with persisted UUID]
    SendRes --> ShowSucc[UI: Display success banner with UUID]
    
    BeginTx -->|On Exception| RollbackTx[Backend: Rollback Transaction]
    RollbackTx --> Return500[Return HTTP 500 / 400 Error]
    Return500 --> ShowErrBanner[UI: Display error banner]
```
