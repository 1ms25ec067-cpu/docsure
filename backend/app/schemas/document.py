from pydantic import BaseModel


class DocumentResponse(BaseModel):

    document_id: str
    filename: str
    document_type: str
    size_bytes: int
    status: str


class DocumentValidationResult(BaseModel):

    document_id: str
    filename: str
    document_type: str
    size_bytes: int
    max_size_bytes: int

    file_type_valid: bool
    readable: bool
    size_valid: bool

    status: str
    reason: str | None = None