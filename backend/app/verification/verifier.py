from enum import Enum
from typing import Any


class VerificationStatus(str, Enum):

    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"


class Verifier:

    def verify(
        self,
        expected: Any,
        actual: Any,
        evidence: Any,
    ) -> VerificationStatus:

        if evidence is None:
            return VerificationStatus.UNVERIFIED

        if expected == actual:
            return VerificationStatus.VERIFIED

        return VerificationStatus.FAILED