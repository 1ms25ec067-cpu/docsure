from pydantic import BaseModel


class EvidenceResponse(BaseModel):

    evidence_id: str
    source: str
    claim: str
    value: str
    verdict: str