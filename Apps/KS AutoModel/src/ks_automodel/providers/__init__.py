"""Model provider implementations for KS AutoModel."""

from .base import ModelProvider
from .huggingface import HuggingFaceProvider
# from .github import GitHubProvider  # TODO: Implement
# from .modelscope import ModelScopeProvider  # TODO: Implement

__all__ = [
    "ModelProvider",
    "HuggingFaceProvider",
]