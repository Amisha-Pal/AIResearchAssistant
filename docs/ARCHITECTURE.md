# Architecture

## Overview

```
┌──────────────┐   HTTP/JSON (JWT)   ┌──────────────────────┐      ┌────────────┐
│ React + Vite │ ──────────────────▶ │ Django REST API      │ ───▶ │ PostgreSQL │
│  (frontend/) │ ◀────────────────── │ (backend/apps/*)     │      └────────────┘
└──────────────┘                     │   thin views         │
                                     │   ↓                  │      ┌────────────┐
                                     │ service layer        │ ───▶ │ Redis      │
                                     └─────────┬────────────┘      └─────┬──────┘
                                               │ calls                   │ broker
                                     ┌─────────▼────────────┐      ┌─────▼──────┐
                                     │ ai_engine/           │ ◀─── │ Celery     │
                                     │  llm  rag  agents    │      │ workers    │
                                     │  documents  lab      │      └────────────┘
                                     └───┬─────────┬────────┘
                                         │         │
                                   ┌─────▼───┐ ┌───▼──────────┐
                                   │ Ollama  │ │ FAISS index  │
                                   │ (local) │ │ (data/faiss) │
                                   └─────────┘ └──────────────┘
```

### Layering rules

1. **Views** (`apps/<app>/views.py`) validate input with serializers, check permissions and call a service. No business or AI logic.
2. **Services** (`apps/<app>/services/`) hold the domain logic and talk to the ORM. Long-running work is enqueued as Celery tasks (`apps/<app>/tasks.py`).
3. **AI engine** (`backend/ai_engine/`) does not depend on Django: it receives plain data and returns plain data. `ai_engine.config.get_ai_config()` is the only place that reads Django settings, and it does so lazily. This keeps the AI code testable on its own and reusable from workers and notebooks.
4. **Configuration** comes only from environment variables (`backend/.env`, see `.env.example`). Secrets are never committed or exposed to the frontend. Only `VITE_*` variables reach the browser.

## Folder structure

```
AIResearchAssistant/
├── docker-compose.yml          # local PostgreSQL + Redis
├── docs/ARCHITECTURE.md
├── backend/
│   ├── manage.py
│   ├── requirements.txt        # core web stack
│   ├── requirements-ml.txt     # PyTorch / HF / LangChain / FAISS (Phase 5+)
│   ├── .env.example
│   ├── config/                 # settings, urls, celery app, env helpers
│   ├── apps/
│   │   ├── core/               # health check, shared utilities
│   │   ├── accounts/           # custom User, auth, profile (Phase 2)
│   │   ├── research/           # research projects / workspaces
│   │   ├── papers/             # PDF upload, metadata, analysis, citations
│   │   ├── chatbot/            # conversations and messages
│   │   ├── agents/             # LangGraph workflow runs and logs
│   │   ├── knowledge_graph/    # entities and relations
│   │   └── experiments/        # experiment tracker and model lab runs
│   └── ai_engine/
│       ├── config.py           # typed AI config built from settings
│       ├── device.py           # CUDA/CPU selection with fallback
│       ├── llm/                # Ollama client (+ chat/streaming in Phase 5)
│       ├── documents/          # PyMuPDF extraction, cleaning, chunking (Phase 4)
│       ├── rag/                # embeddings, FAISS, retrieval (Phase 6)
│       ├── agents/             # LangGraph graphs (Phase 7)
│       └── lab/                # PyTorch from-scratch models (Phase 10)
└── frontend/                   # React + Vite app
```

Folders marked with a later phase are created when that phase is implemented.

## Runtime configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | required | Django signing key |
| `DJANGO_DEBUG` | `False` | Debug mode. Production hardening (HSTS, secure cookies, SSL redirect) is enabled when off |
| `POSTGRES_*` | see `.env.example` | Database connection (`POSTGRES_PASSWORD` required) |
| `REDIS_URL` / `CACHE_REDIS_URL` | `redis://localhost:6379/0` / `/1` | Celery broker + results / Django cache |
| `LLM_MODEL` / `LLM_FALLBACK_MODELS` | `qwen2.5:3b` / `qwen2.5:1.5b` | Ollama models, tried in order |
| `COMPUTE_DEVICE` | `auto` | `auto`, `cpu` or `cuda` for embeddings and PyTorch |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` / `RAG_TOP_K` | `800` / `120` / `5` | RAG defaults (overlap must be smaller than the chunk size) |
| `MAX_PDF_UPLOAD_MB` | `25` | Upload size limit (enforced in Phase 4) |

## Phase roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Inspection, architecture, folder structure, env config, PostgreSQL, Redis/Celery, health check | Done |
| 2 | Auth (register, login, JWT refresh/blacklist, profile, password change), API conventions | Planned |
| 3 | React app shell: dark theme, sidebar, routing, protected routes, auth UI, dashboard | Planned |
| 4 | PDF upload and validation, PyMuPDF extraction, metadata, projects, processing status (Celery) | Planned |
| 5 | Ollama inference layer, research chat with history, streaming, markdown | Planned |
| 6 | Chunking, embeddings, FAISS index, retrieval with scores, cited answers, retrieval evaluation | Planned |
| 7 | LangGraph agents (planner, literature, analysis, comparison, gap, critic, citation, report), logs, retries, human approval | Planned |
| 8 | Paper comparison tables, research gap finder (with references and uncertainty warnings), literature review | Planned |
| 9 | Knowledge graph (NetworkX + interactive UI), experiment tracker with charts | Planned |
| 10 | PyTorch model lab: regressions, MLP and backprop, CNN, attention, Transformer, Mini GPT | Planned |
| 11 | Citation manager (APA/IEEE/BibTeX, reference extraction, manual correction), report generator with PDF export | Planned |
| 12 | Security review, performance tuning, docs, deployment configuration | Planned |
