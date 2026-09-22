from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agent.recovery import RecoveryEngine
from app.documents.extractor import DocumentExtractor
from app.documents.validator import DocumentValidator


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# STORAGE
# ============================================================

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SERVICES
# ============================================================

validator = DocumentValidator()
extractor = DocumentExtractor()
recovery_engine = RecoveryEngine()


# ============================================================
# HELPERS
# ============================================================

def find_document_file(document_id: str) -> Path | None:
    """
    Find the uploaded file belonging to a DocuSure document ID.

    Uploaded files are stored as:

        DOC-XXXXXXXX_original_filename.pdf
    """

    matches = list(
        UPLOAD_DIR.glob(
            f"{document_id}_*"
        )
    )

    if not matches:
        return None

    # Use the first matching artifact.
    # A document ID is unique, so normally there
    # should only be one original file.
    return matches[0]


def resolve_file_path(file_path: str) -> Path:
    """
    Resolve relative or absolute file paths safely.
    """

    path = Path(file_path)

    if not path.is_absolute():
        path = Path.cwd() / path

    return path


# ============================================================
# UPLOAD
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload a document and immediately validate it.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    document_id = (
        f"DOC-{uuid4().hex[:8].upper()}"
    )

    safe_filename = Path(
        file.filename
    ).name

    file_path = (
        UPLOAD_DIR
        / f"{document_id}_{safe_filename}"
    )

    try:
        content = await file.read()

        file_path.write_bytes(
            content
        )

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not save file: {error}"
            ),
        ) from error

    validation = validator.validate(
        str(file_path)
    )

    return {
        "document_id": document_id,
        "filename": safe_filename,
        "stored_path": str(file_path),
        "validation": validation,
    }


# ============================================================
# EXTRACT
# ============================================================

@router.post("/extract")
def extract_document(
    file_path: str,
):
    """
    Extract text from an uploaded PDF.

    Example:

        uploads/DOC-12345678_document.pdf
    """

    path = resolve_file_path(
        file_path
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "file_path": str(path),
            },
        )

    result = extractor.extract(
        str(path)
    )

    if result["status"] == "FAILED":
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result


# ============================================================
# RECOVERY
# ============================================================

@router.post("/recover")
def recover_document(
    document_id: str,
    failure_type: str,
):
    """
    Attempt controlled self-healing for an uploaded document.

    The user provides the DocuSure document ID instead
    of manually providing the filesystem path.

    Example:

        document_id = DOC-6E722D3C
        failure_type = FILE_TOO_LARGE
    """

    # --------------------------------------------------------
    # Find the uploaded document automatically
    # --------------------------------------------------------

    path = find_document_file(
        document_id
    )

    if path is None:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "FAILED",
                "reason": "DOCUMENT_NOT_FOUND",
                "document_id": document_id,
            },
        )

    # --------------------------------------------------------
    # Run recovery engine
    # --------------------------------------------------------

    result = recovery_engine.recover(
        failure_type=failure_type,
        file_path=str(path),
    )

    # --------------------------------------------------------
    # Add document identity to the result
    # --------------------------------------------------------

    result["document_id"] = document_id
    result["original_file"] = str(path)

    return result