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
        raise HTTPException(status_code=404, detail={"status":"FAILED","reason":"FILE_NOT_FOUND","file_path":str(path)})

    validation = validator.validate(str(path))
    if validation.get("status") != "VERIFIED":
        raise HTTPException(status_code=400, detail={"status":"BLOCKED","reason":validation.get("reason","DOCUMENT_NOT_VERIFIED"),"validation":validation})

    extraction = extractor.extract(str(path))
    if extraction.get("status") != "SUCCESS":
        raise HTTPException(status_code=400, detail={"status":"BLOCKED","reason":"DOCUMENT_EXTRACTION_FAILED","extraction":extraction})

    text = extraction.get("text", "")

    def find_value(patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                value = re.split(r"\s{2,}|\n", value)[0].strip()
                if value:
                    return value
        return None

    fields = {}
    full_name = find_value([r"(?:full\s*name|name)\s*[:\-]\s*([^\n]+)", r"applicant\s*name\s*[:\-]\s*([^\n]+)"])
    dob = find_value([r"(?:date\s*of\s*birth|dob)\s*[:\-]\s*([^\n]+)", r"birth\s*date\s*[:\-]\s*([^\n]+)"])
    email = find_value([r"(?:email\s*(?:address)?)\s*[:\-]\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})"])
    phone = find_value([r"(?:phone|mobile|phone\s*number|mobile\s*number)\s*[:\-]\s*(\+?[0-9][0-9\s\-]{7,}[0-9])"])

    if full_name: fields["Full Name"] = full_name
    if dob: fields["Date of Birth"] = dob
    if email: fields["Email Address"] = email
    if phone: fields["Phone Number"] = phone

    if not fields:
        evidence_store.add(source="docsure_document_extractor", claim="Verified application fields were extracted from the document.", value={"file_path":str(path),"fields":{}}, verdict="BLOCKED", evidence_type="DOCUMENT_FIELD_EXTRACTION", metadata={"reason":"NO_SUPPORTED_APPLICATION_FIELDS_FOUND","document_hash":validation.get("sha256")})
        raise HTTPException(status_code=400, detail={"status":"BLOCKED","reason":"NO_SUPPORTED_APPLICATION_FIELDS_FOUND","message":"The verified document does not contain supported labeled application fields such as Full Name, Date of Birth, Email Address, or Phone Number."})

    evidence = evidence_store.add(source="docsure_document_extractor", claim="Verified application fields were extracted from the document.", value={"file_path":str(path),"fields":fields}, verdict="VERIFIED", evidence_type="DOCUMENT_FIELD_EXTRACTION", metadata={"document_hash":validation.get("sha256"),"validation_status":validation.get("status")})

    return {"status":"VERIFIED","source":"UPLOADED_DOCUMENT","document":{"filename":path.name,"sha256":validation.get("sha256")},"fields":fields,"evidence":evidence}
