import io
import pandas as pd
from typing import Any


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def validate_file(filename: str, content: bytes) -> None:
    """Validate file by extension."""
    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")



def _get_extension(filename: str) -> str:
    import os
    return os.path.splitext(filename.lower())[1]


def parse_file(filename: str, content: bytes) -> dict[str, Any]:
    """Parse CSV/Excel and return a structured summary dict."""
    ext = _get_extension(filename)
    buf = io.BytesIO(content)

    if ext == ".csv":
        df = pd.read_csv(buf)
    else:
        df = pd.read_excel(buf)

    df.columns = [str(c).strip() for c in df.columns]
    row_count = len(df)
    columns = list(df.columns)

    summary: dict[str, Any] = {
        "filename": filename,
        "rows": row_count,
        "columns": columns,
        "head": df.head(5).to_dict(orient="records"),
    }

    # Numeric aggregations
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        summary["totals"] = df[numeric_cols].sum().to_dict()
        summary["averages"] = df[numeric_cols].mean().round(2).to_dict()

    # Category breakdowns (value_counts for low-cardinality string columns)
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    breakdowns: dict[str, Any] = {}
    for col in cat_cols:
        vc = df[col].value_counts()
        if 1 < len(vc) <= 20:
            breakdowns[col] = vc.to_dict()
    summary["breakdowns"] = breakdowns

    # Revenue / Units shortcuts if columns exist
    if "Revenue" in df.columns:
        summary["total_revenue"] = float(df["Revenue"].sum())
    if "Units_Sold" in df.columns:
        summary["total_units"] = int(df["Units_Sold"].sum())

    return summary
