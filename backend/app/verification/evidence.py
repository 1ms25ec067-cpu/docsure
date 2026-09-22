from datetime import datetime, timezone
from uuid import uuid4


class EvidenceRecord:
    """
    Machine-readable evidence supporting a DocuSure claim.
    """

    def __init__(
        self,
        source: str,
        claim: str,
        value,
        verdict: str,
        evidence_type: str = "GENERAL",
        metadata: dict | None = None,
    ):
        self.evidence_id = (
            f"EVD-{uuid4().hex[:8].upper()}"
        )

        self.source = source
        self.claim = claim
        self.value = value
        self.verdict = verdict
        self.evidence_type = evidence_type
        self.metadata = metadata or {}

        self.timestamp = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

    def to_dict(self):
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "claim": self.claim,
            "value": self.value,
            "verdict": self.verdict,
            "evidence_type": self.evidence_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }