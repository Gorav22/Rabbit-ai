from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import os

from app.routers import analyze

load_dotenv()

# ── Rate limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])


# ── Security headers middleware ───────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Allow Swagger UI & ReDoc to iframe themselves; block everything else
        if request.url.path in ("/docs", "/redoc", "/api-docs"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ── OpenAPI metadata ──────────────────────────────────────────────────────────
DESCRIPTION = """
## 🐇 Rabbitt AI — Sales Insight Automator API

Transform raw sales data into executive-ready narratives in seconds.

### How it works

1. **Upload** a `.csv` or `.xlsx` sales file via `POST /api/analyze`
2. The backend **parses** the file with pandas (rows, totals, breakdowns)
3. Structured data is sent to **Groq (Llama 3.3-70b)** for a narrative summary
4. A branded HTML **email** is delivered to the specified recipient

---

### Authentication
This API is currently open for internal team use. Rate limiting is enforced:
- **10 requests / minute** per IP address
- Exceeding this returns `HTTP 429 Too Many Requests`

### Supported File Formats
| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 or Windows-1252 encoding |
| Excel (2007+) | `.xlsx` | Multi-sheet files — first sheet used |
| Excel (legacy) | `.xls` | Legacy binary format |

### Error Codes
| Code | Meaning |
|------|---------|
| `400` | Invalid file type or malformed data |
| `422` | Request validation failed (e.g. bad email) |
| `429` | Rate limit exceeded |
| `500` | AI generation or email delivery failure |

---

> **Tip:** Use the **Try it out** button on `POST /api/analyze` below to upload a file and test the full pipeline directly from this page.
"""

TAGS_METADATA = [
    {
        "name": "Analyze",
        "description": (
            "Core pipeline endpoint. Accepts a sales file + recipient email, "
            "runs it through the Groq AI engine, and delivers the summary via email."
        ),
        "externalDocs": {
            "description": "Groq Llama 3 model docs",
            "url": "https://console.groq.com/docs/models",
        },
    },
    {
        "name": "Health",
        "description": "Liveness probe used by Docker health checks and load balancers.",
    },
]


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sales Insight Automator",
    description=DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "Rabbitt AI Engineering",
        "email": "eng@rabbitt.ai",
        "url": "https://github.com/Gorav22/Rabbit-ai",
    },
    license_info={
        "name": "Proprietary — Rabbitt AI Internal",
    },
    openapi_tags=TAGS_METADATA,
    # Disable default docs so we can serve custom-branded ones
    docs_url=None,
    redoc_url=None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router, prefix="/api")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["Health"],
    summary="Liveness probe",
    response_description="Service is healthy",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "service": "sales-insight-automator"}
                }
            },
        }
    },
)
async def health():
    """
    Returns `200 OK` when the service is running.

    Used by Docker `HEALTHCHECK`, Render health checks, and load balancers.
    """
    return {"status": "ok", "service": "sales-insight-automator"}


