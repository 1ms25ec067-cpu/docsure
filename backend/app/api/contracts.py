from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.verification.evidence import EvidenceRecord
from app.verification.store import evidence_store


router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"],
)


# ============================================================
# MODELS
# ============================================================

class FieldValue(BaseModel):
    document: str = Field(min_length=1)
    field: str = Field(min_length=1)
    value: Any = None


class CrossDocumentCheck(BaseModel):
    requirement: str = Field(min_length=1)
    field: str = Field(min_length=1)
    documents: list[FieldValue] = Field(min_length=2)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value: Any) -> str:
    """
    Normalize values before comparison.

    This is intentionally conservative.
    We do not try to guess different identities.
    """

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


# ============================================================
# CROSS-DOCUMENT VERIFICATION
# ============================================================

@router.post("/cross-check")
def cross_document_check(
    data: CrossDocumentCheck,
):
    """
    Verify that a field has the same value across
    all supplied documents.

    Example:

    Name:
        Aadhaar       -> Koushik V
        Income Cert.  -> Koushik V
        Marks Card    -> Koushik V

    Result:
        VERIFIED
    """

    evidence = []

    normalized_values = [
        normalize(item.value)
        for item in data.documents
    ]

    first_value = normalized_values[0]

    all_match = all(
        value == first_value
        for value in normalized_values
    )

    # --------------------------------------------------------
    # VERIFIED
    # --------------------------------------------------------

    if all_match and first_value:
        for item in data.documents:
            record = evidence_store.add(
                source="cross_document_verifier",
                claim=(
                    f"{data.field} matches across submitted "
                    f"documents."
                ),
                value={
                    "document": item.document,
                    "field": item.field,
                    "value": item.value,
                },
                verdict="VERIFIED",
                evidence_type="CROSS_DOCUMENT",
                metadata={
                    "requirement": data.requirement,
                },
            )

            evidence.append(record)

        final = evidence_store.add(
            source="cross_document_verifier",
            claim=data.requirement,
            value={
                "field": data.field,
                "documents_checked": [
                    item.document
                    for item in data.documents
                ],
                "values": [
                    item.value
                    for item in data.documents
                ],
            },
            verdict="VERIFIED",
            evidence_type="FINAL_VERDICT",
            metadata={
                "documents_checked": len(data.documents),
                "comparison": "ALL_VALUES_MATCH",
            },
        )

        evidence.append(final)

        return {
            "status": "VERIFIED",
            "requirement": data.requirement,
            "field": data.field,
            "documents_checked": len(data.documents),
            "result": "MATCH",
            "evidence": evidence,
            "message": (
                "Requirement verified across all supplied "
                "documents."
            ),
        }

    # --------------------------------------------------------
    # CONFLICT
    # --------------------------------------------------------

    conflict_details = []

    for item in data.documents:
        conflict_details.append(
            {
                "document": item.document,
                "field": item.field,
                "value": item.value,
            }
        )

    conflict_evidence = evidence_store.add(
        source="cross_document_verifier",
        claim=(
            f"{data.field} is consistent across all "
            f"submitted documents."
        ),
        value=conflict_details,
        verdict="FAILED",
        evidence_type="CROSS_DOCUMENT",
        metadata={
            "requirement": data.requirement,
            "reason": "FIELD_CONFLICT",
        },
    )

    final = evidence_store.add(
        source="cross_document_verifier",
        claim=data.requirement,
        value=conflict_details,
        verdict="BLOCKED",
        evidence_type="FINAL_VERDICT",
        metadata={
            "reason": "FIELD_CONFLICT",
            "action": "HUMAN_REVIEW_REQUIRED",
        },
    )

    return {
        "status": "BLOCKED",
        "requirement": data.requirement,
        "field": data.field,
        "documents_checked": len(data.documents),
        "result": "CONFLICT",
        "reason": "FIELD_CONFLICT",
        "action": "HUMAN_REVIEW_REQUIRED",
        "evidence": [
            conflict_evidence,
            final,
        ],
        "message": (
            "Conflicting values detected. "
            "DocuSure will not guess or modify the values. "
            "Human review is required."
        ),
    }