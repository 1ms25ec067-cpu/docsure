from dataclasses import dataclass
from typing import Optional


@dataclass
class Application:
    application_id: str
    applicant_name: str
    application_type: str
    status: str


@dataclass
class Document:
    document_id: str
    filename: str
    document_type: str
    size_bytes: int
    status: str


@dataclass
class AgentEvent:
    event_id: str
    application_id: str
    stage: str
    message: str


@dataclass
class VerificationResult:
    verification_id: str
    application_id: str
    expected: str
    actual: str
    verdict: str


@dataclass
class Evidence:
    evidence_id: str
    source: str
    claim: str
    value: str
    verdict: str
    timestamp: Optional[str] = None