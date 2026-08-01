"""
RCA Investigator Agent: Pydantic AI Edition.

This agent acts as the 'Reasoning Head' of the Multi-Head SOC. It consumes
TriageAlerts and runs an autonomous investigation using Pydantic AI's
ReAct-style execution.

Leverages Llama 3.1 8B via the ModelRegistry with a 16k context window.
"""

import asyncio
import json
import logging
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.utils.telemetry import track_token_usage
from soc.engine.core.model_registry import ModelRegistry


# --- Structured Output Models ---
class InvestigationConclusion(BaseModel):
    """The final verdict of an autonomous investigation."""

    severity: str = Field(
        description="The final severity assessment (INFO, WARNING, CRITICAL)"
    )
    confidence: int = Field(description="Confidence percentage [0-100]")
    mitre_ttps: List[str] = Field(description="Relevant MITRE ATT&CK TTP IDs")
    summary: str = Field(
        description="Direct, concise summary of the confirmed threat activity"
    )
    hypothesis: str = Field(
        description="The primary working hypothesis of what occurred"
    )
    containment_strategy: Optional[str] = Field(
        description="Drafted containment action steps"
    )


@dataclass
class AgentDeps:
    """Dependencies for the Pydantic AI Investigator Agent."""

    out_bus: EventBus
    investigation_id: str
    tools: "InvestigatorTools"
    alert: Dict[str, Any]


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain for UI parity."""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    investigation_id: str = ""
    agent: str = "QUILL-INVESTIGATOR"
    type: str = "THOUGHT"  # THOUGHT | ACTION | OBSERVATION | CONCLUSION
    content: str = ""
    tool: Optional[str] = None
    confidence: int = 100
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Tool Library
# ---------------------------------------------------------------------------
class InvestigatorTools:
    """Simulated tools for SIEM and Forensics."""

    def query_siem(self, source_ip: str, time_range: str) -> str:
        return f"SIEM Results for {source_ip}: 3x Encoded PowerShell observed, 1x LSASS access attempt."

    def check_threat_intel(self, indicator: str) -> str:
        return f"TI Lookup for {indicator}: Matched 'APT-29' related beaconing. Risk: 88/100."

    def collect_forensics(
        self, target_ip: str, artifact_type: str, investigation_id: str
    ) -> str:
        return f"Forensics {artifact_type} collected for {target_ip}. Path: /tmp/forensics_{investigation_id}.pcap"

    def draft_containment(self, strategy: str, target_ip: str) -> str:
        return f"Drafted {strategy} for {target_ip}. Status: PENDING_APPROVAL."


# ---------------------------------------------------------------------------
# Investigator Agent
# ---------------------------------------------------------------------------
class InvestigatorAgent:
    def __init__(self, agent_name: str = "QUILL-INVESTIGATOR"):
        self.agent_name = agent_name
        self.in_bus = EventBus("triage_alerts")
        self.out_bus = EventBus("investigation_reasoning")
        self.tools = InvestigatorTools()

        # Initialize Reasoning Model from Multi-Head Registry
        self.model = ModelRegistry.get_reasoning_model()

        # Pydantic AI Agent
        self.ai_agent = Agent(
            self.model,
            deps_type=AgentDeps,
            result_type=InvestigationConclusion,
            retries=3,
        )
        self._register_tools()

    def _register_tools(self):
        @self.ai_agent.tool
        async def query_siem(
            ctx: RunContext[AgentDeps], source_ip: str, time_range: str = "-1h"
        ) -> str:
            """Query SIEM for events from a source IP."""
            res = ctx.deps.tools.query_siem(source_ip, time_range)
            self._publish_step(
                ctx.deps, "ACTION", f"Querying SIEM for {source_ip}", tool="query_siem"
            )
            self._publish_step(ctx.deps, "OBSERVATION", res)
            return res

        @self.ai_agent.tool
        async def check_threat_intel(ctx: RunContext[AgentDeps], indicator: str) -> str:
            """Look up threat intel for an IP/domain/hash."""
            res = ctx.deps.tools.check_threat_intel(indicator)
            self._publish_step(
                ctx.deps, "ACTION", f"TI Lookup: {indicator}", tool="check_threat_intel"
            )
            self._publish_step(ctx.deps, "OBSERVATION", res)
            return res

        @self.ai_agent.tool
        async def collect_forensics(
            ctx: RunContext[AgentDeps], target_ip: str, artifact_type: str = "MEMORY"
        ) -> str:
            """Collect forensics (MEMORY, PCAP) from a host."""
            res = ctx.deps.tools.collect_forensics(
                target_ip, artifact_type, ctx.deps.investigation_id
            )
            self._publish_step(
                ctx.deps,
                "ACTION",
                f"Forensics {artifact_type} collection: {target_ip}",
                tool="collect_forensics",
            )
            self._publish_step(ctx.deps, "OBSERVATION", res)
            return res

        @self.ai_agent.tool
        async def draft_containment(
            ctx: RunContext[AgentDeps], strategy: str, target_ip: str
        ) -> str:
            """Draft a containment action (ISOLATE, QUARANTINE)."""
            res = ctx.deps.tools.draft_containment(strategy, target_ip)
            self._publish_step(
                ctx.deps,
                "ACTION",
                f"Drafted {strategy} on {target_ip}",
                tool="draft_containment",
            )
            self._publish_step(ctx.deps, "OBSERVATION", res)
            return res

    def _publish_step(
        self, deps: AgentDeps, type: str, content: str, tool: Optional[str] = None
    ):
        step = ReasoningStep(
            investigation_id=deps.investigation_id,
            agent=self.agent_name,
            type=type,
            content=content,
            tool=tool,
        )
        self.out_bus.push(asdict(step))

    async def _investigate(self, alert: Dict[str, Any], investigation_id: str):
        logger.info(f"[{investigation_id}] Starting Pydantic AI ReAct investigation...")

        deps = AgentDeps(
            out_bus=self.out_bus,
            investigation_id=investigation_id,
            tools=self.tools,
            alert=alert,
        )

        system_doctrine = f"You are {self.agent_name}. Investigate the following security alert. Provide a structured conclusion."

        try:
            result = await self.ai_agent.run(
                f"ALERT_PAYLOAD: {json.dumps(alert)}",
                deps=deps,
                system_prompt=system_doctrine,
                model_settings={"temperature": 0.2},
            )

            conclusion = result.data
            logger.info(
                f"[{investigation_id}] Investigation complete: {conclusion.severity}"
            )

            # Final Conclusion Broadcast
            self._publish_step(
                deps, "CONCLUSION", f"{conclusion.severity}: {conclusion.summary}"
            )

            EventBus("investigation_reasoning").push(
                {
                    "type": "CONCLUSION",
                    "investigation_id": investigation_id,
                    "agent": self.agent_name,
                    "content": conclusion.model_dump(),
                }
            )

        except Exception as e:
            logger.error(f"[{investigation_id}] Agent failed: {e}")

    def run_cycle(self) -> int:
        count = 0
        while True:
            msg = self.in_bus.pop()
            if not msg:
                break

            alert = msg.get("alert", msg)
            case_id = msg.get("case_id", f"INC-{secrets.token_hex(4)}")

            asyncio.run(self._investigate(alert, case_id))
            count += 1
        return count


if __name__ == "__main__":
    agent = InvestigatorAgent()
    while True:
        agent.run_cycle()
        time.sleep(10)
