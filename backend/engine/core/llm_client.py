import json
import logging
import os
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Unified LLM Client abstraction designed for local, air-gapped inference
    (e.g., Ollama or vLLM) via an OpenAI-compatible REST API.
    
    Defaults to localhost:11434 (Standard Ollama port).
    """
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, default_model: str = "llama3-soc"):
        self.base_url = base_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1")
        self.api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama_local")
        self.default_model = default_model
        
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    async def generate_json(self, prompt: str, system_instruction: str = "", model: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Produce a structured JSON payload from the local model.
        Forces the local model to adhere strictly to JSON output.
        """
        target_model = model or self.default_model
        
        messages = []
        if system_instruction:
            # Reinforce JSON instruction for smaller edge models
            messages.append({"role": "system", "content": f"{system_instruction}\n\nIMPORTANT: You must output strictly valid JSON format. Provide no other text or explanation."})
            
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content.strip()
            
            # Defensive stripping for models that ignore response_format constraint
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            return json.loads(raw_content.strip())
            
        except Exception as e:
            logger.error(f"Local LLM JSON generation failed: {e}")
            raise e

    async def generate(self, prompt: str, system_instruction: str = "", model: Optional[str] = None, temperature: float = 0.2) -> str:
        """Generate a raw string completion."""
        target_model = model or self.default_model
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
            
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Local LLM raw generation failed: {e}")
            raise e

    async def generate_chat_json(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.2) -> tuple[Dict[str, Any], str]:
        """
        Generate a JSON response from an ongoing chat history.
        Always returns a tuple of (parsed_json_dict, raw_assistant_message).
        """
        target_model = model or self.default_model
        
        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            orig_content = raw_content
            
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            return (json.loads(raw_content.strip()), orig_content)
        except Exception as e:
            logger.error(f"Local LLM stateful chat failed: {e}")
            raise e

    async def generate_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Generate a raw string completion from an ongoing chat history.
        """
        target_model = model or self.default_model
        
        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Local LLM chat generation failed: {e}")
            raise e

    async def get_embedding(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate semantic embeddings for RAG indexing."""
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Local LLM embedding failed: {e}")
            raise e
