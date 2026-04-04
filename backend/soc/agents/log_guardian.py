"""
SENTINEL-LOG-GUARDIAN: Pydantic AI Edition.

This agent acts as the 'Syntactic Head' for log normalization. It uses 
NLP-driven guidance to fix "broken" logs and map them to OCSF schemas.

Utilizes Qwen 2.5 3B for high-fidelity extraction of proprietary OT data.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from collections import deque
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.engine.core.model_registry import ModelRegistry
from soc.security.ocsf_schema import (
    OCSFAuthentication, OCSFNetworkActivity, 
    OCSFProprietaryOT, OCSFMetadata, OCSFEndpoint
)

logger = logging.getLogger("RCA-LogGuardian")

# --- Structured Output Models ---
class LogExtraction(BaseModel):
    """The result of an LLM-based log extraction."""
    ip: str = Field(description="The extracted source IP or 'Unknown'")
    inferred_meaning: str = Field(description="1-sentence summary of the activity")
    proprietary_codes: str = Field(description="Any hex codes, PLC error tags, or raw string variables")

# ---------------------------------------------------------------------------
# Log Guardian Agent
# ---------------------------------------------------------------------------
class LogGuardianAgent:
    def __init__(self):
        self.raw_bus = EventBus("raw_logs")
        self.out_bus = EventBus("discovery_events")
        self.is_running = False
        
        # Initialize Syntactic Model (Qwen 2.5 3B)
        self.model = ModelRegistry.get_syntactic_model()
        
        # Pydantic AI Agent
        self.ai_agent = Agent(
            self.model,
            result_type=LogExtraction,
            retries=2
        )
        
        # Performance Tracking
        self.stats = {
            "total_processed": 0,
            "fast_path": 0,
            "llm_fallback": 0,
            "failed": 0
        }
        self.last_flush = time.time()

    async def _agentic_fallback(self, raw: str, source: str) -> Optional[OCSFProprietaryOT]:
        """LLM Fallback extraction for proprietary OT data via Qwen 2.5."""
        prompt = f"""
        Extract security context from this proprietary OT log.
        Source: {source}
        Payload: {raw}
        """
        
        try:
            result = await self.ai_agent.run(
                prompt,
                system_prompt="You are an expert OT log parsing specialist. Extract IPs and meanings from industrial protocol logs.",
                model_settings={"temperature": 0.1}
            )
            
            data = result.data
            
            unmapped_dict = {
                "inferred_meaning": data.inferred_meaning,
                "proprietary_codes": data.proprietary_codes,
                "original_source": source,
                "raw_event": raw
            }
            
            return OCSFProprietaryOT(
                metadata=OCSFMetadata(normalization_type="custom_OT_inferred"),
                time=time.time(),
                src_endpoint=OCSFEndpoint(ip=data.ip) if data.ip != "Unknown" else None,
                unmapped=unmapped_dict
            )
        except Exception as e:
            logger.error(f"[!] Log extraction failed: {e}")
            return None

    async def _normalize_log(self, event: Dict[str, Any]):
        raw_data = event.get("raw_data", "")
        source = event.get("source", "Unknown")
        
        self.stats["total_processed"] += 1
        
        # 1. Fast-Path parsing (Simplified for rewrite)
        if "user" in raw_data.lower() and "login" in raw_data.lower():
             ocsf_obj = OCSFAuthentication(
                metadata=OCSFMetadata(normalization_type="standard"),
                time=time.time(),
                src_endpoint=OCSFEndpoint(ip="10.0.0.1"),
                status="Success",
                user="authed_user",
                message="User login attempt natively recognized."
            )
             self.stats["fast_path"] += 1
        else:
            # 2. Agentic Fallback
            ocsf_obj = await self._agentic_fallback(raw_data, source)
            if ocsf_obj:
                self.stats["llm_fallback"] += 1
        
        if ocsf_obj:
            self.out_bus.push(ocsf_obj.model_dump())
        else:
            self.stats["failed"] += 1

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Log-Guardian Pydantic AI Normalizer started.")
        while self.is_running:
            raw_event = await asyncio.to_thread(self.raw_bus.pop)
            if raw_event:
                await self._normalize_log(raw_event)
            else:
                await asyncio.sleep(0.5)

if __name__ == "__main__":
    guardian = LogGuardianAgent()
    asyncio.run(guardian.run())
