# AIVOA API Specification Documentation

This document provides complete, reference-grade specification details for all REST API endpoints exposed by the **AIVOA Complaint Management System** backend.

---

## Base Configuration

- **Base URL**: `http://localhost:8000`
- **Default Protocol**: HTTP/1.1
- **Content Type**: `application/json` (except multipart document upload)
- **CORS Allowed Origins**: Configured via `FRONTEND_ORIGIN` (default: `http://localhost:5173`)

---

## Summary of Endpoints

| Method | Endpoint | Description | Auth Required |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Service health check and operational status verification. | None |
| `POST` | `/api/ai/complaints/process` | Conversational message processing & non-destructive merging. | None |
| `POST` | `/api/ai/complaints/document` | Document upload, text extraction, & non-destructive intake. | None |
| `POST` | `/api/complaints` | ACID database persistence of complaint and risk assessment. | None |

---

## Endpoint Details

### 1. `GET /api/health`

#### Purpose
Verifies backend service availability, operational readiness, and component responsiveness.

#### Request
- **HTTP Method**: `GET`
- **Path**: `/api/health`
- **Headers**: None required

#### Responses

##### `200 OK`
```json
{
  "status": "healthy",
  "service": "AIVOA Complaint Management Backend",
  "message": "Backend is operational and ready for Phase 2."
}
```

---

### 2. `POST /api/ai/complaints/process`

#### Purpose
Processes a natural language chat message through the LangGraph agent graph (`determine_intent` -> `extract_fields` -> `merge_patch` -> `assess_risk`). Returns the non-destructively merged complaint, updated risk assessment, missing fields array, and changed fields array.

#### Request
- **HTTP Method**: `POST`
- **Path**: `/api/ai/complaints/process`
- **Content-Type**: `application/json`

##### Request Schema (`ProcessComplaintRequest`)
| Field Name | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `string` | Yes | Natural language text typed by the user. |
| `current_complaint` | `object` | No | Current complaint fields in Redux store. Defaults to `null`. |
| `current_risk` | `object` | No | Current risk assessment in Redux store. Defaults to `null`. |

##### Example Request Payload
```json
{
  "message": "Apollo Pharmacy reported that 50 bottles of Paracetamol 500mg (Batch BATCH-9988) had broken tamper seals on 2026-05-10.",
  "current_complaint": null,
  "current_risk": null
}
```

#### Responses

##### `200 OK` (`ProcessComplaintResponse`)
```json
{
  "complaint": {
    "complaint_source": null,
    "customer_name": "Apollo Pharmacy",
    "product_name": "Paracetamol",
    "product_strength_grade": "500mg",
    "batch_number": "BATCH-9988",
    "manufacturing_date": null,
    "expiry_date": null,
    "quantity_affected": 50,
    "complaint_type": "broken tamper seals",
    "complaint_date": "2026-05-10",
    "detailed_complaint_description": "50 bottles of Paracetamol 500mg had broken tamper seals",
    "initial_severity": null,
    "priority": null
  },
  "risk": {
    "severity": "medium",
    "rationale": "Broken tamper seals represent a physical packaging defect without reported patient exposure.",
    "missing_fields": [
      "complaint_source",
      "manufacturing_date",
      "expiry_date",
      "initial_severity",
      "priority"
    ],
    "confidence": 0.85,
    "recommended_action": "Quarantine affected lot BATCH-9988 and perform packaging integrity review."
  },
  "missing_fields": [
    "complaint_source",
    "manufacturing_date",
    "expiry_date",
    "initial_severity",
    "priority"
  ],
  "changed_fields": [
    "customer_name",
    "product_name",
    "product_strength_grade",
    "batch_number",
    "quantity_affected",
    "complaint_type",
    "complaint_date",
    "detailed_complaint_description"
  ]
}
```

##### Possible Error Responses

- **`422 Unprocessable Entity`**: Request body missing required `message` field.
  ```json
  {
    "detail": [
      {
        "loc": ["body", "message"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
  ```
- **`502 Bad Gateway`**: Groq API failure or model response failing strict JSON schema validation.
  ```json
  {
    "detail": "Complaint processing failed: Groq API call failed: Connection refused"
  }
  ```

---

### 3. `POST /api/ai/complaints/document`

#### Purpose
Uploads and processes a complaint document binary (`.pdf`, `.txt`, `.eml`). Validates file constraints, extracts text, applies prompt hardening boundaries, runs facts through the LangGraph pipeline, and non-destructively augments missing complaint fields.

#### Request
- **HTTP Method**: `POST`
- **Path**: `/api/ai/complaints/document`
- **Content-Type**: `multipart/form-data`

##### Form Parameters
| Parameter Name | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | `UploadFile` | Yes | Binary document file (`.pdf`, `.txt`, `.eml`). Max 10MB. |
| `current_complaint_json` | `string` | No | Serialized JSON string of current frontend complaint state. |
| `current_risk_json` | `string` | No | Serialized JSON string of current frontend risk state. |

##### Example Form Upload (cURL)
```bash
curl -X POST "http://localhost:8000/api/ai/complaints/document" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@samples/metformin_complaint.pdf;type=application/pdf" \
  -F 'current_complaint_json={"customer_name":"Metro General Hospital"}'
```

