# 🐇 Rabbitt AI — Sales Insight Automator

> **Engineer's Log** · AI Cloud DevOps Sprint  
> Stack: FastAPI · Groq (Llama 3) · React/Vite · Docker · GitHub Actions

[![Backend Image](https://img.shields.io/docker/v/gorav22/rabbitai-backend?label=gorav22%2Frabbitai-backend&logo=docker&color=7c3aed)](https://hub.docker.com/r/gorav22/rabbitai-backend)
[![Frontend Image](https://img.shields.io/docker/v/gorav22/rabbitai-frontend?label=gorav22%2Frabbitai-frontend&logo=docker&color=4f46e5)](https://hub.docker.com/r/gorav22/rabbitai-frontend)

A single-page application where sales team members upload a `.csv` or `.xlsx` file and instantly receive an AI-generated executive summary in their inbox — powered by **Groq (Llama 3.3-70b)**.

---

## � Docker Hub Images

| Image | Docker Hub | Pull Command |
|---|---|---|
| **Backend** | [gorav22/rabbitai-backend](https://hub.docker.com/r/gorav22/rabbitai-backend) | `docker pull gorav22/rabbitai-backend:latest` |
| **Frontend** | [gorav22/rabbitai-frontend](https://hub.docker.com/r/gorav22/rabbitai-frontend) | `docker pull gorav22/rabbitai-frontend:latest` |

Run the full stack from Docker Hub (no source code needed):
```bash
docker compose pull && docker compose up
```

## �🚀 Quick Start with Docker Compose

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Groq API key](https://console.groq.com/) (free tier available)
- Gmail App Password ([guide](https://myaccount.google.com/apppasswords))

### 1. Clone & configure

```bash
git clone https://github.com/Gorav22/Rabbit-ai.git
cd Rabbit-ai

# Copy and fill in backend environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your GROQ_API_KEY, SMTP credentials, etc.
```

### 2. Spin up the stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **API (FastAPI)** | http://localhost:8000 |
| **Swagger Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

### 3. Test it

1. Open **http://localhost:3000**
2. Upload `sales_q1_2026.csv` (included in repo root)
3. Enter a recipient email address
4. Click **⚡ Generate AI Summary & Send**
5. Check your inbox for the formatted report

---

## 🏗️ Architecture Overview

```
rabbitai/
├── backend/          # FastAPI — Python 3.11
│   ├── app/
│   │   ├── main.py          # App factory, CORS, security headers, rate limiting
│   │   ├── models.py        # Pydantic response models
│   │   ├── routers/
│   │   │   └── analyze.py   # POST /api/analyze
│   │   └── services/
│   │       ├── parser.py    # CSV/XLSX → structured dict (pandas)
│   │       ├── ai.py        # Groq Llama 3 summary generation
│   │       └── mailer.py    # HTML email via SMTP
│   └── Dockerfile           # Multi-stage, non-root user
│
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── App.jsx          # SPA — upload, loading steps, success/error
│   │   └── index.css        # Premium dark glassmorphism design
│   ├── nginx.conf           # SPA routing + gzip + security headers
│   └── Dockerfile           # node:20 builder → nginx:alpine
│
├── .github/workflows/ci.yml # GitHub Actions CI
├── docker-compose.yml
└── sales_q1_2026.csv        # Sample test file
```

---

## 🔒 Security Overview

| Layer | Implementation |
|---|---|
| **Rate Limiting** | SlowAPI — 10 requests/min per IP on all API routes |
| **CORS** | Strict allow-list via `ALLOWED_ORIGINS` env var |
| **File Validation** | Extension whitelist (`.csv`, `.xlsx`, `.xls`) + 10 MB max |
| **Security Headers** | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy`, `Strict-Transport-Security` |
| **Input Sanitization** | Pydantic `EmailStr` validation, no raw SQL or shell commands |
| **Non-root containers** | Both Dockerfiles use a dedicated non-root user/group |
| **No secrets in image** | All credentials via `env_file`, never baked into the image |

---

## 🔁 CI/CD Pipeline

Triggered on every **Pull Request → `main`** via GitHub Actions:

```
backend-lint  ──►  backend-build
frontend-lint ──►  frontend-build
```

- `backend-lint`: `flake8` with max line 120
- `backend-build`: Full Docker build validation
- `frontend-lint`: `eslint` on React source
- `frontend-build`: Full Docker build with production `VITE_API_URL`
- Docker layer caching via GitHub Actions cache for fast rebuilds

---

## 🌐 Deployment

Both the frontend and backend are optimized for deployment on **Vercel**.

| Component | Platform | Notes |
|---|---|---|
| **Frontend** | Vercel | Static SPA deploy from `frontend/dist` |
| **Backend** | Vercel | Serverless Functions (FastAPI) |

### Vercel Deployment

1. **Backend**:
   - Connect repository to Vercel.
   - Set **Root Directory** to `backend`.
   - Vercel automatically detects FastAPI if configured with `vercel.json` or as serverless functions.
   - Add all environment variables from `.env.example` in the Vercel project settings.

2. **Frontend**:
   - Connect repository to Vercel.
   - Set **Root Directory** to `frontend`.
   - Set **Build Command**: `npm run build`.
   - Set **Output Directory**: `dist`.
   - Add env var: `VITE_API_URL=https://your-backend-on-vercel.vercel.app`.

---

## ⚙️ Environment Variables

See [.env.example](./.env.example) for all required keys.

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq Cloud API key |
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP port (587 for TLS) |
| `SMTP_USER` | Sender email address |
| `SMTP_PASSWORD` | App-specific password |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `VITE_API_URL` | Backend URL (frontend env) |

---

## 📊 API Reference

Full interactive docs at `/docs` (Swagger UI) and `/redoc`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/analyze` | Upload file + email → AI summary + send |
| `GET` | `/health` | Liveness probe |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc documentation |

---

*Built with ❤️ by the future team person of Rabbitt AI.*
