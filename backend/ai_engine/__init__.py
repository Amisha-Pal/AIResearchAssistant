"""
Framework-agnostic AI layer (LLM inference, RAG, agents, document processing).

Django apps call into this package through service functions; nothing in here
imports Django views or models, so it can be unit-tested and reused from
Celery workers or notebooks.
"""
