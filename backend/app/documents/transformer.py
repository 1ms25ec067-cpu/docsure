from pathlib import Path
from typing import Any

import fitz


class DocumentTransformer:
    """
    Deterministic document transformation engine.

    Supported transformations:

    - PDF -> compressed PDF
    - image -> PDF
    - supported document -> PDF when PyMuPDF can open it

    Important:
    Transformation does NOT mean verification.

    Every generated file must be validated again.
    """

    TARGET_MAX_SIZE = 5 * 1024 * 1024

    # Compression is attempted from higher quality to stronger
    # compression. The engine stops as soon as the output is
    # within the maximum allowed size.
    COMPRESSION_LEVELS = [
        (120, 55),
        (100, 45),
        (85, 35),
        (75, 30),
        (65, 25),
    ]

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    PDF_EXTENSIONS = {
        ".pdf",
    }

    PDF_CONVERTIBLE_EXTENSIONS = {
        ".docx",
        ".doc",
        ".pptx",
        ".xlsx",
        ".txt",
        ".html",
        ".htm",
        ".epub",
        ".mobi",
    }

    def transform(
        self,
        input_path: str,
        target_format: str,
        output_path: str | None = None,
        max_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Transform a document into the requested format.

        target_format examples:
            PDF
            JPG
            PNG

        Currently PDF is the primary target because
        scholarship/application portals commonly require PDF.
        """

        source = Path(input_path)

        if not source.exists():
            return {
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "input_path": str(source),
            }

        target = target_format.upper().strip()

        if target == "PDF":
            return self.to_pdf(
                input_path=str(source),
                output_path=output_path,
                max_size=max_size,
            )

        return {
            "status": "FAILED",
            "reason": "UNSUPPORTED_TARGET_FORMAT",
            "target_format": target,
        }

    def to_pdf(
        self,
        input_path: str,
        output_path: str | None = None,
        max_size: int | None = None,
    ) -> dict[str, Any]:

        source = Path(input_path)

        if not source.exists():
            return {
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "input_path": str(source),
            }

        max_size = (
            max_size
            if max_size is not None
            else self.TARGET_MAX_SIZE
        )

        suffix = source.suffix.lower()

        if suffix == ".pdf":
            return self._prepare_pdf(
                source=source,
                output_path=output_path,
                max_size=max_size,
            )

        if suffix in self.IMAGE_EXTENSIONS:
            return self._image_to_pdf(
                source=source,
                output_path=output_path,
                max_size=max_size,
            )

        if suffix in self.PDF_CONVERTIBLE_EXTENSIONS:
            return self._document_to_pdf(
                source=source,
                output_path=output_path,
                max_size=max_size,
            )

        return {
            "status": "FAILED",
            "reason": "UNSUPPORTED_SOURCE_FORMAT",
            "source_format": suffix,
        }

    def _prepare_pdf(
        self,
        source: Path,
        output_path: str | None,
        max_size: int,
    ) -> dict[str, Any]:

        output = self._default_output(
            source,
            output_path,
            suffix="_converted",
        )

        original_size = source.stat().st_size

        # No transformation required.
        if original_size <= max_size:
            return {
                "status": "SUCCESS",
                "action": "NO_CONVERSION_REQUIRED",
                "input_file": str(source),
                "output_file": str(source),
                "source_format": "PDF",
                "target_format": "PDF",
                "original_size": original_size,
                "final_size": original_size,
                "max_size": max_size,
                "message": "PDF already satisfies size requirement.",
            }

        return self.compress_pdf(
            input_path=str(source),
            output_path=str(output),
            max_size=max_size,
        )

    def _image_to_pdf(
        self,
        source: Path,
        output_path: str | None,
        max_size: int,
    ) -> dict[str, Any]:

        output = self._default_output(
            source,
            output_path,
            suffix="_converted",
            extension=".pdf",
        )

        try:
            image_doc = fitz.open(
                str(source)
            )

            pdf_bytes = image_doc.convert_to_pdf()
            image_doc.close()

            pdf_doc = fitz.open(
                "pdf",
                pdf_bytes,
            )

            pdf_doc.save(
                str(output),
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            )

            pdf_doc.close()

        except Exception as error:
            return {
                "status": "FAILED",
                "action": "IMAGE_TO_PDF",
                "reason": str(error),
                "input_file": str(source),
                "output_file": str(output),
            }

        final_size = output.stat().st_size

        if final_size > max_size:
            compression = self.compress_pdf(
                input_path=str(output),
                output_path=str(output),
                max_size=max_size,
            )

            if compression["status"] != "SUCCESS":
                return {
                    "status": "FAILED",
                    "action": "IMAGE_TO_PDF",
                    "reason": "CONVERTED_PDF_TOO_LARGE",
                    "input_file": str(source),
                    "output_file": str(output),
                    "final_size": final_size,
                    "compression": compression,
                }

            final_size = output.stat().st_size

        return {
            "status": "SUCCESS",
            "action": "IMAGE_TO_PDF",
            "input_file": str(source),
            "output_file": str(output),
            "source_format": source.suffix.lower().replace(".", "").upper(),
            "target_format": "PDF",
            "original_size": source.stat().st_size,
            "final_size": final_size,
            "max_size": max_size,
            "message": "Image converted to PDF.",
        }

    def _document_to_pdf(
        self,
        source: Path,
        output_path: str | None,
        max_size: int,
    ) -> dict[str, Any]:

        output = self._default_output(
            source,
            output_path,
            suffix="_converted",
            extension=".pdf",
        )

        try:
            document = fitz.open(
                str(source)
            )

            pdf_bytes = document.convert_to_pdf()
            document.close()

            pdf_doc = fitz.open(
                "pdf",
                pdf_bytes,
            )

            pdf_doc.save(
                str(output),
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            )

            pdf_doc.close()

        except Exception as error:
            return {
                "status": "FAILED",
                "action": "DOCUMENT_TO_PDF",
                "reason": str(error),
                "input_file": str(source),
                "output_file": str(output),
            }

        final_size = output.stat().st_size

        if final_size > max_size:
            compression = self.compress_pdf(
                input_path=str(output),
                output_path=str(output),
                max_size=max_size,
            )

            if compression["status"] != "SUCCESS":
                return {
                    "status": "FAILED",
                    "action": "DOCUMENT_TO_PDF",
                    "reason": "CONVERTED_PDF_TOO_LARGE",
                    "input_file": str(source),
                    "output_file": str(output),
                    "final_size": final_size,
                    "compression": compression,
                }

            final_size = output.stat().st_size

        return {
            "status": "SUCCESS",
            "action": "DOCUMENT_TO_PDF",
            "input_file": str(source),
            "output_file": str(output),
            "source_format": source.suffix.lower().replace(".", "").upper(),
            "target_format": "PDF",
            "original_size": source.stat().st_size,
            "final_size": final_size,
            "max_size": max_size,
            "message": "Document converted to PDF.",
        }

    def compress_pdf(
        self,
        input_path: str,
        output_path: str,
        max_size: int | None = None,
    ) -> dict[str, Any]:

        source = Path(input_path)
        output = Path(output_path)

        if not source.exists():
            return {
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "input_file": str(source),
            }

        max_size = (
            max_size
            if max_size is not None
            else self.TARGET_MAX_SIZE
        )

        original_size = source.stat().st_size

        attempts = []

        for dpi, quality in self.COMPRESSION_LEVELS:

            attempt_output = output.with_name(
                f"{output.stem}_{dpi}dpi.pdf"
            )

            try:
                self._rasterize_pdf(
                    source=source,
                    output=attempt_output,
                    dpi=dpi,
                    quality=quality,
                )

                size = attempt_output.stat().st_size

                attempts.append(
                    {
                        "dpi": dpi,
                        "quality": quality,
                        "size_bytes": size,
                    }
                )

                # Target reached.
                if size <= max_size:

                    if output.exists():
                        output.unlink()

                    attempt_output.replace(output)

                    return {
                        "status": "SUCCESS",
                        "action": "PDF_COMPRESSED",
                        "method": "IMAGE_AWARE_COMPRESSION",
                        "input_file": str(source),
                        "output_file": str(output),
                        "original_size": original_size,
                        "final_size": size,
                        "max_size": max_size,
                        "target_reached": True,
                        "attempts": attempts,
                    }

                # If this attempt was too large, continue to
                # the next stronger compression level.

            except Exception as error:
                attempts.append(
                    {
                        "dpi": dpi,
                        "quality": quality,
                        "error": str(error),
                    }
                )

        # Every compression level failed to reach the limit.
        return {
            "status": "FAILED",
            "action": "PDF_COMPRESSED",
            "method": "IMAGE_AWARE_COMPRESSION",
            "input_file": str(source),
            "original_size": original_size,
            "max_size": max_size,
            "target_reached": False,
            "attempts": attempts,
        }

    @staticmethod
    def _rasterize_pdf(
        source: Path,
        output: Path,
        dpi: int,
        quality: int,
    ) -> None:

        source_doc = fitz.open(
            str(source)
        )

        result_doc = fitz.open()

        zoom = dpi / 72

        matrix = fitz.Matrix(
            zoom,
            zoom,
        )

        for page in source_doc:

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            image_bytes = pixmap.tobytes(
                "jpeg",
                jpg_quality=quality,
            )

            new_page = result_doc.new_page(
                width=page.rect.width,
                height=page.rect.height,
            )

            new_page.insert_image(
                new_page.rect,
                stream=image_bytes,
            )

        result_doc.save(
            str(output),
            garbage=4,
            deflate=True,
        )

        result_doc.close()
        source_doc.close()

    @staticmethod
    def _default_output(
        source: Path,
        output_path: str | None,
        suffix: str,
        extension: str | None = None,
    ) -> Path:

        if output_path:
            return Path(output_path)

        final_extension = (
            extension
            if extension is not None
            else source.suffix
        )

        return source.parent / (
            f"{source.stem}{suffix}{final_extension}"
        )