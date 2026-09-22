from app.verification.contracts import (
    VerificationContract,
)


class RequirementInterpreter:

    def interpret(
        self,
        requirement: str,
    ):
        contract = VerificationContract(
            name="document_requirement",
            expected_state=requirement,
            evidence_required=[
                "document_metadata",
                "validation_result",
            ],
        )

        return {
            "original_requirement": requirement,
            "contract": contract.to_dict(),
            "status": "INTERPRETED",
        }