#### Responses

##### `200 OK` (`ProcessComplaintResponse`)
```json
{
  "complaint": {
    "complaint_source": "Hospital Pharmacy Report",
    "customer_name": "Metro General Hospital",
    "product_name": "Metformin",
    "product_strength_grade": "500 mg",
    "batch_number": "MTF-2026-089",
    "manufacturing_date": "2026-01-15",
    "expiry_date": "2028-01-14",
    "quantity_affected": 120,
    "complaint_type": "Physical Defect / Crumbling Tablets",
    "complaint_date": "2026-07-20",
    "detailed_complaint_description": "Tablets exhibit severe crumbling and disintegration inside sealed blister packs.",
    "initial_severity": "Major",
    "priority": "High"
  },
  "risk": {
    "severity": "high",
    "rationale": "Severe physical disintegration of solid oral dosage form compromises dosage uniformity.",
    "missing_fields": [],
    "confidence": 0.94,
    "recommended_action": "Issue immediate batch hold on MTF-2026-089 and initiate friability testing."
  },
  "missing_fields": [],
  "changed_fields": [
    "complaint_source",
    "product_name",
    "product_strength_grade",
    "batch_number",
    "manufacturing_date",
    "expiry_date",
    "quantity_affected",
    "complaint_type",
    "complaint_date",
    "detailed_complaint_description",
    "initial_severity",
    "priority"
  ]
}
```

##### Possible Error Responses

- **`400 Bad Request`**: File validation failure (empty file, unsupported file extension, corrupted PDF, encrypted PDF, or text exceeding 15,000 characters).
  ```json
  {
    "detail": "Unsupported file format '.docx'. Supported formats are: .eml, .pdf, .txt."
  }
  ```
- **`400 Bad Request`**: Malformed JSON string in `current_complaint_json` or `current_risk_json`.
  ```json
  {
    "detail": "Invalid current_complaint JSON string."
  }
  ```
- **`502 Bad Gateway`**: Extraction or risk model failure during document graph execution.
  ```json
  {
    "detail": "Document complaint processing failed: Groq did not return valid JSON"
  }
  ```

---

### 4. `POST /api/complaints`

#### Purpose
Persists the final, verified complaint record and optional AI risk assessment to the underlying database (PostgreSQL / SQLite) within a single ACID-compliant transaction.

#### Request
- **HTTP Method**: `POST`
- **Path**: `/api/complaints`
- **Content-Type**: `application/json`

##### Request Schema (`SaveComplaintRequest`)
```json
{
  "complaint": {
    "complaint_source": "Email Intake",
    "customer_name": "Apollo Pharmacy",
    "product_name": "Amoxicillin",
    "product_strength_grade": "500 mg",
    "batch_number": "AMX-8871",
    "manufacturing_date": "2026-02-10",
    "expiry_date": "2028-02-09",
    "quantity_affected": 30,
    "complaint_type": "Discoloration",
    "complaint_date": "2026-07-25",
    "detailed_complaint_description": "Discolored yellow capsules observed in unopened bottle.",
    "initial_severity": "Critical",
    "priority": "High"
  },
  "risk_assessment": {
    "severity": "high",
    "rationale": "Chemical discoloration indicates potential thermal degradation or contamination.",
    "missing_fields": [],
    "confidence": 0.91,
    "recommended_action": "Quarantine lot AMX-8871 and initiate stability investigation."
  }
}
```

#### Responses

##### `201 Created` (`ComplaintResponse`)
```json
{
  "id": "c7a8b9e0-1234-4567-89ab-cdef01234567",
  "complaint_source": "Email Intake",
  "customer_name": "Apollo Pharmacy",
  "product_name": "Amoxicillin",
  "product_strength_grade": "500 mg",
  "batch_number": "AMX-8871",
  "manufacturing_date": "2026-02-10",
  "expiry_date": "2028-02-09",
  "quantity_affected": 30,
  "complaint_type": "Discoloration",
  "complaint_date": "2026-07-25",
  "detailed_complaint_description": "Discolored yellow capsules observed in unopened bottle.",
  "initial_severity": "Critical",
  "priority": "High",
  "created_at": "2026-07-28T18:14:00.123456",
  "updated_at": "2026-07-28T18:14:00.123456",
  "risk_assessments": [
    {
      "id": "f1e2d3c4-5678-90ab-cdef-1234567890ab",
      "complaint_id": "c7a8b9e0-1234-4567-89ab-cdef01234567",
      "severity": "high",
      "rationale": "Chemical discoloration indicates potential thermal degradation or contamination.",
      "missing_fields": [],
      "confidence": 0.91,
      "recommended_action": "Quarantine lot AMX-8871 and initiate stability investigation.",
      "created_at": "2026-07-28T18:14:00.125000"
    }
  ]
}
```

##### Possible Error Responses

- **`400 Bad Request`**: Complaint object is empty (all fields are `null`).
  ```json
  {
    "detail": "Complaint must contain at least one meaningful field. All fields cannot be null."
  }
  ```
- **`500 Internal Server Error`**: Database connection failure or transaction commit rollback failure.
  ```json
  {
    "detail": "Failed to persist complaint: Database connection error"
  }
  ```
