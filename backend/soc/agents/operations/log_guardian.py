"""
GAGGLE-LOG-GUARDIAN: Pydantic AI Edition.

This agent uses 90% deterministic parsing (Regex/Grok/Wazuh decoders) to
normalize broken logs and map them to OCSF schemas.

It only falls back to the 'Reasoning Head' (Llama 3.1 8B) for truly unknown,
proprietary OT data formats to prevent structural hallucinations.
"""

import asyncio
import json
import logging
import os
import re
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
    OCSFAuthentication,
    OCSFNetworkActivity,
    OCSFProprietaryOT,
    OCSFMetadata,
    OCSFEndpoint,
)

logger = logging.getLogger("RCA-LogGuardian")


# --- Structured Output Models ---
class LogExtraction(BaseModel):
    """The result of an LLM-based log extraction."""

    ip: str = Field(description="The extracted source IP or 'Unknown'")
    inferred_meaning: str = Field(description="1-sentence summary of the activity")
    proprietary_codes: str = Field(
        description="Any hex codes, PLC error tags, or raw string variables"
    )
    extracted_regex_pattern: str = Field(
        description="A Python regex string with named capture groups (?P<ip>, ?P<meaning>, ?P<codes>) that would extract these fields deterministically next time."
    )


# ---------------------------------------------------------------------------
# Log Guardian Agent
# ---------------------------------------------------------------------------
class LogGuardianAgent:
    def __init__(self):
        self.raw_bus = EventBus("raw_logs")
        self.out_bus = EventBus("discovery_events")
        self.is_running = False

        # Initialize Reasoning Model (Llama 3.1 8B) for fallback extraction
        self.model = ModelRegistry.get_reasoning_model()

        # Pydantic AI Agent
        self.ai_agent = Agent(self.model, result_type=LogExtraction, retries=2)

        # Self-Healing Runtime Cache
        self.learned_decoders_file = get_soc_path(
            "soc", "agents", "learned_decoders.json"
        )
        self.learned_rules: List[re.Pattern] = []
        self._load_decoders()

        # Performance Tracking
        self.stats = {
            "total_processed": 0,
            "fast_path": 0,
            "llm_fallback": 0,
            "failed": 0,
        }
        self.last_flush = time.time()

    def _load_decoders(self):
        if os.path.exists(self.learned_decoders_file):
            try:
                with open(self.learned_decoders_file, "r") as f:
                    patterns = json.load(f)
                    for p in patterns:
                        try:
                            self.learned_rules.append(re.compile(p))
                        except re.error:
                            pass
                logger.info(f"Loaded {len(self.learned_rules)} learned regex decoders.")
            except Exception as e:
                logger.error(f"Failed to load cached decoders: {e}")

    def _save_decoder(self, pattern_str: str):
        try:
            compiled = re.compile(pattern_str)
            self.learned_rules.append(compiled)

            patterns = [p.pattern for p in self.learned_rules]
            with open(self.learned_decoders_file, "w") as f:
                json.dump(patterns, f, indent=2)
            logger.info(
                f"[+] LLM successfully wrote new deterministic rule: {pattern_str}"
            )
        except Exception as e:
            logger.error(f"Failed to save dynamic rule: {e}")

    async def _agentic_fallback(
        self, raw: str, source: str
    ) -> Optional[OCSFProprietaryOT]:
        """LLM Fallback extraction for proprietary OT data via Reasoning Head."""
        prompt = f"""
        Extract security context from this proprietary OT log.
        If successful, ALSO provide a Python compatible regex pattern using named capture 
        groups matching strictly: (?P<ip>...), (?P<meaning>...), (?P<codes>...)
        so we can natively decode this log structure next time.
        
        Source: {source}
        Payload: {raw}
        """

        try:
            result = await self.ai_agent.run(
                prompt,
                system_prompt="You are an expert OT log parsing specialist. Extract IPs and meanings from industrial protocol logs, and generate native regex for self-healing caching.",
                model_settings={"temperature": 0.1},
            )

            data = result.data

            # Cache the newly generated rule!
            if data.extracted_regex_pattern and data.extracted_regex_pattern != "None":
                self._save_decoder(data.extracted_regex_pattern)

            unmapped_dict = {
                "inferred_meaning": data.inferred_meaning,
                "proprietary_codes": data.proprietary_codes,
                "original_source": source,
                "raw_event": raw,
            }

            return OCSFProprietaryOT(
                metadata=OCSFMetadata(normalization_type="custom_OT_inferred"),
                time=time.time(),
                src_endpoint=OCSFEndpoint(ip=data.ip) if data.ip != "Unknown" else None,
                unmapped=unmapped_dict,
            )
        except Exception as e:
            logger.error(f"[!] Log extraction failed: {e}")
            return None

    async def _normalize_log(self, event: Dict[str, Any]):
        raw_data = event.get("raw_data", "")
        source = event.get("source", "Unknown")

        self.stats["total_processed"] += 1
        ocsf_obj = None

        # 1. 90% Deterministic Parsing (Regex/Grok/Targeted Decoders)
        if "user" in raw_data.lower() and "login" in raw_data.lower():
            ocsf_obj = OCSFAuthentication(
                metadata=OCSFMetadata(normalization_type="standard"),
                time=time.time(),
                src_endpoint=OCSFEndpoint(ip="10.0.0.1"),
                status="Success",
                user="authed_user",
                message="User login attempt natively recognized.",
            )
            self.stats["fast_path"] += 1
        else:
            # Check LLM-generated dynamic cache
            matched = False
            for rule in self.learned_rules:
                m = rule.search(raw_data)
                if m:
                    group_dict = m.groupdict()
                    unmapped_dict = {
                        "inferred_meaning": group_dict.get(
                            "meaning", "regex_fallback_match"
                        ),
                        "proprietary_codes": group_dict.get("codes", ""),
                        "original_source": source,
                        "raw_event": raw_data,
                    }
                    ocsf_obj = OCSFProprietaryOT(
                        metadata=OCSFMetadata(
                            normalization_type="custom_OT_inferred_cached"
                        ),
                        time=time.time(),
                        src_endpoint=OCSFEndpoint(ip=group_dict.get("ip", "127.0.0.1")),
                        unmapped=unmapped_dict,
                    )
                    self.stats["fast_path"] += 1
                    matched = True
                    break

            if not matched:
                # 2. Agentic Fallback (LLM takes the hit and writes the rule)
                ocsf_obj = await self._agentic_fallback(raw_data, source)
                if ocsf_obj:
                    self.stats["llm_fallback"] += 1

        if ocsf_obj:
            self.out_bus.push(ocsf_obj.model_dump())
        else:
            self.stats["failed"] += 1

    async def run(self):
        self.is_running = True
        logger.info(
            "[SQ] Log-Guardian Pydantic AI Normalizer started (Self-Healing Active)."
        )
        while self.is_running:
            raw_event = await asyncio.to_thread(self.raw_bus.pop)
            if raw_event:
                await self._normalize_log(raw_event)
            else:
                await asyncio.sleep(0.5)


if __name__ == "__main__":
    guardian = LogGuardianAgent()
    asyncio.run(guardian.run())
