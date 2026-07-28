# AIVOA Database & Entity Model Documentation

## Overview

The **AIVOA Complaint Management System** utilizes a relational database architecture designed for compliance with pharmaceutical Quality Management Systems (QMS). The data layer strictly isolates **factual customer complaint data** from **AI decision support assessments**.

The backend uses **SQLAlchemy 2.0 ORM** with native PostgreSQL support (`psycopg3`) for production deployment and SQLite in-memory support for zero-dependency automated testing.

---

## Entity-Relationship Architecture

```mermaid
erDiagram
    complaints ||--o{ risk_assessments : "possesses (cascade delete-orphan)"
    
    complaints {
        uuid id PK "Primary Key (UUIDv4)"
        string complaint_source "Source channel (e.g. Email, Phone, Document)"
        string customer_name "Reporting customer or facility name"
        string product_name "Commercial product name"
        string product_strength_grade "Dosage strength or grade (e.g. 500mg)"
        string batch_number "Manufacturing lot identifier"
        date manufacturing_date "Manufacturing date (YYYY-MM-DD)"
        date expiry_date "Product expiration date (YYYY-MM-DD)"
        numeric quantity_affected "Exact numerical count or volume"
        string complaint_type "Defect category classification"
        date complaint_date "Date complaint was received"
        text detailed_complaint_description "Unstructured technical description"
        string initial_severity "Initial reporter severity indicator"
        string priority "Intake triage priority level"
        datetime created_at "System timestamp at record creation"
        datetime updated_at "System timestamp at last modification"
    }

    risk_assessments {
        uuid id PK "Primary Key (UUIDv4)"
        uuid complaint_id FK "Foreign Key -> complaints.id"
        string severity "AI Risk Severity (low, medium, high, critical)"
        text rationale "Ground-truth grounded assessment explanation"
        json missing_fields "JSON array of missing complaint fields"
        float confidence "Confidence score between 0.0 and 1.0"
        text recommended_action "Decision-support recommendation"
        datetime created_at "Timestamp when assessment was generated"
    }
```

---

## Detailed Schema Specification

### 1. `Complaint` Entity Table (`complaints`)

Stores extracted facts regarding customer complaints.

| Field Name | DB Column Type | Nullable | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `UUID` | No | `uuid.uuid4()` | Primary Key UUID identifier. |
| `complaint_source` | `VARCHAR` | Yes | `NULL` | Source channel (e.g., `"Hospital Pharmacy Report"`). |
| `customer_name` | `VARCHAR` | Yes | `NULL` | Name of customer or entity reporting complaint. |
| `product_name` | `VARCHAR` | Yes | `NULL` | Brand or active drug product name. |
| `product_strength_grade` | `VARCHAR` | Yes | `NULL` | Dosage strength (e.g., `"500 mg"`). |
| `batch_number` | `VARCHAR` | Yes | `NULL` | Production lot/batch number. |
| `manufacturing_date` | `DATE` | Yes | `NULL` | Date of manufacture (`YYYY-MM-DD`). |
| `expiry_date` | `DATE` | Yes | `NULL` | Expiration date (`YYYY-MM-DD`). |
| `quantity_affected` | `NUMERIC` | Yes | `NULL` | Definite numeric quantity affected. |
| `complaint_type` | `VARCHAR` | Yes | `NULL` | Category of issue (e.g., `"Discoloration"`). |
| `complaint_date` | `DATE` | Yes | `NULL` | Date of initial reporting (`YYYY-MM-DD`). |
| `detailed_complaint_description` | `TEXT` | Yes | `NULL` | Detailed narrative of reported issue. |
| `initial_severity` | `VARCHAR` | Yes | `NULL` | Severity reported during intake. |
| `priority` | `VARCHAR` | Yes | `NULL` | Priority assigned at intake. |
| `created_at` | `DATETIME` | No | `utcnow()` | Record creation timestamp. |
| `updated_at` | `DATETIME` | No | `utcnow()` | Record last updated timestamp. |

#### Field Constraints & Nullability Policy
- **Nullable by Design**: In compliance with pharmaceutical audit standards, every field on `Complaint` (excluding system IDs and timestamps) is nullable. Missing or unknown information **must remain NULL** rather than being assigned default placeholder text like `"Unknown"`, `"N/A"`, or guessed dates.

---

### 2. `RiskAssessment` Entity Table (`risk_assessments`)

Stores AI-generated decision support assessments associated with a specific complaint.

| Field Name | DB Column Type | Nullable | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `UUID` | No | `uuid.uuid4()` | Primary Key UUID identifier. |
| `complaint_id` | `UUID` | No | N/A | Foreign Key referencing `complaints.id`. |
| `severity` | `VARCHAR` | Yes | `NULL` | AI-evaluated risk level (`low`, `medium`, `high`, `critical`). |
| `rationale` | `TEXT` | Yes | `NULL` | Technical explanation grounded in complaint facts. |
| `missing_fields` | `JSON` | Yes | `[]` | List of field names that remain NULL on `Complaint`. |
| `confidence` | `FLOAT` | Yes | `NULL` | AI confidence score ($0.0 \le \text{confidence} \le 1.0$). |
| `recommended_action` | `TEXT` | Yes | `NULL` | Suggested QA action (e.g., `"Quarantine stock"`). |
| `created_at` | `DATETIME` | No | `utcnow()` | Assessment generation timestamp. |

---

## Entity Relationships & Data Integrity

```mermaid
classDiagram
    class Base {
        <<DeclarativeBase>>
    }

    class Complaint {
        +UUID id
        +String complaint_source
        +String customer_name
        +String product_name
        +String product_strength_grade
        +String batch_number
        +Date manufacturing_date
        +Date expiry_date
        +Numeric quantity_affected
        +String complaint_type
        +Date complaint_date
        +Text detailed_complaint_description
        +String initial_severity
        +String priority
        +DateTime created_at
        +DateTime updated_at
        +List~RiskAssessment~ risk_assessments
    }

    class RiskAssessment {
        +UUID id
        +UUID complaint_id
        +String severity
        +Text rationale
        +JSON missing_fields
        +Float confidence
        +Text recommended_action
        +DateTime created_at
        +Complaint complaint
    }

    Base <|-- Complaint
    Base <|-- RiskAssessment
    Complaint "1" *-- "0..*" RiskAssessment : cascade="all, delete-orphan"
```

### Relationship Design Rationale
1. **Separation of Facts and Decisions**: Factual metadata belongs strictly to `Complaint`. Interpretations, risk ratings, and recommended actions belong to `RiskAssessment`.
2. **Historical Audit Traceability**: Storing risk assessments as a separate child table allows maintaining historical assessments over time if a complaint record undergoes subsequent QA reviews.

---

## Database Connection & Session Management

Database interactions are managed in `backend/app/db/database.py`.

### Connection Configuration
The database URL is resolved from the environment variable `DATABASE_URL`:

- **Production / PostgreSQL**: `postgresql+psycopg://user:password@localhost:5432/aivoa_complaints`
- **Development / SQLite**: `sqlite:///./aivoa.db`

### Session Lifecycle (`get_db`)
FastAPI uses a generator dependency to manage request session boundaries:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Schema Creation (`init_db`)
Tables can be created programmatically on startup or via CLI:

```python
def init_db():
    Base.metadata.create_all(bind=engine)
```
*(Note: `init_db()` is decoupled from app startup so database connection errors do not prevent the API server from booting).*
