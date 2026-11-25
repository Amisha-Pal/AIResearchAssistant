from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AIConfig:
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: float = 120.0
    llm_model: str = "qwen2.5:3b"
    llm_fallback_models: tuple = ("qwen2.5:1.5b",)
    llm_temperature: float = 0.2
    llm_num_ctx: int = 4096
    llm_keep_alive: str = "5m"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 16
    compute_device: str = "auto"
    faiss_index_dir: Path = field(default_factory=lambda: Path("data/faiss"))
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 5

    def __post_init__(self):
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE.")
        if self.compute_device not in {"auto", "cpu", "cuda"}:
            raise ValueError("COMPUTE_DEVICE must be one of: auto, cpu, cuda.")

    @property
    def candidate_models(self):
        """Primary model first, then fallbacks, without duplicates."""
        seen = []
        for name in (self.llm_model, *self.llm_fallback_models):
            if name and name not in seen:
                seen.append(name)
        return seen

    @classmethod
    def from_mapping(cls, values):
        return cls(
            ollama_base_url=values["OLLAMA_BASE_URL"].rstrip("/"),
            ollama_timeout=float(values["OLLAMA_TIMEOUT"]),
            llm_model=values["LLM_MODEL"],
            llm_fallback_models=tuple(values["LLM_FALLBACK_MODELS"]),
            llm_temperature=float(values["LLM_TEMPERATURE"]),
            llm_num_ctx=int(values["LLM_NUM_CTX"]),
            llm_keep_alive=values["LLM_KEEP_ALIVE"],
            embedding_model=values["EMBEDDING_MODEL"],
            embedding_batch_size=int(values["EMBEDDING_BATCH_SIZE"]),
            compute_device=values["COMPUTE_DEVICE"].lower(),
            faiss_index_dir=Path(values["FAISS_INDEX_DIR"]),
            rag_chunk_size=int(values["RAG_CHUNK_SIZE"]),
            rag_chunk_overlap=int(values["RAG_CHUNK_OVERLAP"]),
            rag_top_k=int(values["RAG_TOP_K"]),
        )


def get_ai_config():
    """Build the config from Django settings (imported lazily to keep this package Django-free)."""
    from django.conf import settings

    return AIConfig.from_mapping(settings.AI_ENGINE)
