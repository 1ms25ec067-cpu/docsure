from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(
    prefix="/test-application",
    tags=["Test Application"],
)


@router.get("", response_class=HTMLResponse)
def application_form():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DocuSure Test Application</title>
    </head>
    <body>
        <h1>Application Form</h1>

        <form method="post" action="/test-application/submit">
            <label for="full_name">Full Name</label>
            <input
                id="full_name"
                name="full_name"
                type="text"
            >

            <label for="email">Email</label>
            <input
                id="email"
                name="email"
                type="email"
            >

            <button type="submit">Submit Application</button>
        </form>
    </body>
    </html>
    """


@router.post("/submit", response_class=HTMLResponse)
def submit_application(full_name: str = "", email: str = ""):
    application_id = f"APP-{uuid4().hex[:8].upper()}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Application Submitted</title>
    </head>
    <body>
        <h1>Application Submitted Successfully</h1>

        <p>Your application has been submitted.</p>

        <p>
            <strong>Application ID:</strong>
            {application_id}
        </p>

        <p>
            <strong>Full Name:</strong>
            {full_name}
        </p>

        <p>
            <strong>Email:</strong>
            {email}
        </p>
    </body>
    </html>
    """