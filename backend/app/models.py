from pydantic import BaseModel, EmailStr
from typing import Optional


class AnalyzeResponse(BaseModel):
    """Response returned after a successful sales file analysis."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Analysis complete. Summary sent to exec@company.com.",
                "recipient": "exec@company.com",
                "summary_preview": (
                    "## Q1 2026 Sales Executive Summary\n\n"
                    "**Total Revenue:** $684,000 across 6 transactions. "
                    "Electronics dominated with ~97% of revenue ($639,750). "
                    "North was the strongest region at $442,500. "
                    "One cancellation (Home Appliances, $24,000) flagged for follow-up."
                ),
                "rows_processed": 6,
                "columns_detected": [
                    "Date", "Product_Category", "Region",
                    "Units_Sold", "Unit_Price", "Revenue", "Status"
                ],
            }
        }
    }

    status: str
    message: str
    recipient: EmailStr
    summary_preview: Optional[str] = None
    rows_processed: Optional[int] = None
    columns_detected: Optional[list[str]] = None
