# Academic Project Report Outline: AIVOA Complaint Management System

This document outlines the formal academic project report structure for the **AIVOA AI-Powered Customer Complaint Management System**. It is formatted for expansion into a thesis, capstone project report, or conference paper submission.

---

# Title: AIVOA: A Constrained LLM Architecture for Pharmaceutical Quality Complaint Management

---

## Abstract

In regulated pharmaceutical manufacturing environments, customer complaint intake requires extracting structured parameters from heterogeneous, natural language communications (such as emails, phone logs, and uploaded PDF documents) into strict Quality Management System (QMS) database records. Unconstrained Large Language Models (LLMs) present significant operational risks in this domain due to schema hallucinations, silent date/quantity formatting corruptions, prompt injection vulnerabilities, and destructive state overwrites during multi-turn dialogs. This paper presents **AIVOA**, an enterprise-grade complaint management architecture that addresses these challenges through a hybrid system design. AIVOA integrates Groq-accelerated LLM inference (`openai/gpt-oss-120b`) enforcing token-level JSON Schema constrained decoding, a directed state graph managed by LangGraph, non-destructive patch-merging state logic, and relational database persistence via FastAPI and SQLAlchemy. Empirical evaluation across 33 unit and integration tests demonstrates zero schema violation, 100% missing field tracking accuracy, robust prompt injection defense, and reliable transactional persistence.

---

## 1. Introduction

- **1.1 Regulatory Background**: Overview of Good Manufacturing Practice (GMP), 21 CFR Part 211, and EU Annex 11 requirements for complaint handling and risk triaging.
- **1.2 The Role of Artificial Intelligence in Quality Management**: Opportunities for automation in QMS intake workflows.
- **1.3 Scope of the Project**: Development of a dual-panel web application (React/Redux frontend, FastAPI/LangGraph backend, Groq LLM integration).

---

## 2. Problem Statement & Motivation

- **2.1 Operational Bottlenecks in Manual QMS Intake**: High latency, transcription error risks, and delayed recall decisions.
- **2.2 Failure Modes of Unconstrained Generative AI**:
  - *Schema Mismatch & Type Errors*: Non-numeric string quantities (e.g., `"three bottles"` vs `3`).
  - *Date Ambiguity*: Partial or relative dates failing ISO 8601 requirements.
  - *Hallucination of Missing Data*: AI inventing batch numbers or expiry dates when absent in source text.
  - *Destructive State Merging*: Overwriting verified facts during follow-up user clarification messages.
  - *Prompt Injection*: Adversarial instructions embedded in uploaded customer PDFs attempting to override severity triaging.

---

## 3. Objectives

- **Primary Objective**: Design and implement a submission-ready, end-to-end complaint management web application.
- **Key Technical Goals**:
  1. Enforce strict JSON schema compliance at the token decoding boundary.
  2. Implement a 4-node LangGraph orchestration graph (`determine_intent`, `extract_fields`, `merge_patch`, `assess_risk`).
  3. Guarantee non-destructive state merging across multi-turn conversational edits and document intake.
  4. Develop secure server-side PDF/TXT/EML document processing with prompt injection defense.
  5. Provide ACID-compliant relational database persistence separating complaint facts from AI decision support.

---

## 4. Architecture & System Design

- **4.1 System Overview**: Decoupled client-server architecture diagram.
- **4.2 Frontend Architecture**: React 18, Vite, Redux Toolkit state slices (`complaintSlice`, `copilotSlice`), read-only form projection, visual pulse animation engine.
- **4.3 Backend Architecture**: FastAPI REST routers, service layers, SQLAlchemy ORM models.
- **4.4 Agent Graph Design (LangGraph)**:
  - `ComplaintAgentState` definition.
  - Deterministic intent classification (`create` vs `update`).
  - Non-destructive patch merging rules (conversational vs document augmentation rules).
  - Risk assessment & deterministic missing field computation.
- **4.5 LLM Service & Schema Constraints**:
  - Model selection justification (`openai/gpt-oss-120b` via Groq Cloud API).
  - Hand-crafted `COMPLAINT_EXTRACTION_SCHEMA` and `RISK_ASSESSMENT_SCHEMA` with `strict: true`.
  - Pydantic v2 field validators for numeric and date normalization safety nets.
- **4.6 Data & Database Architecture**:
  - Entity-Relationship diagram (`complaints` vs `risk_assessments`).
  - Strict nullability policy (preserving missing facts as `NULL`).

---

## 5. Implementation Details

- **5.1 Technology Stack Summary**: Table of frameworks, languages, and libraries.
- **5.2 API Layer**: Detailed endpoint specifications (`GET /api/health`, `POST /api/ai/complaints/process`, `POST /api/ai/complaints/document`, `POST /api/complaints`).
- **5.3 Document Service & Security**: File size limits (10MB), character caps (15k), PyPDF parsing, untrusted text encapsulation headers.
- **5.4 Model Migration Analysis**: Decommissioning of `gemma2-9b-it`, deprecation of `llama-3.3-70b-versatile`, and adoption of `openai/gpt-oss-120b`.

---

## 6. Verification, Testing & Results

- **6.1 Test Methodology**: Suite of 33 unit and integration tests using Python `unittest` and `FastAPI.testclient`.
- **6.2 Test Coverage Categories**:
  - *Persistence Tests*: ACID transaction commit, foreign key linking, empty complaint rejection.
  - *Patch Merging Tests*: Field updates, non-destructive preservation of non-null fields, document augmentation.
  - *Normalizer & Validator Tests*: Word-to-number conversion (`"48 capsules"` -> `48`), indefinite quantity handling (`"several"` -> `None`), ISO date parsing.
  - *Document Extraction Tests*: Extension validation, empty file rejection, size cap enforcement.
- **6.3 Summary of Empirical Results**: 100% test pass rate across 33 test cases.

---

## 7. Discussion & Evaluation

- **7.1 Comparison with Unconstrained LLM Approaches**: Trade-off between generative flexibility and regulatory auditability.
- **7.2 Security & Robustness**: Evaluation of prompt injection defense mechanisms.
- **7.3 Compliance Readiness**: Alignment with GxP data integrity guidelines.

---

## 8. Conclusion & Future Scope

- **8.1 Summary of Contributions**: Successfully built and validated AIVOA as a constrained QMS complaint management platform.
- **8.2 Future Directions**:
  - Multi-tenant Role-Based Access Control (RBAC).
  - Integration with enterprise QMS software (Veeva Vault, TrackWise).
  - Optical Character Recognition (OCR) for scanned paper complaints.
  - Multi-lingual complaint extraction.

---

## References

1. US Food and Drug Administration (FDA). *21 CFR Part 211 - Current Good Manufacturing Practice for Finished Pharmaceuticals*.
2. European Medicines Agency (EMA). *EudraLex Volume 4 - Annex 11: Computerised Systems*.
3. LangChain / LangGraph Documentation. *StateGraph and Multi-Agent Systems*.
4. Groq Developer Platform. *Structured Outputs with Strict Mode JSON Schema*.
