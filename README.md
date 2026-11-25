# Advanced AI Research Assistant

A local-first research platform for reading, analysing and comparing papers, running RAG over your own PDFs, orchestrating multi-agent research workflows, and experimenting with PyTorch models. All AI runs locally (Ollama + small open models); no paid APIs are required.

> Status: **Phase 1 (foundation)** is complete. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the architecture and the phase roadmap.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, React Router, Axios, Lucide |
| API | Django 5.2, Django REST Framework, SimpleJWT, drf-spectacular |
| Data | PostgreSQL (relational), FAISS (vectors, Phase 6) |
| Background jobs | Celery + Redis |
| AI engine | Ollama (`qwen2.5:3b` default), Sentence Transformers, LangChain/LangGraph, PyTorch, PyMuPDF |

## Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL 14+ and Redis 6+ (native install, or `docker compose`, see below)
- [Ollama](https://ollama.com/download) for local LLM inference

## 1. Configure environment

```bash
cp backend/.env.example backend/.env          # Windows: copy backend\.env.example backend\.env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # paste into DJANGO_SECRET_KEY
```

Set `POSTGRES_PASSWORD` (and anything else you need) in `backend/.env`. The `.env` file is git-ignored; never commit it.

## 2. Start PostgreSQL and Redis

**Option A: Docker**

```bash
docker compose --env-file backend/.env up -d
```

**Option B: native PostgreSQL** (create the role and database once):

```sql
CREATE USER research_user WITH PASSWORD '<your password>' CREATEDB;  -- CREATEDB is needed for the test database
CREATE DATABASE research_assistant OWNER research_user;
```

On Windows, Redis is easiest via Docker or WSL (`sudo apt install redis-server`), or use [Memurai](https://www.memurai.com/).

## 3. Backend

```bash
cd backend
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser        # optional, for /admin
python manage.py runserver
```

Background worker (separate terminal, venv activated):

```bash
celery -A config worker -l info                 # Linux/macOS
celery -A config worker -l info --pool=solo     # Windows (prefork is not supported)
```

ML dependencies (needed from Phase 5 onwards). Install the PyTorch build for your hardware first:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121   # NVIDIA GPU (e.g. RTX 2050)
pip install torch --index-url https://download.pytorch.org/whl/cpu     # CPU only
pip install -r requirements-ml.txt
```

## 4. Local LLM

```bash
ollama pull qwen2.5:3b       # ~1.9 GB, Q4_K_M quantized
ollama pull qwen2.5:1.5b     # optional lighter fallback
```

Change `LLM_MODEL` / `LLM_FALLBACK_MODELS` in `backend/.env` to use other Ollama models.

## 5. Frontend

```bash
cd frontend
cp .env.example .env         # optional
npm install
npm run dev                  # http://localhost:5173 (proxies /api to http://localhost:8000)
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/api/v1/health/` | Database / Redis / Ollama status (`ok`, `degraded`, or `error` with HTTP 503) |
| `http://localhost:8000/api/docs/` | Swagger UI (OpenAPI schema at `/api/schema/`) |
| `http://localhost:8000/admin/` | Django admin |

## API overview (v1)

All endpoints except register, login, refresh and health need `Authorization: Bearer <access token>`.
Errors always use `{"error": {"status", "code", "message", "fields"?}}`.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/register/` | Create an account; returns `access`, `refresh`, `user` |
| POST | `/api/v1/auth/login/` | Log in with username **or** email |
| POST | `/api/v1/auth/refresh/` | Rotate the refresh token (old one is blacklisted) |
| POST | `/api/v1/auth/logout/` | Blacklist the given refresh token |
| GET/PATCH | `/api/v1/auth/me/` | View or edit profile (affiliation, bio, research interests) |
| POST | `/api/v1/auth/password/change/` | Change password; revokes all other sessions and returns new tokens |
| GET/POST | `/api/v1/projects/` | List (`?search=`, `?status=`, `?ordering=`, `?page=`) or create research projects |
| GET/PATCH/DELETE | `/api/v1/projects/<id>/` | Manage one of your own projects |

Auth endpoints are rate limited (`API_THROTTLE_AUTH`, default `10/min`).

## Tests and checks

```bash
cd backend && python manage.py test          # needs PostgreSQL; the DB user needs CREATEDB
cd frontend && npm run lint && npm run build
```

## Hardware notes

The default configuration targets a laptop with ~8 GB RAM and a 4 GB GPU (e.g. i5-12450H + RTX 2050):

- `qwen2.5:3b` (Q4_K_M) is a 1.9 GB download; with a 4K context it is expected to fit in 4 GB of VRAM. If it does not, Ollama offloads layers to CPU automatically when VRAM is short, which is slower but works.
- Only one LLM is loaded at a time. `LLM_KEEP_ALIVE` unloads it after 5 idle minutes to free memory.
- Embeddings use `all-MiniLM-L6-v2` (~90 MB). `COMPUTE_DEVICE=auto` uses CUDA when PyTorch sees a GPU and falls back to CPU otherwise.
- Celery runs 2 worker processes with prefetch 1, so large PDFs are processed in the background without exhausting RAM.
- The Model Lab (Phase 10) trains small educational models (MLPs, small CNNs, a Mini GPT with a few million parameters). It cannot train or fine-tune production-scale LLMs on this hardware.
