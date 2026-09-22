from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatus,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


APPLICATIONS: Dict[str, ApplicationResponse] = {}


@router.post(
    "",
    response_model=ApplicationResponse,
)
def create_application(
    data: ApplicationCreate,
):
    application_id = f"APP-{uuid4().hex[:8].upper()}"

    application = ApplicationResponse(
        application_id=application_id,
        applicant_name=data.applicant_name,
        application_type=data.application_type,
        status=ApplicationStatus.CREATED,
    )

    APPLICATIONS[application_id] = application

    return application


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(
    application_id: str,
):
    application = APPLICATIONS.get(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application