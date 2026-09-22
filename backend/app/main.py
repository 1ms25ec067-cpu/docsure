from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contracts import router as contracts_router
from app.api.agent import router as agent_router
from app.api.applications import router as applications_router
from app.api.submission import router as submission_router
from app.api.documents import router as documents_router
from app.api.transformations import router as transformations_router
from app.api.verification import router as verification_router
from app.api.offline import router as offline_router
from app.api.browser import router as browser_router

app = FastAPI(
    title="DocuSure API",
    description=(
        "Evidence-Gated Document Submission "
        "and Verification Agent"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submission_router)
app.include_router(contracts_router)
app.include_router(applications_router)
app.include_router(documents_router)
app.include_router(agent_router)
app.include_router(verification_router)
app.include_router(transformations_router)
app.include_router(offline_router)
app.include_router(browser_router)


@app.get("/")
def root():
    return {
        "name": "DocuSure",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test-application")
def test_application():
    from fastapi.responses import HTMLResponse

    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DocuSure Test Application</title>
        </head>
        <body>
            <h1>Application Form</h1>
            <form id="application-form" onsubmit="submitForm(event)">
                <label for="full_name">Full Name</label>
                <input id="full_name" name="full_name" type="text" placeholder="Enter your full name" />
                <br><br>
                <label for="email">Email</label>
                <input id="email" name="email" type="email" placeholder="Enter your email" />
                <br><br>
                <button type="submit">Submit Application</button>
            </form>
            <div id="result"></div>
            <script>
                function submitForm(event) {
                    event.preventDefault();
                    document.getElementById("result").innerText =
                        "Application submitted successfully";
                    document.title = "Application Submitted";
                }
            </script>
        </body>
        </html>
        """
    )
