from pathlib import Path

import fitz


class DocumentExtractor:

    def extract(
        self,
        file_path: str,
    ):
        path = Path(file_path)

        if not path.exists():
            return {
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
            }

        try:
            document = fitz.open(
                str(path)
            )

            pages = []

            for page_number, page in enumerate(
                document,
                start=1,
            ):
                pages.append(
                    {
                        "page": page_number,
                        "text": page.get_text(),
                    }
                )

            page_count = len(document)

            document.close()

            full_text = "\n".join(
                page["text"]
                for page in pages
            )

            return {
                "status": "SUCCESS",
                "filename": path.name,
                "page_count": page_count,
                "text": full_text,
                "pages": pages,
            }

        except Exception as error:
            return {
                "status": "FAILED",
                "reason": str(error),
            }