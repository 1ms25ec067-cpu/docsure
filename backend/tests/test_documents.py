from pathlib import Path

from app.documents.validator import (
    DocumentValidator,
)


def test_missing_document():

    validator = DocumentValidator()

    result = validator.validate(
        "file_that_does_not_exist.pdf"
    )

    assert result["status"] == "FAILED"
    assert result["reason"] == "FILE_NOT_FOUND"