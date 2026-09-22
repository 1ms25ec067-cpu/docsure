from datetime import datetime, timezone
from uuid import uuid4


class SubmissionVerifier:

    def __init__(self):
        self.submissions = {}

    def submit(self, application_id: str, portal_status: str = "SUBMITTED"):
        submission_id = f"SUB-{uuid4().hex[:8].upper()}"

        record = {
            "submission_id": submission_id,
            "application_id": application_id,
            "portal_status": portal_status,
            "backend_status": "DRAFT",
            "created_at": self._now(),
        }

        self.submissions[application_id] = record

        return {
            "status": "SUCCESS",
            "message": "Portal reported submission success.",
            "submission": record,
        }

    def verify(self, application_id: str):
        submission = self.submissions.get(application_id)

        if submission is None:
            return {
                "status": "FAILED",
                "verification": "NO_SUBMISSION_FOUND",
                "application_id": application_id,
                "message": "No submission record exists.",
            }

        portal_status = submission.get("portal_status")
        backend_status = submission.get("backend_status")

        if (
            portal_status == "SUBMITTED"
            and backend_status != "SUBMITTED"
        ):
            return {
                "status": "FAILED",
                "verification": "FALSE_SUCCESS_DETECTED",
                "application_id": application_id,
                "submission_id": submission["submission_id"],
                "portal_status": portal_status,
                "backend_status": backend_status,
                "message": (
                    "Portal reported submission success, "
                    "but independent backend verification "
                    "shows the application is not submitted."
                ),
            }

        if backend_status == "SUBMITTED":
            return {
                "status": "VERIFIED",
                "verification": "SUBMISSION_CONFIRMED",
                "application_id": application_id,
                "submission_id": submission["submission_id"],
                "portal_status": portal_status,
                "backend_status": backend_status,
                "message": (
                    "Submission independently verified."
                ),
            }

        return {
            "status": "FAILED",
            "verification": "UNKNOWN_STATE",
            "application_id": application_id,
            "submission_id": submission["submission_id"],
            "portal_status": portal_status,
            "backend_status": backend_status,
            "message": (
                "Submission state could not be independently verified."
            ),
        }

    def recover(self, application_id: str):
        submission = self.submissions.get(application_id)

        if submission is None:
            return {
                "status": "FAILED",
                "message": "No submission exists to recover.",
            }

        # Safe recovery: only update an existing known record.
        submission["backend_status"] = "SUBMITTED"
        submission["recovered_at"] = self._now()

        return {
            "status": "RECOVERED",
            "action": "RESUBMISSION_STATE_REPAIRED",
            "submission": submission,
            "message": (
                "Submission state was repaired and is "
                "ready for independent verification."
            ),
        }

    @staticmethod
    def _now():
        return datetime.now(
            timezone.utc
        ).isoformat()


submission_verifier = SubmissionVerifier()