# ── Custom Swagger UI (branded) ───────────────────────────────────────────────
SWAGGER_CSS = """
body { background: #080b14 !important; }
.swagger-ui { font-family: 'Inter', -apple-system, sans-serif !important; }
.swagger-ui .topbar { background: linear-gradient(135deg,#7c3aed,#4f46e5) !important; padding: 12px 24px; }
.swagger-ui .topbar .download-url-wrapper { display: none; }
.swagger-ui .info .title { color: #f1f5f9 !important; font-size: 28px !important; }
.swagger-ui .info { background: #0f1322; border-radius: 12px; padding: 24px; border: 1px solid rgba(139,92,246,0.18); margin-bottom: 24px; }
.swagger-ui .info p, .swagger-ui .info li, .swagger-ui .info td { color: #94a3b8 !important; }
.swagger-ui .info h2, .swagger-ui .info h3 { color: #a78bfa !important; }
.swagger-ui .info table { color: #94a3b8 !important; }
.swagger-ui .info code { background: rgba(124,58,237,0.15) !important; color: #a5b4fc !important; border-radius: 4px; padding: 2px 6px; }
.swagger-ui .scheme-container { background: #0f1322 !important; border: 1px solid rgba(139,92,246,0.18) !important; border-radius: 8px; }
.swagger-ui .opblock-tag { color: #a78bfa !important; border-bottom: 1px solid rgba(139,92,246,0.18) !important; font-size: 18px !important; }
.swagger-ui .opblock { background: #0f1322 !important; border-radius: 8px !important; border: 1px solid rgba(139,92,246,0.2) !important; }
.swagger-ui .opblock .opblock-summary { background: rgba(124,58,237,0.08) !important; }
.swagger-ui .opblock .opblock-summary-method { background: linear-gradient(135deg,#7c3aed,#4f46e5) !important; border-radius: 4px !important; font-weight: 700 !important; }
.swagger-ui .opblock-description-wrapper p { color: #94a3b8 !important; }
.swagger-ui section.models { background: #0f1322 !important; border: 1px solid rgba(139,92,246,0.18) !important; border-radius: 8px; }
.swagger-ui .model-title { color: #a78bfa !important; }
.swagger-ui .model { color: #94a3b8 !important; }
.swagger-ui select, .swagger-ui input[type=text], .swagger-ui textarea { background: #16192a !important; color: #f1f5f9 !important; border: 1px solid rgba(139,92,246,0.3) !important; border-radius: 6px !important; }
.swagger-ui .btn.execute { background: linear-gradient(135deg,#7c3aed,#4f46e5) !important; border: none !important; color: #fff !important; font-weight: 700 !important; border-radius: 8px !important; }
.swagger-ui .btn.authorize { background: rgba(124,58,237,0.15) !important; border: 1px solid rgba(124,58,237,0.4) !important; color: #a78bfa !important; border-radius: 8px !important; }
.swagger-ui .response-col_status { color: #6ee7b7 !important; }
.swagger-ui .response-col_description { color: #94a3b8 !important; }
.swagger-ui .highlight-code { background: #16192a !important; border-radius: 6px; }
.swagger-ui .microlight { color: #a5b4fc !important; }
"""

SWAGGER_JS_CONFIG = """
window.onload = function() {
  const ui = SwaggerUIBundle({
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    layout: 'StandaloneLayout',
    deepLinking: true,
    displayRequestDuration: true,
    tryItOutEnabled: true,
    requestSnippetsEnabled: true,
    defaultModelsExpandDepth: 2,
    defaultModelExpandDepth: 2,
    syntaxHighlight: { activated: true, theme: 'monokai' },
    tagsSorter: 'alpha',
    operationsSorter: 'alpha',
  });
  window.ui = ui;
};
"""


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Branded Swagger UI for the team."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>🐇 Rabbitt AI API Docs</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
  <style>
    {SWAGGER_CSS}
    /* Custom topbar logo */
    .topbar-wrapper img {{ display: none; }}
    .topbar-wrapper::before {{
      content: '🐇 Rabbitt AI — Sales Insight Automator API';
      color: #fff;
      font-size: 18px;
      font-weight: 700;
      font-family: Inter, sans-serif;
      letter-spacing: -0.3px;
    }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>{SWAGGER_JS_CONFIG}</script>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """ReDoc alternative documentation."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>🐇 Rabbitt AI — API Reference</title>
  <style>
    body { margin: 0; padding: 0; background: #080b14; }
  </style>
</head>
<body>
  <redoc spec-url="/openapi.json"
         hide-download-button
         expand-responses="200"
         theme='{
           "colors": {
             "primary": { "main": "#7c3aed" },
             "text": { "primary": "#f1f5f9", "secondary": "#94a3b8" }
           },
           "sidebar": { "backgroundColor": "#0f1322", "textColor": "#f1f5f9" },
           "rightPanel": { "backgroundColor": "#080b14" },
           "codeBlock": { "backgroundColor": "#16192a" },
           "typography": {
             "fontFamily": "Inter, -apple-system, sans-serif",
             "headings": { "fontFamily": "Inter, sans-serif" }
           }
         }'>
  </redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/api-docs", include_in_schema=False)
async def api_docs_redirect():
    """Friendly redirect — /api-docs goes to the Swagger UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
