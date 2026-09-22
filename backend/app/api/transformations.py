from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.documents.transformer import DocumentTransformer


router = APIRouter(
    prefix="/transformations",
    tags=["Transformations"],
)

transformer = DocumentTransformer()


@router.post("/to-pdf")
def transform_to_pdf(
    file_path: str,
    max_size: int = 5 * 1024 * 1024,
):
    path = Path(file_path)

    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "file_path": str(path),
            },
        )

    result = transformer.to_pdf(
        input_path=str(path),
        max_size=max_size,
    )

    if result["status"] == "FAILED":
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result