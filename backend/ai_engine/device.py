"""Compute-device selection with CPU fallback. PyTorch is optional at this layer."""

import importlib.util
import logging

logger = logging.getLogger(__name__)


def torch_installed():
    return importlib.util.find_spec("torch") is not None


def resolve_device(preference="auto"):
    """Return "cuda" or "cpu" for the given preference ("auto", "cpu", "cuda")."""
    preference = (preference or "auto").lower()
    if preference == "cpu" or not torch_installed():
        if preference == "cuda":
            logger.warning("COMPUTE_DEVICE=cuda requested but PyTorch is not installed; using CPU.")
        return "cpu"

    import torch

    if torch.cuda.is_available():
        return "cuda"
    if preference == "cuda":
        logger.warning("COMPUTE_DEVICE=cuda requested but CUDA is unavailable; using CPU.")
    return "cpu"
