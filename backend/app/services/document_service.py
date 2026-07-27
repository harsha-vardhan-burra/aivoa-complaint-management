import io
import os
from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_EXTRACTED_CHARACTERS = 15000         # 15,000 chars (~3000 words)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".eml"}


class DocumentValidationError(Exception):
    """Raised when file validation or text extraction fails."""
    pass


def validate_and_extract_document_text(filename: str, content_bytes: bytes) -> str:
    """Validate file metadata/binary content and extract raw text.

    Enforces strict server-side validation:
    - Allowed extension (.pdf, .txt, .eml)
    - Non-empty binary content
    - File size <= 10MB
    - Unencrypted, valid PDF with extractable text stream
    - Extracted text length <= 15,000 characters (no silent truncation)
    """
    if not content_bytes or len(content_bytes) == 0:
        raise DocumentValidationError("Uploaded file is empty (0 bytes).")

    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(content_bytes) / (1024 * 1024)
        raise DocumentValidationError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed upload limit of 10 MB."
        )

    _, ext = os.path.splitext(filename or "")
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise DocumentValidationError(
            f"Unsupported file format '{ext_lower}'. Supported formats are: {allowed_str}."
        )

    if ext_lower == ".pdf":
        extracted_text = _extract_pdf_text(content_bytes)
    else:
        # .txt or .eml
        extracted_text = _extract_plain_text(content_bytes)

    extracted_text = extracted_text.strip()

    if not extracted_text:
        raise DocumentValidationError(
            "Uploaded document contains no extractable text. "
            "Please provide a text-based PDF or paste complaint details manually."
        )

    if len(extracted_text) > MAX_EXTRACTED_CHARACTERS:
        raise DocumentValidationError(
            f"Extracted document content exceeds the supported limit of {MAX_EXTRACTED_CHARACTERS} characters "
            f"(found {len(extracted_text)} characters). Please provide a shorter document."
        )

    return extracted_text


def _extract_pdf_text(content_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content_bytes))
        if reader.is_encrypted:
            raise DocumentValidationError("PDF file is encrypted or password-protected and cannot be read.")

        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n\n".join(pages_text)
    except PyPdfError as exc:
        raise DocumentValidationError(f"Invalid or corrupt PDF document: {str(exc)}")
    except DocumentValidationError:
        raise
    except Exception as exc:
        raise DocumentValidationError(f"Failed to parse PDF document: {str(exc)}")


def _extract_plain_text(content_bytes: bytes) -> str:
    try:
        return content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content_bytes.decode("latin-1")
        except Exception as exc:
            raise DocumentValidationError(f"Failed to decode text file: {str(exc)}")
