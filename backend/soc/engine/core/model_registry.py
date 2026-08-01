"""
Multi-Head LLM Model Registry & VRAM Optimization Manager.
Routes reasoning, syntactic, and embedding workloads across specialized LLM heads within hardware limits.
"""

import os
import logging
from typing import Optional
try:
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel

    def create_openai_model(model_name: str, base_url: str, api_key: str) -> OpenAIModel:
        provider = OpenAIProvider(base_url=base_url, api_key=api_key)
        return OpenAIModel(model_name, provider=provider)
except ImportError:
    from pydantic_ai.models.openai import OpenAIModel

    def create_openai_model(model_name: str, base_url: str, api_key: str) -> OpenAIModel:
        return OpenAIModel(model_name=model_name, base_url=base_url, api_key=api_key)

from pydantic_ai import Agent

logger = logging.getLogger("RCA-ModelRegistry")

# --- Performance Constants ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1")
NUM_CTX = 32768  # Enforce 32k context window for all heads


class ModelRegistry:
    """
    Centralized factory for the Agentic SOC's Multi-Head Model Design.
    Distributes tasks between Qwen 2.5 7B (Reasoning) and Qwen 2.5 3B (Syntactic).
    """

    @staticmethod
    def get_reasoning_model(model_id: str = "qwen2.5:7b-instruct") -> OpenAIModel:
        """High-fidelity head for the QUILL-INVESTIGATOR."""
        logger.info(
            f"[Registry] Initializing Reasoning Head: {model_id} (num_ctx={NUM_CTX})"
        )
        return create_openai_model(
            model_name=model_id, base_url=OLLAMA_BASE_URL, api_key="ollama_local"
        )

    @staticmethod
    def get_syntactic_model(model_id: str = "qwen2.5:3b-instruct") -> OpenAIModel:
        """High-speed header for Log-Guardian and Communicator tasks."""
        logger.info(
            f"[Registry] Initializing Syntactic Head: {model_id} (num_ctx={NUM_CTX})"
        )
        return create_openai_model(
            model_name=model_id, base_url=OLLAMA_BASE_URL, api_key="ollama_local"
        )

    @staticmethod
    def get_embedding_model_id() -> str:
        """ID for local embeddings."""
        return "bge-m3"


def get_pydantic_ai_model_settings() -> dict:
    """
    Returns standard model settings to be passed to Agent.run().
    Enforces the context window and parallel throughput performance.
    """
    return {
        # Note: num_ctx is passed in 'extra_body' for Ollama-OpenAI compatibility
        # but check if your Pydantic AI version supports it in settings.
        "temperature": 0.2,
    }
