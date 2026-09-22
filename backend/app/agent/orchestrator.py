from datetime import datetime, timezone
from uuid import uuid4

from app.agent.planner import AgentPlanner
from app.agent.recovery import RecoveryEngine
from app.verification.store import evidence_store


class AgentOrchestrator:

    STAGES = [
        "REQUIREMENTS",
        "DOCUMENTS",
        "VALIDATION",
        "CROSS_CHECK",
        "FORM_FILLING",
        "APPROVAL",
        "SUBMISSION",
        "VERIFICATION",
        "RECOVERY",
        "PROOF",
    ]

    EVIDENCE_GATED_STAGES = {
        "VALIDATION",
        "CROSS_CHECK",
        "APPROVAL",
        "SUBMISSION",
        "VERIFICATION",
    }

    def __init__(self):
        self.planner = AgentPlanner()
        self.recovery_engine = RecoveryEngine()
        self.workflows = {}

    def start(self, application_id: str):
        workflow_id = f"WF-{uuid4().hex[:8].upper()}"
        now = self._now()

        workflow = {
            "workflow_id": workflow_id,
            "application_id": application_id,
            "stage": "REQUIREMENTS",
            "status": "RUNNING",
            "started_at": now,
            "updated_at": now,
            "completed_stages": [],
            "failed_stages": [],
            "recovery_attempts": [],
            "evidence_ids": [],
            "human_review_required": False,
            "message": "DocuSure agent started",
        }

        self.workflows[workflow_id] = workflow
        return workflow.copy()

    def get_workflow(self, workflow_id: str):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        return workflow.copy()

    def get_next_action(self, current_stage: str):
        return self.planner.next_action(current_stage)

    def advance(
        self,
        workflow_id: str,
        evidence_verified: bool = False,
        message: str | None = None,
    ):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_stage = workflow["stage"]

        if current_stage in self.EVIDENCE_GATED_STAGES:
            verified_evidence = self._get_verified_evidence()

            if not verified_evidence:
                workflow["status"] = "BLOCKED"
                workflow["updated_at"] = self._now()
                workflow["message"] = (
                    "Stage cannot advance without machine-checkable "
                    "verification evidence."
                )
                return workflow.copy()

            for record in verified_evidence:
                evidence_id = record.get("evidence_id")

                if evidence_id and evidence_id not in workflow["evidence_ids"]:
                    workflow["evidence_ids"].append(evidence_id)

        if current_stage not in workflow["completed_stages"]:
            workflow["completed_stages"].append(current_stage)

        current_index = self.STAGES.index(current_stage)

        if current_stage == "PROOF":
            workflow["status"] = "VERIFIED"
            workflow["updated_at"] = self._now()
            workflow["message"] = (
                message or "Workflow completed with verified proof."
            )
            return workflow.copy()

        next_index = current_index + 1

        if next_index >= len(self.STAGES):
            workflow["status"] = "VERIFIED"
            workflow["updated_at"] = self._now()
            workflow["message"] = message or "Workflow completed."
            return workflow.copy()

        next_stage = self.STAGES[next_index]

        workflow["stage"] = next_stage
        workflow["status"] = "RUNNING"
        workflow["updated_at"] = self._now()
        workflow["message"] = (
            message or f"Workflow advanced to {next_stage}"
        )

        return workflow.copy()

    def block(
        self,
        workflow_id: str,
        reason: str,
        human_review_required: bool = False,
    ):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_stage = workflow["stage"]

        if current_stage not in workflow["failed_stages"]:
            workflow["failed_stages"].append(current_stage)

        workflow["status"] = "BLOCKED"
        workflow["human_review_required"] = human_review_required
        workflow["updated_at"] = self._now()
        workflow["message"] = reason

        return workflow.copy()

    def recover(self, failure_type: str, file_path: str | None = None):
        if file_path:
            return self.recovery_engine.recover(
                failure_type=failure_type,
                file_path=file_path,
            )

        return self.recovery_engine.recover(
            failure_type=failure_type
        )

    def record_recovery(self, workflow_id: str, recovery_result: dict):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow["recovery_attempts"].append({
            "failure_type": recovery_result.get("failure_type"),
            "status": recovery_result.get("status"),
            "action": recovery_result.get("action"),
            "timestamp": self._now(),
        })

        for record in recovery_result.get("evidence", []):
            evidence_id = record.get("evidence_id")

            if evidence_id and evidence_id not in workflow["evidence_ids"]:
                workflow["evidence_ids"].append(evidence_id)

        workflow["updated_at"] = self._now()

        if recovery_result.get("status") == "RECOVERED":
            workflow["status"] = "RUNNING"
            workflow["message"] = (
                "Failure recovered and evidence recorded."
            )
        else:
            workflow["status"] = "BLOCKED"
            workflow["message"] = (
                "Recovery did not produce a verified result."
            )

        return workflow.copy()

    def attach_evidence(self, workflow_id: str, evidence_id: str):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        all_evidence = evidence_store.get_all()

        matching = [
            record
            for record in all_evidence
            if record.get("evidence_id") == evidence_id
        ]

        if not matching:
            raise ValueError(f"Evidence not found: {evidence_id}")

        if matching[0].get("verdict") != "VERIFIED":
            raise ValueError(
                "Only VERIFIED evidence can be attached "
                "to an evidence-gated workflow."
            )

        if evidence_id not in workflow["evidence_ids"]:
            workflow["evidence_ids"].append(evidence_id)

        workflow["updated_at"] = self._now()

        return workflow.copy()

    def create_proof(self, workflow_id: str):
        workflow = self.workflows.get(workflow_id)

        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        all_evidence = evidence_store.get_all()

        # Final proof MUST be based on independently verified
        # submission evidence.
        submission_evidence = [
            record
            for record in all_evidence
            if record.get("verdict") == "VERIFIED"
            and record.get("evidence_type") == "SUBMISSION_VERIFICATION"
            and record.get("value", {}).get("verification")
            == "SUBMISSION_CONFIRMED"
        ]

        if not submission_evidence:
            workflow["status"] = "BLOCKED"
            workflow["updated_at"] = self._now()
            workflow["message"] = (
                "Final proof blocked: independently verified "
                "submission evidence is required."
            )
            return workflow.copy()

        for record in submission_evidence:
            evidence_id = record.get("evidence_id")

            if evidence_id and evidence_id not in workflow["evidence_ids"]:
                workflow["evidence_ids"].append(evidence_id)

        proof_evidence = evidence_store.add(
            source="docsure_proof_engine",
            claim="Application submission is complete and independently verified.",
            value={
                "application_id": workflow["application_id"],
                "workflow_id": workflow["workflow_id"],
                "submission_verification": "SUBMISSION_CONFIRMED",
                "submission_evidence_ids": [
                    record["evidence_id"]
                    for record in submission_evidence
                ],
            },
            verdict="VERIFIED",
            evidence_type="FINAL_PROOF",
            metadata={
                "evidence_gate": "SUBMISSION_VERIFICATION",
                "proof_type": "APPLICATION_COMPLETION",
            },
        )

        if proof_evidence.get("evidence_id"):
            workflow["evidence_ids"].append(
                proof_evidence["evidence_id"]
            )

        workflow["stage"] = "PROOF"
        workflow["status"] = "VERIFIED"
        workflow["updated_at"] = self._now()
        workflow["message"] = (
            "Final proof created from independently verified submission evidence."
        )

        return workflow.copy()

    def status(self, workflow_id: str):
        return self.get_workflow(workflow_id)

    def _get_verified_evidence(self):
        all_evidence = evidence_store.get_all()

        return [
            record
            for record in all_evidence
            if record.get("verdict") == "VERIFIED"
        ]

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()