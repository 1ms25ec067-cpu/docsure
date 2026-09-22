# DocuSure

Evidence-Gated Document Submission & Verification Agent.

## Core principle

DocuSure does not declare a task complete simply because
an action was performed.

Completion requires machine-checkable evidence that the
expected state actually exists.

## Workflow

Requirements
→ Documents
→ Validation
→ Cross-check
→ Form Filling
→ Approval
→ Submission
→ Verification
→ Recovery
→ Re-verification
→ Proof

## Technology

Backend:
- Python
- FastAPI
- Pydantic

Documents:
- PyMuPDF
- Pillow

Browser:
- Playwright

LLM:
- Gemini

Database:
- Supabase/PostgreSQL

Frontend:
- React

## Verification states

VERIFIED
FAILED
UNVERIFIED

## Recovery examples

FILE_TOO_LARGE
→ repair
→ validate again

DOB_CONFLICT
→ human review

CAPTCHA
→ human review

UNKNOWN_STATE
→ stop safely