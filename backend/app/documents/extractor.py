import io
import os
import shutil
from pathlib import Path

import fitz
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


class DocumentExtractor:
    """
    Two-stage document text extraction engine:
    1. Direct PDF text layer extraction.
    2. Automatic OCR fallback using Tesseract when the text layer
       is empty or insufficient (e.g., scanned/image documents).
    """

    def __init__(self):
        self._configure_tesseract()

    def _configure_tesseract(self):
        if pytesseract is None:
            return

        tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if tesseract_cmd and Path(tesseract_cmd).exists():
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            return

        which_tesseract = shutil.which("tesseract")
        if which_tesseract:
            pytesseract.pytesseract.tesseract_cmd = which_tesseract
            return

        # Common Windows installation locations
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for candidate in common_paths:
            if candidate and Path(candidate).exists():
                pytesseract.pytesseract.tesseract_cmd = candidate
                return

    def _is_tesseract_available(self) -> bool:
        if pytesseract is None:
            return False
        try:
            self._configure_tesseract()
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

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

            full_text = "\n".join(
                page["text"]
                for page in pages
            )

            # Check if normal text extraction yielded sufficient content
            # A useful document text usually has at least 15-20 characters.
            text_is_useful = len(full_text.strip()) >= 20

            if text_is_useful:
                document.close()
                return {
                    "status": "SUCCESS",
                    "filename": path.name,
                    "page_count": page_count,
                    "text": full_text,
                    "pages": pages,
                    "extraction_method": "TEXT",
                }

            # If text is empty or insufficient, trigger OCR fallback
            if not self._is_tesseract_available():
                document.close()
                return {
                    "status": "FAILED",
                    "reason": "OCR_UNAVAILABLE",
                    "message": "Direct PDF text extraction yielded insufficient text, and Tesseract OCR is not available.",
                    "filename": path.name,
                    "page_count": page_count,
                    "text": full_text,
                    "pages": pages,
                    "extraction_method": "FAILED",
                }

            ocr_pages = []
            for page_number, page in enumerate(
                document,
                start=1,
            ):
                pixmap = page.get_pixmap(dpi=200)
                image_bytes = pixmap.tobytes("png")
                pil_image = Image.open(io.BytesIO(image_bytes))
                page_ocr_text = pytesseract.image_to_string(pil_image)

                ocr_pages.append(
                    {
                        "page": page_number,
                        "text": page_ocr_text,
                    }
                )

            document.close()

            ocr_full_text = "\n".join(
                page["text"]
                for page in ocr_pages
            )

            return {
                "status": "SUCCESS",
                "filename": path.name,
                "page_count": page_count,
                "text": ocr_full_text,
                "pages": ocr_pages,
                "extraction_method": "OCR",
            }

        except Exception as error:
            return {
                "status": "FAILED",
                "reason": str(error),
            }