from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app
from app.verification.store import evidence_store
from app.offline.queue import offline_queue

client = TestClient(app)


def test_cross_document_matching():
    evidence_store.clear()
    payload = {
        "requirement": "Name must match across all documents",
        "field": "Full Name",
        "documents": [
            {"document": "Aadhaar Card", "field": "Full Name", "value": "Koushik V"},
            {"document": "Income Certificate", "field": "Applicant Name", "value": "Koushik V"},
        ],
    }
    res = client.post("/contracts/cross-check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VERIFIED"
    assert data["result"] == "MATCH"


def test_cross_document_conflict_requires_human_review():
    evidence_store.clear()
    payload = {
        "requirement": "DOB must match across all documents",
        "field": "Date of Birth",
        "documents": [
            {"document": "Document A", "field": "DOB", "value": "17 February 2008"},
            {"document": "Document B", "field": "DOB", "value": "18 February 2008"},
        ],
    }
    res = client.post("/contracts/cross-check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "BLOCKED"
    assert data["result"] == "CONFLICT"
    assert data["action"] == "HUMAN_REVIEW_REQUIRED"


def test_offline_validation_queue_and_sync():
    evidence_store.clear()
    pdf_path = Path("uploads/DOC-1DD97BBF_fictional_income_certificate_demo.pdf")
    if pdf_path.exists():
        # 1. Offline validate
        res_val = client.post("/offline/validate", json={
            "application_id": "APP-OFFLINE-001",
            "file_path": str(pdf_path),
        })
        assert res_val.status_code == 200
        val_data = res_val.json()
        assert val_data["execution_mode"] == "OFFLINE"
        assert val_data["queued"] is True
        event_id = val_data["event_id"]

        # 2. Check offline queue
        res_queue = client.get("/offline/queue")
        assert res_queue.status_code == 200
        queue_data = res_queue.json()
        pending_ids = [e["event_id"] for e in queue_data["pending_events"]]
        assert event_id in pending_ids

        # 3. Synchronize when connection returns
        res_sync = client.post("/offline/sync")
        assert res_sync.status_code == 200
        sync_data = res_sync.json()
        assert sync_data["status"] == "SYNCHRONIZED"
        assert sync_data["events_synced"] >= 1

        # 4. Check evidence store contains OFFLINE_SYNC evidence
        all_ev = evidence_store.get_all()
        sync_ev = [e for e in all_ev if e["evidence_type"] == "OFFLINE_SYNC"]
        assert len(sync_ev) >= 1
