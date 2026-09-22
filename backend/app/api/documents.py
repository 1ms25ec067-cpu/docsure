from pathlib import Path
from uuid import uuid4
import re

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agent.recovery import RecoveryEngine
from app.documents.extractor import DocumentExtractor
from app.documents.validator import DocumentValidator
from app.verification.store import evidence_store

router = APIRouter(prefix="/documents", tags=["Documents"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
validator = DocumentValidator()
extractor = DocumentExtractor()
recovery_engine = RecoveryEngine()

def find_document_file(document_id: str) -> Path | None:
    matches = list(UPLOAD_DIR.glob(f"{document_id}_*"))
    if not matches:
        return None
    return matches[0]

def resolve_file_path(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    document_id = f"DOC-{uuid4().hex[:8].upper()}"
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIR / f"{document_id}_{safe_filename}"
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except OSError as error:
        raise HTTPException(status_code=500, detail=f"Could not save file: {error}") from error
    validation = validator.validate(str(file_path))
    return {
        "document_id": document_id,
        "filename": safe_filename,
        "stored_path": str(file_path),
        "validation": validation,
    }

@router.post("/extract")
def extract_document(file_path: str):
    path = resolve_file_path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail={"status":"FAILED","reason":"FILE_NOT_FOUND","file_path":str(path)})
    result = extractor.extract(str(path))
    if result["status"] == "FAILED":
        raise HTTPException(status_code=400, detail=result)
    return result

@router.post("/recover")
def recover_document(document_id: str, failure_type: str):
    path = find_document_file(document_id)
    if path is None:
        raise HTTPException(status_code=404, detail={"status":"FAILED","reason":"DOCUMENT_NOT_FOUND","document_id":document_id})
    result = recovery_engine.recover(failure_type=failure_type, file_path=str(path))
    result["document_id"] = document_id
    result["original_file"] = str(path)
    return result

@router.get("/verified-fields")
def verified_document_fields(file_path: str):
    path = resolve_file_path(file_path)

    if not path.exists():
        raise HTTPException(status_code=404, detail={"status": "FAILED", "reason": "FILE_NOT_FOUND", "file_path": str(path)})

    validation = validator.validate(str(path))
    if validation.get("status") != "VERIFIED":
        raise HTTPException(
            status_code=400,
            detail={
                "status": "BLOCKED",
                "reason": validation.get("reason", "DOCUMENT_NOT_VERIFIED"),
                "validation": validation,
            },
        )

    extraction = extractor.extract(str(path))
    if extraction.get("status") != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail={
                "status": "BLOCKED",
                "reason": extraction.get("reason", "DOCUMENT_EXTRACTION_FAILED"),
                "extraction": extraction,
            },
        )

    # If extraction used OCR, record DOCUMENT_OCR evidence
    if extraction.get("extraction_method") == "OCR":
        evidence_store.add(
            source="docsure_document_extractor",
            claim="Application fields were extracted from the verified document using OCR.",
            value={
                "file_path": str(path),
                "extraction_method": "OCR",
                "page_count": extraction.get("page_count", 1),
            },
            verdict="VERIFIED",
            evidence_type="DOCUMENT_OCR",
            metadata={
                "extraction_method": "OCR",
                "document_hash": validation.get("sha256"),
                "page_count": extraction.get("page_count", 1),
            },
        )

    text = extraction.get("text", "")

    KNOWN_LABELS = [
        "school name", "roll number", "date of birth", "dob", "birth date",
        "year of passing", "board", "father", "mother", "annual family income",
        "income in words", "document type", "certificate number", "issue date",
        "purpose", "declaration", "address", "subject code", "subject name",
        "theory", "practical", "total", "marks obtained",
    ]

    def is_label_name(val: str) -> bool:
        v = val.lower().strip()
        return any(v == lbl or v.startswith(lbl) for lbl in KNOWN_LABELS)

    def clean_extracted_value(val: str) -> str:
        if not val:
            return ""
        for lbl in KNOWN_LABELS:
            split_parts = re.split(rf"[\s\t]+{lbl}[\s\t]*[:\-]", val, flags=re.IGNORECASE)
            if len(split_parts) > 1:
                val = split_parts[0]

        val = re.split(r"\s{2,}|\t|\n", val)[0]
        val = re.sub(r"^[ :\-\t]+", "", val)
        return val.strip()

    fields = {}

    # 1. Full Name
    name_patterns = [
        r"(?:full\s*name|student\s*name|applicant\s*name|candidate\s*name)\s*[:\-]\s*([^\n\r]+)",
        r"(?:name)\s*[:\-]\s*([^\n\r]+)",
        r"(?:full\s*name|student\s*name|applicant\s*name|candidate\s*name)\s*\n+([^\n\r]+)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_name = clean_extracted_value(match.group(1))
            cleaned_name = re.sub(r"[^a-zA-Z\s\.\'-]", "", raw_name).strip()
            if cleaned_name and len(cleaned_name) > 1 and not is_label_name(cleaned_name):
                fields["Full Name"] = cleaned_name
                break

    # 2. Date of Birth
    dob_patterns = [
        r"(?:date\s*of\s*birth|dob|birth\s*date)\s*[:\-]\s*([^\n\r]+)",
        r"(?:date\s*of\s*birth|dob|birth\s*date)\s*\n+([^\n\r]+)",
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_dob = clean_extracted_value(match.group(1))
            date_match = re.search(
                r"(\d{1,2}(?:st|nd|rd|th)?[\s\/\-\.](?:January|February|March|April|May|June|July|August|September|October|November|December|[A-Za-z]{3}|\d{1,2})[\s\/\-\.]\d{2,4}|\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})",
                raw_dob,
                re.IGNORECASE,
            )
            if date_match:
                fields["Date of Birth"] = date_match.group(1).strip()
                break
            elif raw_dob and not is_label_name(raw_dob):
                fields["Date of Birth"] = raw_dob
                break

    # 3. Email Address
    email_patterns = [
        r"(?:email\s*(?:address)?|e-mail)\s*[:\-]\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
        r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})",
    ]
    for pattern in email_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["Email Address"] = match.group(1).strip()
            break

    # 4. Phone Number
    phone_patterns = [
        r"(?:phone|mobile|contact|phone\s*number|mobile\s*number|contact\s*number)\s*[:\-]\s*(\+?[0-9][0-9\s\-]{7,}[0-9])",
        r"(?:phone|mobile|contact)\s*\n+(\+?[0-9][0-9\s\-]{7,}[0-9])",
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_phone = clean_extracted_value(match.group(1))
            if raw_phone and not is_label_name(raw_phone):
                fields["Phone Number"] = raw_phone
                break

    if not fields:
        evidence_store.add(
            source="docsure_document_extractor",
            claim="Verified application fields were extracted from the document.",
            value={"file_path": str(path), "fields": {}},
            verdict="BLOCKED",
            evidence_type="DOCUMENT_FIELD_EXTRACTION",
            metadata={"reason": "NO_SUPPORTED_APPLICATION_FIELDS_FOUND", "document_hash": validation.get("sha256")},
        )
        raise HTTPException(
            status_code=400,
            detail={
                "status": "BLOCKED",
                "reason": "NO_SUPPORTED_APPLICATION_FIELDS_FOUND",
                "message": "The verified document does not contain supported labeled application fields such as Full Name, Date of Birth, Email Address, or Phone Number.",
            },
        )

    evidence = evidence_store.add(
        source="docsure_document_extractor",
        claim="Verified application fields were extracted from the document.",
        value={"file_path": str(path), "fields": fields},
        verdict="VERIFIED",
        evidence_type="DOCUMENT_FIELD_EXTRACTION",
        metadata={
            "document_hash": validation.get("sha256"),
            "validation_status": validation.get("status"),
            "extraction_method": extraction.get("extraction_method", "TEXT"),
        },
    )

    return {
        "status": "VERIFIED",
        "source": "UPLOADED_DOCUMENT",
        "document": {
            "filename": path.name,
            "sha256": validation.get("sha256"),
            "extraction_method": extraction.get("extraction_method", "TEXT"),
        },
        "fields": fields,
        "evidence": evidence,
    }


