from pathlib import Path

from app.documents.transformer import DocumentTransformer
from app.documents.validator import DocumentValidator
from app.verification.policies import RECOVERY_POLICIES
from app.verification.store import evidence_store


class RecoveryEngine:

    def __init__(self):
        self.validator = DocumentValidator()
        self.transformer = DocumentTransformer()

    def get_policy(self, failure_type: str):
        return RECOVERY_POLICIES.get(
            failure_type,
            "STOP",
        )

    def add_evidence(
        self,
        source: str,
        claim: str,
        value,
        verdict: str,
        evidence_type: str,
        metadata: dict | None = None,
    ):
        return evidence_store.add(
            source=source,
            claim=claim,
            value=value,
            verdict=verdict,
            evidence_type=evidence_type,
            metadata=metadata,
        )

    def recover(
        self,
        failure_type: str,
        file_path: str | None = None,
    ):
        policy = self.get_policy(
            failure_type
        )

        if policy == "HUMAN":
            self.add_evidence(
                source="recovery_policy",
                claim=(
                    "This failure requires "
                    "human intervention."
                ),
                value=failure_type,
                verdict="HUMAN_REQUIRED",
                evidence_type="RECOVERY_POLICY",
            )

            return {
                "failure_type": failure_type,
                "policy": "HUMAN",
                "status": "HUMAN_REVIEW_REQUIRED",
                "requires_human": True,
                "evidence": evidence_store.get_all(),
            }

        if policy == "STOP":
            self.add_evidence(
                source="recovery_policy",
                claim=(
                    "Automatic recovery is not "
                    "permitted for this failure."
                ),
                value=failure_type,
                verdict="STOP",
                evidence_type="RECOVERY_POLICY",
            )

            return {
                "failure_type": failure_type,
                "policy": "STOP",
                "status": "WORKFLOW_STOPPED",
                "requires_human": False,
                "evidence": evidence_store.get_all(),
            }

        if policy == "AUTO":
            if failure_type == "FILE_TOO_LARGE":
                return self.recover_oversized_file(
                    file_path
                )

            return {
                "failure_type": failure_type,
                "policy": "AUTO",
                "status": "RECOVERY_ALLOWED",
                "requires_human": False,
                "evidence": evidence_store.get_all(),
            }

        return {
            "failure_type": failure_type,
            "policy": "STOP",
            "status": "WORKFLOW_STOPPED",
            "requires_human": False,
            "evidence": evidence_store.get_all(),
        }

    def recover_oversized_file(
        self,
        file_path: str | None,
    ):
        if not file_path:
            return {
                "failure_type": "FILE_TOO_LARGE",
                "policy": "AUTO",
                "status": "FAILED",
                "reason": "FILE_PATH_REQUIRED",
                "evidence": evidence_store.get_all(),
            }

        input_file = Path(file_path)

        if not input_file.is_absolute():
            input_file = Path.cwd() / input_file

        if not input_file.exists():
            return {
                "failure_type": "FILE_TOO_LARGE",
                "policy": "AUTO",
                "status": "FAILED",
                "reason": "FILE_NOT_FOUND",
                "file_path": str(input_file),
                "evidence": evidence_store.get_all(),
            }

        original_validation = self.validator.validate(
            str(input_file)
        )

        self.add_evidence(
            source="document_validator",
            claim=(
                "Original document exceeds "
                "the maximum allowed size."
            ),
            value={
                "size_bytes": original_validation[
                    "size_bytes"
                ],
                "max_size_bytes": original_validation[
                    "max_size_bytes"
                ],
                "sha256": original_validation[
                    "sha256"
                ],
            },
            verdict="FAILED",
            evidence_type="VALIDATION",
            metadata={
                "reason": original_validation.get(
                    "reason"
                )
            },
        )

        output_file = (
            input_file.parent
            / f"{input_file.stem}_repaired.pdf"
        )

        if output_file.exists():
            output_file.unlink()

        transformation = self.transformer.compress_pdf(
            input_path=str(input_file),
            output_path=str(output_file),
        )

        self.add_evidence(
            source="document_transformer",
            claim="Document compression was attempted.",
            value=transformation,
            verdict=(
                "SUCCESS"
                if transformation["status"] == "SUCCESS"
                else "FAILED"
            ),
            evidence_type="TRANSFORMATION",
        )

        if transformation["status"] != "SUCCESS":
            return {
                "failure_type": "FILE_TOO_LARGE",
                "policy": "AUTO",
                "status": "RECOVERY_FAILED",
                "action": "PDF_COMPRESSION",
                "original_file": str(input_file),
                "transformation": transformation,
                "evidence": evidence_store.get_all(),
            }

        repaired_validation = self.validator.validate(
            str(output_file)
        )

        verified = (
            repaired_validation["status"]
            == "VERIFIED"
        )

        self.add_evidence(
            source="document_validator",
            claim=(
                "Repaired document satisfies "
                "all current file validation rules."
            ),
            value={
                "size_bytes": repaired_validation[
                    "size_bytes"
                ],
                "max_size_bytes": repaired_validation[
                    "max_size_bytes"
                ],
                "size_valid": repaired_validation[
                    "size_valid"
                ],
                "readable": repaired_validation[
                    "readable"
                ],
                "page_count": repaired_validation[
                    "page_count"
                ],
                "sha256": repaired_validation[
                    "sha256"
                ],
            },
            verdict=(
                "VERIFIED"
                if verified
                else "FAILED"
            ),
            evidence_type="REVALIDATION",
        )

        if verified:
            self.add_evidence(
                source="recovery_engine",
                claim=(
                    "The oversized document was "
                    "successfully repaired and verified."
                ),
                value="RECOVERED",
                verdict="VERIFIED",
                evidence_type="FINAL_VERDICT",
            )

            return {
                "failure_type": "FILE_TOO_LARGE",
                "policy": "AUTO",
                "status": "RECOVERED",
                "action": "PDF_COMPRESSED",
                "original_file": str(input_file),
                "repaired_file": str(output_file),
                "transformation": transformation,
                "validation": repaired_validation,
                "evidence": evidence_store.get_all(),
                "message": (
                    "Document was repaired "
                    "and independently verified."
                ),
            }

        self.add_evidence(
            source="recovery_engine",
            claim=(
                "The recovery attempt did not "
                "produce a valid document."
            ),
            value="RECOVERY_FAILED",
            verdict="FAILED",
            evidence_type="FINAL_VERDICT",
        )

        return {
            "failure_type": "FILE_TOO_LARGE",
            "policy": "AUTO",
            "status": "RECOVERY_FAILED",
            "action": "PDF_COMPRESSED",
            "original_file": str(input_file),
            "repaired_file": str(output_file),
            "transformation": transformation,
            "validation": repaired_validation,
            "evidence": evidence_store.get_all(),
            "message": (
                "Recovery was attempted, but the "
                "repaired document did not pass validation."
            ),
        }