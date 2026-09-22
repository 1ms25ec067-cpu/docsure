import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.documents.extractor import DocumentExtractor
from app.documents.validator import DocumentValidator
from app.verification.store import evidence_store

client = TestClient(app)


def test_document_validator_on_real_pdf():
    validator = DocumentValidator()
    # Test on existing income certificate demo
    pdf_path = Path("uploads/DOC-1DD97BBF_fictional_income_certificate_demo.pdf")
    if pdf_path.exists():
        result = validator.validate(str(pdf_path))
        assert result["status"] == "VERIFIED"
        assert result["file_type_valid"] is True
        assert result["readable"] is True
        assert result["size_valid"] is True
        assert "sha256" in result


def test_document_extractor_text_layer():
    extractor = DocumentExtractor()
    pdf_path = Path("uploads/DOC-1DD97BBF_fictional_income_certificate_demo.pdf")
    if pdf_path.exists():
        result = extractor.extract(str(pdf_path))
        assert result["status"] == "SUCCESS"
        assert result["extraction_method"] == "TEXT"
        assert "Pendyala Karthik" in result["text"]


def test_document_extractor_ocr_fallback():
    extractor = DocumentExtractor()
    scanned_path = Path("uploads/DOC-4EE0C51D_png2pdf.pdf")
    if scanned_path.exists():
        result = extractor.extract(str(scanned_path))
        assert result["status"] == "SUCCESS"
        assert result["extraction_method"] == "OCR"
        assert "Ananya Rao" in result["text"] or "MARKSHEET" in result["text"]


def test_verified_fields_endpoint_text_and_ocr():
    evidence_store.clear()

    # 1. Text PDF
    pdf_path = Path("uploads/DOC-1DD97BBF_fictional_income_certificate_demo.pdf")
    if pdf_path.exists():
        res = client.get("/documents/verified-fields", params={"file_path": str(pdf_path)})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "VERIFIED"
        assert data["fields"].get("Full Name") == "Pendyala Karthik"
        assert data["document"]["extraction_method"] == "TEXT"

    # 2. Scanned PDF (OCR)
    scanned_path = Path("uploads/DOC-4EE0C51D_png2pdf.pdf")
    if scanned_path.exists():
        res = client.get("/documents/verified-fields", params={"file_path": str(scanned_path)})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "VERIFIED"
        assert data["fields"].get("Full Name") == "Ananya Rao"
        assert data["fields"].get("Date of Birth") == "17 February 2008"
        assert data["document"]["extraction_method"] == "OCR"

        # Verify DOCUMENT_OCR evidence exists
        all_ev = evidence_store.get_all()
        ocr_ev = [e for e in all_ev if e["evidence_type"] == "DOCUMENT_OCR"]
        assert len(ocr_ev) > 0
        assert ocr_ev[0]["verdict"] == "VERIFIED"
