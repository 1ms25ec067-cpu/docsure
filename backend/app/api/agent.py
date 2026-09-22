from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agent.browser import WebsiteApplicationAgent
from app.agent.orchestrator import AgentOrchestrator


router = APIRouter(prefix="/agent", tags=["Agent"])

orchestrator = AgentOrchestrator()
browser_agent = WebsiteApplicationAgent()


# -----------------------------
# Request Models
# -----------------------------

class StartRequest(BaseModel):
    application_id: str


class AdvanceRequest(BaseModel):
    evidence_verified: bool = False
    message: Optional[str] = None


class BlockRequest(BaseModel):
    reason: str
    human_review_required: bool = False


class RecoverRequest(BaseModel):
    failure_type: str
    file_path: Optional[str] = None


# -----------------------------
# START WORKFLOW
# -----------------------------

@router.post("/start")
def start_agent(data: StartRequest):
    return orchestrator.start(data.application_id)


# -----------------------------
# GET WORKFLOW STATUS
# -----------------------------

@router.get("/status/{workflow_id}")
def get_agent_status(workflow_id: str):
    try:
        return orchestrator.get_workflow(workflow_id)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


# -----------------------------
# ADVANCE WORKFLOW
# -----------------------------

@router.post("/advance/{workflow_id}")
def advance_agent(
    workflow_id: str,
    data: AdvanceRequest,
):
    try:
        return orchestrator.advance(
            workflow_id=workflow_id,
            evidence_verified=data.evidence_verified,
            message=data.message,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# -----------------------------
# BLOCK WORKFLOW
# -----------------------------

@router.post("/block/{workflow_id}")
def block_agent(
    workflow_id: str,
    data: BlockRequest,
):
    try:
        return orchestrator.block(
            workflow_id=workflow_id,
            reason=data.reason,
            human_review_required=data.human_review_required,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


# -----------------------------
# RECOVER FROM FAILURE
# -----------------------------

@router.post("/recover/{workflow_id}")
def recover_agent(
    workflow_id: str,
    data: RecoverRequest,
):
    try:
        result = orchestrator.recover(
            failure_type=data.failure_type,
            file_path=data.file_path,
        )

        if result.get("status") == "FAILED":
            return {
                "workflow_id": workflow_id,
                "status": "RECOVERY_FAILED",
                "recovery": result,
            }

        orchestrator.record_recovery(
            workflow_id=workflow_id,
            recovery_result=result,
        )

        return {
            "workflow_id": workflow_id,
            "status": "RECOVERED",
            "recovery": result,
            "workflow": orchestrator.get_workflow(workflow_id),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# -----------------------------
# CREATE FINAL PROOF
# -----------------------------

@router.post("/proof/{workflow_id}")
def create_proof(workflow_id: str):
    try:
        return orchestrator.create_proof(workflow_id)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
@router.post("/browser-submit/{workflow_id}")
def browser_submit(
    workflow_id: str,
    url: str,
    field_values: dict[str, str],
):
    try:
        workflow = orchestrator.get_workflow(workflow_id)

        if workflow["status"] == "BLOCKED":
            return workflow

        result = browser_agent.run(
            url=url,
            field_values=field_values,
            submit=True,
        )

        # Attach only VERIFIED evidence to the workflow.
        for record in result.get("evidence", []):
            if record.get("verdict") == "VERIFIED":
                evidence_id = record.get("evidence_id")

                if evidence_id:
                    try:
                        orchestrator.attach_evidence(
                            workflow_id,
                            evidence_id,
                        )
                    except ValueError:
                        pass

        if result.get("status") != "VERIFIED":
            return orchestrator.block(
                workflow_id=workflow_id,
                reason=result.get(
                    "reason",
                    "Browser submission was not independently verified.",
                ),
                human_review_required=(
                    result.get("reason") == "SUBMISSION_NOT_CONFIRMED"
                ),
            )

        submission_verified = any(
            record.get("verdict") == "VERIFIED"
            and record.get("evidence_type") == "SUBMISSION_VERIFICATION"
            and record.get("value", {}).get("verification")
            == "SUBMISSION_CONFIRMED"
            for record in result.get("evidence", [])
        )

        if not submission_verified:
            return orchestrator.block(
                workflow_id=workflow_id,
                reason="Browser submission completed without independently verified submission evidence.",
            )

        return orchestrator.advance(
            workflow_id=workflow_id,
            message=(
                "Browser application submitted and independently verified."
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "FAILED",
                "reason": "WORKFLOW_NOT_FOUND",
                "error": str(error),
            },
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "FAILED",
                "reason": "BROWSER_WORKFLOW_ERROR",
                "error": str(error),
            },
        ) from error