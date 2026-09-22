class AgentPlanner:

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

    def next_stage(
        self,
        current_stage: str,
    ):
        if current_stage not in self.STAGES:
            return None

        index = self.STAGES.index(
            current_stage
        )

        if index >= len(self.STAGES) - 1:
            return None

        return self.STAGES[index + 1]

    def next_action(
        self,
        current_stage: str,
    ):
        next_stage = self.next_stage(
            current_stage
        )

        if next_stage is None:
            return {
                "current_stage": current_stage,
                "next_stage": None,
                "status": "WORKFLOW_COMPLETE",
            }

        return {
            "current_stage": current_stage,
            "next_stage": next_stage,
            "status": "READY",
        }