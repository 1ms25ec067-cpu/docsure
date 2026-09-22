from fastapi.testclient import TestClient
from app.main import app
from app.verification.store import evidence_store

client = TestClient(app)


def test_false_success_and_self_healing_workflow():
    evidence_store.clear()
    app_id = "APP-TEST-FALSE-SUCCESS"

    # 1. Start agent workflow
    res_start = client.post("/agent/start", json={"application_id": app_id})
    assert res_start.status_code == 200
    wf = res_start.json()
    wf_id = wf["workflow_id"]

    # 2. Portal reports submission (backend is still DRAFT)
    res_sub = client.post("/submission/submit", json={"application_id": app_id})
    assert res_sub.status_code == 200

    # 3. Independent verification detects false success
    res_ver = client.post("/submission/verify", json={"application_id": app_id})
    assert res_ver.status_code == 200
    ver_data = res_ver.json()
    assert ver_data["status"] == "FAILED"
    assert ver_data["verification"] == "FALSE_SUCCESS_DETECTED"

    # 4. Final proof MUST BE BLOCKED before recovery/confirmation
    res_proof_blocked = client.post(f"/agent/proof/{wf_id}")
    assert res_proof_blocked.status_code == 200
    proof_blocked_data = res_proof_blocked.json()
    assert proof_blocked_data["status"] == "BLOCKED"

    # 5. Recovery self-heals the backend status
    res_rec = client.post("/submission/recover", json={"application_id": app_id})
    assert res_rec.status_code == 200
    assert res_rec.json()["status"] == "RECOVERED"

    # 6. Re-verification succeeds
    res_ver2 = client.post("/submission/verify", json={"application_id": app_id})
    assert res_ver2.status_code == 200
    ver2_data = res_ver2.json()
    assert ver2_data["status"] == "VERIFIED"
    assert ver2_data["verification"] == "SUBMISSION_CONFIRMED"

    # 7. Final proof now succeeds with verified evidence
    res_proof = client.post(f"/agent/proof/{wf_id}")
    assert res_proof.status_code == 200
    proof_data = res_proof.json()
    assert proof_data["status"] == "VERIFIED"
    assert proof_data["stage"] == "PROOF"
