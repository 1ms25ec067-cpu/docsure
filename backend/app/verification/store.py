from typing import Any

from app.verification.evidence import EvidenceRecord


class EvidenceStore:
    """
    Central in-memory evidence store.

    This is intentionally in-memory for the current backend
    development stage. We will replace it with Supabase later.
    """

    def __init__(self):
        self._records: list[EvidenceRecord] = []

    def add(
        self,
        source: str,
        claim: str,
        value: Any,
        verdict: str,
        evidence_type: str = "GENERAL",
        metadata: dict | None = None,
    ) -> dict:
        record = EvidenceRecord(
            source=source,
            claim=claim,
            value=value,
            verdict=verdict,
            evidence_type=evidence_type,
            metadata=metadata,
        )

        self._records.append(record)

        return record.to_dict()

    def get_all(self) -> list[dict]:
        return [
            record.to_dict()
            for record in self._records
        ]

    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()


# One shared store for the running backend.
evidence_store = EvidenceStore()