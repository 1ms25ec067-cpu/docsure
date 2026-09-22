from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.documents.validator import DocumentValidator
from app.offline.queue import offline_queue
from app.verification.store import evidence_store


router = APIRouter(prefix="/offline", tags=["Offline"])

validator = DocumentValidator()


class OfflineValidationRequest(BaseModel):
    application_id: str
    file_path: str


@router.post("/validate")
def validate_offline(data: OfflineValidationRequest):
    path = Path(data.file_path)

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # IMPORTANT:
    # This validation happens entirely locally.
    result = validator.validate(str(path))

    event = offline_queue.add(
        event_type="DOCUMENT_VALIDATION",
        application_id=data.application_id,
        result=result,
    )

    return {
        "status": result.get("status"),
        "execution_mode": "OFFLINE",
        "application_id": data.application_id,
        "event_id": event["event_id"],
        "queued": True,
        "message": (
            "Document was processed locally while offline. "
            "Result retained in the local queue for synchronization."
        ),
        "validation": result,
    }


@router.get("/queue")
def get_offline_queue():
    return {
        "pending_events": offline_queue.get_pending(),
        "total_events": len(offline_queue.get_all()),
    }


@router.post("/sync")
def sync_offline_events():
    pending = offline_queue.get_pending()

    if not pending:
        return {
            "status": "NOTHING_TO_SYNC",
            "events_synced": 0,
            "message": "No pending offline events.",
        }

    synced_ids = []

    for event in pending:
        evidence_store.add(
            source="offline_local_validation",
            claim="Document validation completed during connectivity outage.",
            value=event["result"],
            verdict=(
                "VERIFIED"
                if event["result"].get("status") == "VERIFIED"
                else "FAILED"
            ),
            evidence_type="OFFLINE_SYNC",
            metadata={
                "event_id": event["event_id"],
                "application_id": event["application_id"],
                "offline_created_at": event["created_at"],
            },
        )

        synced_ids.append(event["event_id"])

    offline_queue.mark_synced(synced_ids)

    return {
        "status": "SYNCHRONIZED",
        "events_synced": len(synced_ids),
        "event_ids": synced_ids,
        "message": (
            "Offline events were synchronized into the evidence store."
        ),
    }