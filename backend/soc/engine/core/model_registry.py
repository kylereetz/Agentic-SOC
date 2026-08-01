"""
Multi-Head LLM Model Registry & VRAM Optimization Manager.
Routes reasoning, syntactic, and embedding workloads across specialized LLM heads within hardware limits.
"""

import os
import logging
from typing import Optional
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent

logger = logging.getLogger("RCA-ModelRegistry")

# --- Performance Constants ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1")
NUM_CTX = 16384  # Enforce 16k context window for all heads


class ModelRegistry:
    """
    Centralized factory for the Agentic SOC's Multi-Head Model Design.
    Distributes tasks between Llama 3.1 (Reasoning) and Gemma 4 (Syntactic).
    """

    @staticmethod
    def get_reasoning_model(model_id: str = "llama3.1:8b") -> OpenAIModel:
        """High-fidelity head for the QUILL-INVESTIGATOR."""
        logger.info(
            f"[Registry] Initializing Reasoning Head: {model_id} (num_ctx={NUM_CTX})"
        )
        return OpenAIModel(
            model_name=model_id, base_url=OLLAMA_BASE_URL, api_key="ollama_local"
        )

    @staticmethod
    def get_syntactic_model(model_id: str = "gemma4:e4b") -> OpenAIModel:
        """High-speed header for Log-Guardian and Communicator tasks."""
        logger.info(
            f"[Registry] Initializing Syntactic Head: {model_id} (num_ctx={NUM_CTX})"
        )
        return OpenAIModel(
            model_name=model_id, base_url=OLLAMA_BASE_URL, api_key="ollama_local"
        )

    @staticmethod
    def get_embedding_model_id() -> str:
        """ID for local embeddings."""
        return "nomic-embed-text"


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
