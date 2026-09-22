from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.browser import WebsiteApplicationAgent
from app.agent.orchestrator import AgentOrchestrator

router = APIRouter(
    prefix="/browser",
    tags=["Browser Automation"],
)


class ApplicationAutomationRequest(BaseModel):
    url: str = Field(..., description="Target application website URL")
    field_values: dict[str, str] = Field(
        ...,
        description="Verified document/application data",
    )
    submit: bool = True


browser_agent = WebsiteApplicationAgent()
orchestrator = AgentOrchestrator()


@router.post("/application")
def automate_application(request: ApplicationAutomationRequest):
    try:
        result = browser_agent.run(
            url=request.url,
            field_values=request.field_values,
            submit=request.submit,
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "FAILED",
                "reason": "BROWSER_AUTOMATION_ERROR",
                "error": str(error),
            },
        ) from error