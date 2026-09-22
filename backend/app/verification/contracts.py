from dataclasses import dataclass
from typing import List


@dataclass
class VerificationContract:

    name: str
    expected_state: str
    evidence_required: List[str]

    def to_dict(self):
        return {
            "name": self.name,
            "expected_state": self.expected_state,
            "evidence_required": self.evidence_required,
        }