from hashlib import sha256
from pathlib import Path

import fitz


DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024


class DocumentValidator:

    def calculate_hash(self, file_path: str) -> str:
        path = Path(file_path)

        file_hash = sha256()

        with path.open("rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                file_hash.update(chunk)

        return file_hash.hexdigest()

    def validate(
        self,
        file_path: str,
        document_type: str = "UNKNOWN",
        max_size: int = DEFAULT_MAX_FILE_SIZE,
    ):
        path = Path(file_path)

        if not path.exists():
            return {
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
            }

        size_bytes = path.stat().st_size

        file_type_valid = (
            path.suffix.lower() == ".pdf"
        )

        size_valid = (
            size_bytes <= max_size
        )

        readable = False
        page_count = 0

        if file_type_valid:
            try:
                document = fitz.open(
                    str(path)
                )

                page_count = len(document)
                readable = page_count > 0

                document.close()

            except Exception:
                readable = False

        file_hash = self.calculate_hash(
            str(path)
        )

        status = "VERIFIED"
        reason = None

        if not file_type_valid:
            status = "FAILED"
            reason = "INVALID_FILE_TYPE"

        elif not readable:
            status = "FAILED"
            reason = "FILE_NOT_READABLE"

        elif not size_valid:
            status = "FAILED"
            reason = "FILE_TOO_LARGE"

        return {
            "filename": path.name,
            "document_type": document_type,
            "size_bytes": size_bytes,
            "max_size_bytes": max_size,
            "file_type_valid": file_type_valid,
            "readable": readable,
            "size_valid": size_valid,
            "page_count": page_count,
            "sha256": file_hash,
            "status": status,
            "reason": reason,
        }