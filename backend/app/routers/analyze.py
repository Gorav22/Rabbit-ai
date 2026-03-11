import logging
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import EmailStr, ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.parser import validate_file, parse_file
from app.services.ai import generate_summary
from app.services.mailer import send_summary_email
from app.models import AnalyzeResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analyze"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Upload Sales File & Generate AI Summary",
    description=(
        "Accept a `.csv` or `.xlsx` sales data file and a recipient email address. "
        "The backend parses the file, sends the structured data to **Groq (Llama 3)** "
        "for an executive-level narrative summary, and delivers it via email. "
        "Returns a JSON response with status and a preview of the generated summary.\n\n"
        "**Rate limit:** 10 requests per minute per IP.\n\n"
        "**Supported formats:** `.csv`, `.xlsx`, `.xls`."
    ),
    responses={
        200: {"description": "Analysis complete; email sent."},
        400: {"description": "Invalid file type or malformed input."},
        422: {"description": "Validation error (e.g., invalid email)."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Internal server error (AI or mailer failure)."},
    },
)
@limiter.limit("10/minute")
async def analyze_sales_file(
    request: Request,
    file: UploadFile = File(..., description="Sales data file (.csv or .xlsx)"),
    email: str = Form(..., description="Recipient email address for the AI summary"),
):
    # ── Validate email ───────────────────────────────────────────────────────
    try:
        from pydantic import TypeAdapter
        TypeAdapter(EmailStr).validate_python(email)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid email address provided.")

    # ── Read file bytes ──────────────────────────────────────────────────────
    content = await file.read()

    # ── Validate file ────────────────────────────────────────────────────────
    try:
        validate_file(file.filename or "upload", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ── Parse ────────────────────────────────────────────────────────────────
    try:
        data = parse_file(file.filename or "upload", content)
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Could not parse the uploaded file: {str(e)}",
        )

    # ── AI Summary ───────────────────────────────────────────────────────────
    try:
        summary = generate_summary(data)
    except Exception as e:
        logger.error(f"AI error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI summary generation failed: {str(e)}",
        )

    # ── Send email ───────────────────────────────────────────────────────────
    try:
        send_summary_email(recipient=email, summary=summary, filename=file.filename or "upload")
    except Exception as e:
        logger.error(f"Mailer error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Email delivery failed: {str(e)}",
        )

    # Preview (first 300 chars)
    preview = summary[:300] + "…" if len(summary) > 300 else summary

    return AnalyzeResponse(
        status="success",
        message=f"Analysis complete. Summary sent to {email}.",
        recipient=email,
        summary_preview=preview,
        rows_processed=data.get("rows"),
        columns_detected=data.get("columns"),
    )
