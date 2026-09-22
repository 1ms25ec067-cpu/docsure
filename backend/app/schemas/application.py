from enum import Enum

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    RECOVERING = "RECOVERING"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"


class ApplicationCreate(BaseModel):

    applicant_name: str = Field(
        min_length=1,
        max_length=200,
    )

    application_type: str = Field(
        default="SCHOLARSHIP",
        min_length=1,
        max_length=100,
    )


class ApplicationResponse(BaseModel):

    application_id: str
    applicant_name: str
    application_type: str
    status: ApplicationStatus