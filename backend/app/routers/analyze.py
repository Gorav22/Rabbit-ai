import logging
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from pydantic import EmailStr
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
        200: {
            "description": "Analysis complete — AI summary generated and email delivered.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Analysis complete. Summary sent to exec@company.com.",
                        "recipient": "exec@company.com",
                        "summary_preview": (
                            "## Q1 2026 Sales Executive Summary\n\n"
                            "**Total Revenue:** $684,000 across 6 transactions.\n\n"
                            "**Top Category:** Electronics dominated with ~97% of revenue ($639,750). "
                            "**Top Region:** North led with $442,500 in combined sales. "
                            "**Concern:** 1 cancelled order (Home Appliances, North — $24,000) requires follow-up…"
                        ),
                        "rows_processed": 6,
                        "columns_detected": [
                            "Date", "Product_Category", "Region",
                            "Units_Sold", "Unit_Price", "Revenue", "Status"
                        ],
                    }
                }
            },
        },
        400: {
            "description": "Invalid file type (not CSV/XLSX/XLS).",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unsupported file type '.pdf'. Allowed: .csv, .xlsx, .xls"
                    }
                }
            },
        },
        422: {
            "description": "Validation error — invalid email address or missing field.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email address provided."}
                }
            },
        },
        429: {
            "description": "Rate limit exceeded — 10 requests/min per IP.",
            "content": {
                "application/json": {
                    "example": {"error": "Rate limit exceeded: 10 per 1 minute"}
                }
            },
        },
        500: {
            "description": "AI generation or email delivery failure.",
            "content": {
                "application/json": {
                    "examples": {
                        "ai_failure": {
                            "summary": "Groq API failure",
                            "value": {"detail": "AI summary generation failed: Connection timeout"}
                        },
                        "email_failure": {
                            "summary": "SMTP failure",
                            "value": {"detail": "Email delivery failed: Authentication error"}
                        },
                    }
                }
            },
        },
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
