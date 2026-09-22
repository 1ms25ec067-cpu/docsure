from fastapi import APIRouter
from pydantic import BaseModel

from app.verification.submission import submission_verifier
from app.verification.store import evidence_store


router = APIRouter(
    prefix="/submission",
    tags=["Submission"],
)


class SubmissionRequest(BaseModel):
    application_id: str


@router.post("/submit")
def submit_application(data: SubmissionRequest):
    result = submission_verifier.submit(
        application_id=data.application_id
    )

    evidence_store.add(
        source="submission_portal",
        claim="Portal reported that the application was submitted.",
        value=result["submission"],
        verdict="SUCCESS",
        evidence_type="SUBMISSION_ATTEMPT",
        metadata={
            "application_id": data.application_id
        },
    )

    return result


@router.post("/verify")
def verify_submission(data: SubmissionRequest):
    result = submission_verifier.verify(
        application_id=data.application_id
    )

    if result["status"] == "VERIFIED":
        verdict = "VERIFIED"
    else:
        verdict = "FAILED"

    evidence_store.add(
        source="independent_submission_verifier",
        claim=(
            "Application submission status was "
            "independently verified."
        ),
        value=result,
        verdict=verdict,
        evidence_type="SUBMISSION_VERIFICATION",
        metadata={
            "application_id": data.application_id,
            "verification": result.get(
                "verification"
            ),
        },
    )

    return result


@router.post("/recover")
def recover_submission(data: SubmissionRequest):
    result = submission_verifier.recover(
        application_id=data.application_id
    )

    evidence_store.add(
        source="submission_recovery",
        claim="Submission state was repaired.",
        value=result,
        verdict=(
            "VERIFIED"
            if result["status"] == "RECOVERED"
            else "FAILED"
        ),
        evidence_type="RECOVERY",
        metadata={
            "application_id": data.application_id
        },
    )

    return result