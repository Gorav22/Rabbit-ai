import os
import json
from groq import Groq
from typing import Any

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _client = Groq(api_key=api_key)
    return _client


def generate_summary(data: dict[str, Any]) -> str:
    """
    Use Groq (Llama 3) to produce a professional executive-level
    narrative summary from parsed sales data.
    """
    client = _get_client()

    # Build a concise JSON context to keep tokens low
    context = {
        "filename": data.get("filename"),
        "total_rows": data.get("rows"),
        "columns": data.get("columns"),
        "totals": data.get("totals", {}),
        "averages": data.get("averages", {}),
        "breakdowns": data.get("breakdowns", {}),
        "sample_records": data.get("head", [])[:3],
    }
    if "total_revenue" in data:
        context["total_revenue"] = data["total_revenue"]
    if "total_units" in data:
        context["total_units"] = data["total_units"]

    system_prompt = (
        "You are a senior business analyst at Rabbitt AI. "
        "Your job is to read structured sales data and produce a concise, "
        "professional executive summary suitable for C-suite leadership. "
        "Use clear section headings, bullet points, highlight key wins, "
        "risks, and actionable recommendations. Keep it under 400 words. "
        "Do NOT include raw JSON or code — plain, polished business English only."
    )

    user_prompt = (
        f"Here is the parsed sales data from the uploaded file:\n\n"
        f"```json\n{json.dumps(context, indent=2, default=str)}\n```\n\n"
        "Please generate a professional executive sales summary report."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()
