from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    recipient: EmailStr
    summary_preview: Optional[str] = None
    rows_processed: Optional[int] = None
    columns_detected: Optional[list[str]] = None
