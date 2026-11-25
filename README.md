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

Set `POSTGRES_PASSWORD` (and anything else you need) in `backend/.env`. See [Auth-related environment variables](#auth-related-environment-variables-backendenv) for JWT, cookie and email settings. The `.env` file is git-ignored; never commit it.

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

## Authentication

### How sessions work

- **Access token** (JWT, 15 minutes): sent as `Authorization: Bearer <access>`. The web app keeps it **in memory only**, never in `localStorage` or in URLs.
- **Refresh token** (JWT, 7 days): set by the backend as an **httpOnly, SameSite=Strict** cookie scoped to `/api/v1/auth/` (and `Secure` when `DJANGO_DEBUG=False`). It is also returned in the JSON body for non-browser API clients.
- Every refresh **rotates** the refresh token and blacklists the old one. Logout blacklists it and clears the cookie.
- Auth endpoints accept **JSON bodies only** (`415` otherwise). Cross-site HTML forms cannot send JSON, so another site cannot silently log your browser into a different account.
- Changing or resetting the password **revokes every session**: outstanding refresh tokens are blacklisted, and access tokens issued before the change are rejected.
- The frontend Axios client (`frontend/src/api/client.js`) retries a request once after a `401` by calling `/auth/refresh/`. If the refresh fails, the user is sent to the login page with a "session expired" message. On page reload the session is restored from the cookie.
- Auth endpoints are rate limited (`API_THROTTLE_AUTH`, default `10/min` per client IP).

### Endpoints

All errors use one envelope: `{"error": {"status", "code", "message", "fields"?}}`.

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/auth/register/` | – | Create an account, returns tokens and user (201) |
| POST | `/api/v1/auth/login/` | – | Log in with username **or** email |
| POST | `/api/v1/auth/refresh/` | cookie or body | Rotate the refresh token, returns a new access token |
| POST | `/api/v1/auth/logout/` | Bearer | Blacklist the refresh token (cookie or body), 204 |
| GET / PATCH | `/api/v1/auth/me/` | Bearer | View or edit profile (`first_name`, `last_name`, `email`, `affiliation`, `bio`, `research_interests`) |
| POST | `/api/v1/auth/password/change/` | Bearer | Change password, revokes other sessions, returns new tokens |
| POST | `/api/v1/auth/password/reset/` | – | Email a single-use reset link (same response whether or not the email exists) |
| POST | `/api/v1/auth/password/reset/confirm/` | – | Set a new password from the link's `uid` + `token` |
| GET / POST | `/api/v1/projects/` | Bearer | List (`?search=`, `?status=`, `?ordering=`, `?page=`) or create your research projects |
| GET / PATCH / DELETE | `/api/v1/projects/<id>/` | Bearer | Manage one of your own projects (other users' projects return 404) |

### Examples

```http
POST /api/v1/auth/register/
{"username": "ada", "email": "ada@example.com", "password": "s3cure-Passw0rd!", "password_confirm": "s3cure-Passw0rd!",
 "first_name": "Ada", "last_name": "Lovelace"}

201 Created            Set-Cookie: refresh_token=...; HttpOnly; Path=/api/v1/auth/; SameSite=Strict
{"access": "eyJ...", "refresh": "eyJ...",
 "user": {"id": 1, "username": "ada", "email": "ada@example.com", "first_name": "Ada", "last_name": "Lovelace",
          "affiliation": "", "bio": "", "research_interests": [], "date_joined": "...", "last_login": null}}
```

```http
POST /api/v1/auth/login/
{"username": "ada@example.com", "password": "s3cure-Passw0rd!"}

200 OK   {"access": "...", "refresh": "...", "user": {...}}
401      {"error": {"status": 401, "code": "no_active_account", "message": "Invalid username/email or password."}}
```

```http
POST /api/v1/auth/register/        (duplicate email)
400 {"error": {"status": 400, "code": "validation_error", "message": "A user with this email already exists.",
               "fields": {"email": ["A user with this email already exists."]}}}
```

```http
POST /api/v1/auth/refresh/         (body {} with the cookie, or {"refresh": "..."})
200 {"access": "...", "refresh": "..."}
401 {"error": {"status": 401, "code": "token_not_valid", "message": "Token is blacklisted"}}
```

```http
GET /api/v1/auth/me/               (expired or missing access token)
401 {"error": {"status": 401, "code": "token_not_valid", "message": "Given token not valid for any token type"}}
401 {"error": {"status": 401, "code": "not_authenticated", "message": "Authentication credentials were not provided."}}
```

```http
PATCH /api/v1/auth/me/
{"affiliation": "Analytical Engine Lab", "research_interests": ["NLP", "RAG"]}
200 {"id": 1, "username": "ada", ..., "affiliation": "Analytical Engine Lab", "research_interests": ["NLP", "RAG"]}
```

```http
POST /api/v1/auth/password/change/
{"current_password": "...", "new_password": "...", "new_password_confirm": "..."}
200 {"access": "...", "refresh": "...", "user": {...}}
```

```http
POST /api/v1/auth/password/reset/
{"email": "ada@example.com"}
200 {"detail": "If an account exists for that email, a password reset link has been sent."}

POST /api/v1/auth/password/reset/confirm/
{"uid": "MQ", "token": "c2x1f0-...", "new_password": "...", "new_password_confirm": "..."}
200 {"detail": "Your password has been reset. You can now log in."}
400 {"error": {..., "fields": {"token": ["This reset link is invalid or has expired."]}}}
```

### Password reset email

The link looks like `FRONTEND_URL/reset-password#uid=...&token=...`. The values are in the URL **fragment**, so browsers never send them to a server or in a `Referer` header, and the page removes them from the address bar on load. Links expire after `PASSWORD_RESET_TIMEOUT_SECONDS` (1 hour) and stop working once the password changes.

In development the email is printed in the `runserver` terminal (console backend). To send real mail, set the SMTP variables below. Any SMTP provider works, including a free Gmail app password.

### Auth-related environment variables (`backend/.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_ACCESS_MINUTES` | `15` | Access token lifetime |
| `JWT_REFRESH_DAYS` | `7` | Refresh token and cookie lifetime |
| `AUTH_REFRESH_COOKIE_NAME` | `refresh_token` | Cookie name |
| `AUTH_REFRESH_COOKIE_SAMESITE` | `Strict` | Use `None` (with HTTPS) only if frontend and API are on different sites |
| `AUTH_REFRESH_COOKIE_SECURE` | `not DEBUG` | Send cookie over HTTPS only |
| `API_THROTTLE_AUTH` | `10/min` | Rate limit for login, register, refresh, password endpoints |
| `API_NUM_PROXIES` | `0` | Trusted reverse proxies in front of Django (for client IP in throttling) |
| `EMAIL_BACKEND` | console | `django.core.mail.backends.smtp.EmailBackend` for real mail |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | – | SMTP settings |
| `DEFAULT_FROM_EMAIL` | `AI Research Assistant <no-reply@localhost>` | Sender address |
| `FRONTEND_URL` | `http://localhost:5173` | Base URL used in reset links |
| `PASSWORD_RESET_TIMEOUT_SECONDS` | `3600` | Reset link lifetime |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,...` | Origins allowed to call the API with credentials |

Frontend (`frontend/.env`): `VITE_API_BASE_URL` (leave empty to use the Vite proxy, recommended so the cookie stays same-site) and `VITE_BACKEND_URL` (proxy target). Never put secrets in `VITE_*` variables; they are bundled into the browser app.

### Web app pages

| Route | Access | Page |
|-------|--------|------|
| `/login` | logged-out only | Login with username or email |
| `/signup` | logged-out only | Registration with client- and server-side validation |
| `/forgot-password` | logged-out only | Request a reset email |
| `/reset-password` | anyone with a link | Choose a new password |
| `/dashboard` | logged-in | Account summary and your research projects |
| `/profile` | logged-in | Edit profile and change password |

Logged-out users who open a private page are redirected to `/login` and returned to that page after logging in. Logged-in users who open login or signup are redirected to `/dashboard`.

## Tests and checks

```bash
cd backend
python manage.py test                       # all tests (needs PostgreSQL; the DB user needs CREATEDB)
python manage.py test apps.accounts         # authentication tests only
python manage.py makemigrations --check --dry-run
python manage.py spectacular --validate --fail-on-warn --file schema.yml

cd ../frontend
npm run lint
npm run build
```

## Hardware notes

The default configuration targets a laptop with ~8 GB RAM and a 4 GB GPU (e.g. i5-12450H + RTX 2050):

- `qwen2.5:3b` (Q4_K_M) is a 1.9 GB download; with a 4K context it is expected to fit in 4 GB of VRAM. If it does not, Ollama offloads layers to CPU automatically when VRAM is short, which is slower but works.
- Only one LLM is loaded at a time. `LLM_KEEP_ALIVE` unloads it after 5 idle minutes to free memory.
- Embeddings use `all-MiniLM-L6-v2` (~90 MB). `COMPUTE_DEVICE=auto` uses CUDA when PyTorch sees a GPU and falls back to CPU otherwise.
- Celery runs 2 worker processes with prefetch 1, so large PDFs are processed in the background without exhausting RAM.
- The Model Lab (Phase 10) trains small educational models (MLPs, small CNNs, a Mini GPT with a few million parameters). It cannot train or fine-tune production-scale LLMs on this hardware.
