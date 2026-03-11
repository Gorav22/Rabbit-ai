from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import os

from app.routers import analyze

load_dotenv()

# ── Rate limiter ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

# ── Security headers middleware ──────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        return response

# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sales Insight Automator",
    description=(
        "Upload a CSV or Excel sales file and receive an AI-generated "
        "executive summary directly in your inbox — powered by Groq (Llama 3)."
    ),
    version="1.0.0",
    contact={"name": "Rabbitt AI Engineering", "email": "eng@rabbitt.ai"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {
            "name": "Analyze",
            "description": "Upload a sales file and trigger AI summary + email delivery.",
        }
    ],
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
@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health():
    return {"status": "ok", "service": "sales-insight-automator"}


