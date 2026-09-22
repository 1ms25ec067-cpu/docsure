from fastapi import FastAPI
from app.api.contracts import router as contracts_router
from app.api.agent import router as agent_router
from app.api.applications import router as applications_router
from app.api.submission import router as submission_router
from app.api.documents import router as documents_router
from app.api.transformations import router as transformations_router
from app.api.verification import router as verification_router
from app.api.offline import router as offline_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.browser import router as browser_router
from app.api.test_application import router as test_application_router

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
app.include_router(test_application_router)
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
    return {
        "status": "ok"
    }