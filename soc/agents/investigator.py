"""
RCA Investigator Agent: LLM-Backed Autonomous Threat Investigator.

Consumes CRITICAL/WARNING alerts from the 'triage_alerts' bus and runs a
ReAct (Reason → Act → Observe) loop powered by Google Gemini to perform
structured incident investigation.

Each reasoning step is published to the 'investigation_reasoning' bus as a
structured event with type THOUGHT, ACTION, or OBSERVATION, so the SOC
dashboard can render a live reasoning chain and analysts can follow along.

Investigation lifecycle per alert:
  1. THOUGHT  — Agent reasons about what it knows and what to do next
  2. ACTION   — Agent calls a named tool (e.g. query_siem, get_entity_info)
  3. OBSERVATION — Tool result is fed back to the LLM as input for next step
  4. Repeat until the agent issues a CONCLUSION or hits max_steps

Tool outputs are always text (so they can be safely serialised to the bus).
Tools that would trigger real changes draft a containment action
(PENDING_APPROVAL) rather than executing directly — matching the same
human-gating pattern used by the Responder.

# Satisfies NIST 800-171 Rev 3:
# 3.6.1  - Establish an operational incident-handling capability.
# 3.6.2  - Track, document, and report incidents to designated officials.
# 3.14.3 - Monitor system security alerts and take action in response.
# 3.14.6 - Monitor organisational systems to detect attacks.
# 3.3.5  - Correlate audit record review for investigation and response.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import google.generativeai as genai

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

@dataclass
class CaseMemory:
    """[IQ] Shared state between multiple specialists investigating the same case."""
    case_id: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    conclusion_consensus: List[str] = field(default_factory=list) # List of agent names who concluded

    def add_finding(self, agent: str, content: str, mitre: Optional[str] = None):
        self.findings.append({
            "agent": agent,
            "content": content,
            "mitre": mitre,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def update_entity(self, entity_id: str, data: Dict[str, Any]):
        if entity_id not in self.entities:
            self.entities[entity_id] = {}
        self.entities[entity_id].update(data)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Investigator - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_PATH = get_soc_path("configs", "investigator_config.json")
INVESTIGATION_LOG_DIR = get_soc_path("reports", "investigations")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def _load_config(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load Investigator configuration from JSON."""
    defaults: Dict[str, Any] = {
        "gemini_model": "gemini-1.5-pro-latest",
        "max_steps_per_investigation": 10,
        "temperature": 0.2,
        "min_severity": "WARNING",          # Only investigate WARNING and above
        "agent_name": "SENTINEL-01",
        "poll_interval_seconds": 15,
        "save_investigations": True,
        "tool_timeout_seconds": 10,
    }
    try:
        with open(path, "r") as fh:
            user_cfg = json.load(fh)
            defaults.update(user_cfg)
            logger.info(f"Investigator config loaded from {path}")
    except FileNotFoundError:
        logger.warning(f"Config not found at {path} — using defaults.")
    return defaults


# ---------------------------------------------------------------------------
# ReAct step data structure
# ---------------------------------------------------------------------------
STEP_TYPES = ("THOUGHT", "ACTION", "OBSERVATION", "CONCLUSION", "ERROR")

@dataclass
class ReasoningStep:
    """A single step in the ReAct reasoning chain."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()).split("-", 1)[0])
    investigation_id: str = ""
    agent: str = "SENTINEL-01"
    type: str = "THOUGHT"                  # THOUGHT | ACTION | OBSERVATION | CONCLUSION | ERROR
    content: str = ""                      # Human-readable text
    tool: Optional[str] = None             # Populated for ACTION steps
    tool_args: Optional[Dict] = None       # Arguments passed to the tool
    tool_result: Optional[str] = None      # Populated for OBSERVATION steps
    mitre: Optional[str] = None            # MITRE ATT&CK TTP if applicable
    confidence: int = 75                   # 0–100
    duration: Optional[str] = None
    reasoning: str = ""                    # Expanded reasoning (for Explain modal)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hive_contribution: bool = False        # [IQ] True if info came from Hive Memory


# ---------------------------------------------------------------------------
# Simulated Tool Library
# ---------------------------------------------------------------------------
# Tools are callable functions that return a plain-text observation string.
# In production these would call real APIs; here they synthesise plausible
# outputs from the alert data so the ReAct loop can run end-to-end.

class InvestigatorTools:
    """
    Named tool library available to the InvestigatorAgent.
    Each method receives **kwargs from the LLM tool call specification and
    returns a plain-text observation string.
    """

    @staticmethod
    def query_siem(source_ip: str = "", time_range: str = "-1h", **_) -> str:
        """Query the SIEM for recent events from a source IP."""
        logger.info(f"[Tool] query_siem({source_ip}, {time_range})")
        # In production: call Splunk/Sentinel API
        return (
            f"SIEM query [{time_range}] for {source_ip}: "
            "Found 14 events — 3x PowerShell invocations (encoded commands), "
            "1x LSASS memory read, 2x SMB lateral attempts to 192.168.1.108. "
            "No prior baseline activity for this host. Event log gaps detected (possible log clearing T1070.001)."
        )

    @staticmethod
    def get_entity_info(entity_id: str = "", **_) -> str:
        """Retrieve enriched metadata for an entity (IP, host, user, process)."""
        logger.info(f"[Tool] get_entity_info({entity_id})")
        ENTITY_DB = {
            "192.168.1.105": "Host-DX9 | Owner: KR\\admin | OS: Windows 10 Pro | VLAN: 40 | Status: ISOLATED",
            "192.168.1.108": "Host-WS4 | Owner: KR\\jsmith | OS: Windows 11 | VLAN: 40 | Status: ONLINE",
            "KR\\admin":     "User | Dept: IT Operations | Groups: Domain Admins, Schema Admins | Last Logon: 2 hrs ago | Risk: HIGH",
            "svchost.exe":   "Process | PID: 9912 | Parent: services.exe | SHA256: d8f3b1... | Signed: FALSE | Matches Cobalt Strike beacon profile",
        }
        return ENTITY_DB.get(entity_id, f"No enriched record found for '{entity_id}'. Consider manual investigation.")

    @staticmethod
    def check_threat_intel(indicator: str = "", **_) -> str:
        """Look up an IOC against threat intelligence feeds."""
        logger.info(f"[Tool] check_threat_intel({indicator})")
        return (
            f"TI lookup for '{indicator}': "
            "Matched in 3 feeds — MISP cluster APT-29 (Cozy Bear), "
            "Recorded Future risk score 87/100, AlienVault OTX: 14 pulses. "
            "Last seen targeting defence contractors. "
            "Associated TTPs: T1566.001, T1059.001, T1003.001, T1550.003."
        )

    @staticmethod
    def scan_host(target_ip: str = "", **_) -> str:
        """Run a lightweight port/service scan against a target host."""
        logger.info(f"[Tool] scan_host({target_ip})")
        return (
            f"Port scan of {target_ip}: "
            "Open: 445/SMB (signing disabled), 3389/RDP (enabled), 5985/WinRM. "
            "Detected IPC$ share accessible from 2 foreign IPs. "
            "No EDR agent visible. Patch level: 623 days behind."
        )

    @staticmethod
    def correlate_events(investigation_id: str = "", **_) -> str:
        """Correlate all events collected so far in the investigation."""
        logger.info(f"[Tool] correlate_events({investigation_id})")
        return (
            "Correlation complete. High-confidence attack chain identified: "
            "Phishing → Macro execution → PowerShell C2 beacon (60s interval) → "
            "Credential dump (LSASS) → Lateral movement (Pass-the-Ticket) → "
            "Silver Ticket forgery targeting srv-dc01. "
            "Estimated dwell time: 4–6 hours. Blast radius: 3 confirmed hosts, 2 suspected."
        )

    @staticmethod
    def draft_containment(strategy: str = "", target_ip: str = "", **_) -> str:
        """Draft a containment action (PENDING_APPROVAL — never auto-executes)."""
        logger.info(f"[Tool] draft_containment(strategy={strategy}, target={target_ip})")
        action_id = f"ACT_{datetime.utcnow().strftime('%H%M%S')}"
        return (
            f"Containment action drafted [{action_id}] — Status: PENDING_APPROVAL. "
            f"Strategy: {strategy} on {target_ip}. "
            "This action has been queued for human review and will NOT execute automatically. "
            "Analyst must approve via the SOC dashboard Approval Workflow."
        )

    @staticmethod
    def analyse_process(pid: str = "", host: str = "", **_) -> str:
        """Retrieve process tree and memory analysis for a suspected process."""
        logger.info(f"[Tool] analyse_process(pid={pid}, host={host})")
        return (
            f"Process analysis PID {pid} on {host}: "
            "Parent chain: services.exe → svchost.exe [9912]. "
            "Injected PE module found (reflective DLL injection). "
            "Network connections: 203.0.113.45:443 (Cobalt Strike malleable C2). "
            "Memory strings match Mimikatz sekurlsa::logonpasswords signature."
        )

    @staticmethod
    def collect_forensics(target_ip: str = "", artifact_type: str = "MEMORY", **kwargs) -> str:
        """Collect forensic artifacts (MEMORY, PCAP, REGISTRY) for the Evidence Inspector."""
        logger.info(f"[Tool] collect_forensics(target_ip={target_ip}, artifact_type={artifact_type})")
        from soc.agents.forensics import ForensicsAgent
        agent = ForensicsAgent()
        case_id = kwargs.get("investigation_id", "INC-AUTO-COLLECT")
        path = agent.collect_evidence(case_id, target_ip, artifact_type)
        return f"Forensic collection successful. Artifact '{artifact_type}' saved to: {path}. Linked to {case_id}."

    @staticmethod
    def inspect_modbus_traffic(target_ip: str = "", port: int = 502, **_) -> str:
        """[OT Specialist Only] Deep packet inspection for Modbus/TCP industrial protocol."""
        logger.info(f"[Tool] inspect_modbus_traffic(target_ip={target_ip}, port={port})")
        return (
            f"Modbus Inspection for {target_ip}:{port}: "
            "Detected high frequency of 'Function Code 5' (Write Single Coil) targeting registers 0x0001-0x000F. "
            "Traffic pattern deviates from 'PLC-Maintenance-Baseline' by 84%. "
            "Source MAC matches unauthorized engineering laptop [MAC: 00:0A:95:9D:68:16]. "
            "Potential Impact: Emergency Shutdown override attempted."
        )

    @staticmethod
    def audit_ad_privileges(entity_id: str = "", **_) -> str:
        """[Identity Specialist Only] Audit Active Directory privilege changes and GPO modifications."""
        logger.info(f"[Tool] audit_ad_privileges(entity_id={entity_id})")
        return (
            f"AD Privilege Audit for '{entity_id}': "
            "Detected modification to 'Default Domain Controllers Policy' 4 hours ago. "
            "Account '{entity_id}' added to 'Domain Admins' via temporary nested group bypass. "
            "Security Event ID 4728 (Member added to security-enabled global group) flagged. "
            "Risk Level: CRITICAL - Privilege Escalation confirmed."
        )

    @staticmethod
    def verify_remediation_safety(strategy: str = "", target_ip: str = "", **_) -> str:
        """[Remediation Specialist Only] Simulate a containment action to check for critical service disruption."""
        logger.info(f"[Tool] verify_remediation_safety(strategy={strategy}, target={target_ip})")
        CRITICAL_SERVICES = {
            "192.168.1.10": "Primary Domain Controller (SRV-DC01)",
            "192.168.40.5": "Plant HMI Operator Station",
            "10.0.0.1":     "Enterprise Gateway",
        }
        if target_ip in CRITICAL_SERVICES:
            return (
                f"SAFETY WARNING: Target {target_ip} ({CRITICAL_SERVICES[target_ip]}) is a CRITICAL service. "
                f"Applying '{strategy}' will cause immediate operational downtime. "
                "Recommendation: Switch to 'VLAN_ROUTING_FILTER' instead of 'ISOLATE'."
            )
        return f"Safety check PASSED for {target_ip}. '{strategy}' is considered low-risk for the broader network."

    @staticmethod
    def report_false_positive(rule_id: str, source_ip: str, reason: str = "", **_) -> str:
        """[EQ] Signal the Triage agent to auto-tune a noisy or incorrect rule."""
        logger.info(f"[Tool] report_false_positive(rule={rule_id}, ip={source_ip})")
        # In production: push to a 'triage_feedback' bus
        return f"Feedback logged: Rule {rule_id} marked as FP for {source_ip}. Triage auto-tuning initiated."

    @staticmethod
    def consult_librarian(query: str = "", **kwargs) -> str:
        """[IQ] Search institutional memory for similar past cases and hypotheses."""
        logger.info(f"[Tool] consult_librarian('{query}')")
        query_bus = EventBus("memory_queries")
        response_bus = EventBus("memory_responses")
        correlation_id = str(uuid.uuid4())
        
        query_bus.push({
            "query": query,
            "requester": "SENTINEL-INVESTIGATOR",
            "correlation_id": correlation_id
        })
        
        # Poll for response (timeout 5s)
        for _ in range(5):
            time.sleep(1)
            resp = response_bus.pop()
            if resp and resp.get("correlation_id") == correlation_id:
                results = resp.get("results", [])
                if not results: return "Librarian: No relevant past cases found matching this behavior."
                
                formatted = "Librarian: Found relevant past incidents:\n"
                for r in results:
                    formatted += f"- {r['case_id']} (Sim: {r['similarity']}): {r['summary']}. Hypothesis was: {r['hypothesis']}\n"
                return formatted
                
        return "Librarian: Service timed out. Proceed with current evidence."

    # ── Registry ──────────────────────────────────────────────────────────
    TOOL_MAP: Dict[str, Any] = {}  # populated after class definition

    def dispatch(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        """Dispatch a named tool and return its string output."""
        fn = self.TOOL_MAP.get(tool_name)
        if fn is None:
            return f"Unknown tool '{tool_name}'. Available: {list(self.TOOL_MAP.keys())}"
        try:
            # Combine args with caller-supplied context (e.g. investigation_id)
            return fn(**{**args, **kwargs})
        except Exception as exc:
            return f"Tool '{tool_name}' raised an error: {exc}"


# Register tools into the class after definition
InvestigatorTools.TOOL_MAP = {
    "query_siem":        InvestigatorTools.query_siem,
    "get_entity_info":   InvestigatorTools.get_entity_info,
    "check_threat_intel":InvestigatorTools.check_threat_intel,
    "scan_host":         InvestigatorTools.scan_host,
    "correlate_events":  InvestigatorTools.correlate_events,
    "draft_containment": InvestigatorTools.draft_containment,
    "analyse_process":   InvestigatorTools.analyse_process,
    "collect_forensics": InvestigatorTools.collect_forensics,
    "inspect_modbus_traffic": InvestigatorTools.inspect_modbus_traffic,
    "audit_ad_privileges":    InvestigatorTools.audit_ad_privileges,
    "verify_remediation_safety": InvestigatorTools.verify_remediation_safety,
    "report_false_positive": InvestigatorTools.report_false_positive,
    "consult_librarian":     InvestigatorTools.consult_librarian,
}


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """You are SENTINEL-01, an elite autonomous SOC investigator AI running inside Aegis Agent, a next-generation AI Security Operations Center.

You investigate security alerts using a strict ReAct (Reason → Act → Observe) loop. For each step you must respond with a single JSON object — no markdown, no extra text.

Available tools:
- query_siem(source_ip, time_range)       — query SIEM for events from a host
- get_entity_info(entity_id)              — enrich an IP, hostname, user, or process
- check_threat_intel(indicator)           — look up an IP/hash/domain in threat intel
- scan_host(target_ip)                    — lightweight port/service scan
- correlate_events(investigation_id)      — correlate all collected evidence
- analyse_process(pid, host)              — deep process tree + memory analysis
- collect_forensics(target_ip, artifact_type) — collect PCAP, MEMORY, or REGISTRY
- draft_containment(strategy, target_ip) — draft a PENDING_APPROVAL containment action
- report_false_positive(rule_id, source_ip, reason) — flag a rule as noise/FP for auto-tuning
- consult_librarian(query) — [IQ] query shared memory for similar past incidents and TTPs

Response format — EXACTLY one of these three forms per reply:

THOUGHT step:
{"type": "THOUGHT", "content": "Your reasoning here", "mitre": "T1059.001", "confidence": 85, "reasoning": "Extended explanation for the Explain modal"}

ACTION step:
{"type": "ACTION", "tool": "query_siem", "args": {"source_ip": "192.168.1.105", "time_range": "-1h"}, "content": "Querying SIEM for recent events from the suspected host"}

CONCLUSION step (when investigation is complete):
{"type": "CONCLUSION", "content": "Summary of findings", "mitre": "T1566.001", "confidence": 92, "reasoning": "Full narrative"}

Rules:
- Never include anything outside the JSON object
- Never call a non-existent tool
- Alternate THOUGHT → ACTION → (system provides OBSERVATION) → THOUGHT → ...
- Issue CONCLUSION when you have enough evidence or after being asked to conclude
- Always cite a MITRE ATT&CK TTP in THOUGHT and CONCLUSION steps when applicable
- Keep content under 150 words — the UI renders it in a compact card
"""


# ---------------------------------------------------------------------------
# Investigator Agent
# ---------------------------------------------------------------------------
class InvestigatorAgent:
    """
    LLM-backed autonomous investigator.

    Reads triage alerts from the 'triage_alerts' bus, runs a multi-step
    ReAct reasoning loop via the Gemini API, and publishes each step to the
    'investigation_reasoning' bus for real-time UI rendering.

    # Satisfies NIST 800-171 3.6.1, 3.6.2, 3.14.3, 3.14.6
    """

    SEVERITY_RANK = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.cfg = _load_config(config_path)
        self.agent_name: str = self.cfg["agent_name"]
        self.max_steps: int = self.cfg["max_steps_per_investigation"]
        self.min_severity: str = self.cfg["min_severity"]

        # Buses
        self.in_bus  = EventBus("triage_alerts")
        self.out_bus = EventBus("investigation_reasoning")
        self.memory_query_bus = EventBus("memory_queries")
        self.memory_response_bus = EventBus("memory_responses")

        # Tool library
        self.tools = InvestigatorTools()
        
        # [IQ] Hive Context
        self.memory: Optional[CaseMemory] = None
        self.model: Optional[genai.GenerativeModel] = None

        # Investigate report dir
        os.makedirs(INVESTIGATION_LOG_DIR, exist_ok=True)

        # Configure Gemini
        api_key = os.environ.get("GEMINI_API_KEY") or self.cfg.get("gemini_api_key", "")
        if not api_key:
            logger.warning(
                "GEMINI_API_KEY not set. Set the env variable or add "
                "'gemini_api_key' to investigator_config.json."
            )
        genai.configure(api_key=api_key)
        self._reinit_model()

    def _reinit_model(self, custom_prompt: str = None):
        """Allow re-initializing the model with a specialized prompt."""
        prompt = custom_prompt or _SYSTEM_PROMPT
        self.model = genai.GenerativeModel(
            model_name=self.cfg["gemini_model"],
            system_instruction=prompt,
            generation_config=genai.GenerationConfig(
                temperature=self.cfg["temperature"],
                response_mime_type="application/json",
            ),
        )
        logger.info(f"Model re-initialised for {self.agent_name}")

        logger.info(
            f"InvestigatorAgent initialised — model: {self.cfg['gemini_model']}, "
            f"max_steps: {self.max_steps}, min_severity: {self.min_severity}"
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def run_cycle(self) -> int:
        """
        Pop all pending alerts from the triage bus and investigate each one.
        Returns the number of investigations completed.
        """
        investigations_run = 0

        while True:
            alert = self.in_bus.pop()
            if not alert:
                break

            severity = alert.get("severity", "INFO")
            if self.SEVERITY_RANK.get(severity, 0) < self.SEVERITY_RANK.get(self.min_severity, 1):
                logger.info(f"Skipping {severity} alert (below threshold {self.min_severity})")
                continue

            investigation_id = self._generate_investigation_id()
            logger.info(
                f"Starting investigation {investigation_id} "
                f"[{severity}] {alert.get('rule_name', 'Unknown')} — {alert.get('source_ip', '?')}"
            )

            steps = self._investigate(alert, investigation_id)
            investigations_run += 1

            if self.cfg.get("save_investigations", True):
                self._save_investigation(investigation_id, alert, steps)

        return investigations_run

    def run_once_on_alert(self, alert: Dict[str, Any]) -> List[ReasoningStep]:
        """
        Run a single investigation on a supplied alert dict.
        Useful for testing and CLI usage.
        """
        investigation_id = self._generate_investigation_id()
        return self._investigate(alert, investigation_id)

    # ------------------------------------------------------------------
    # Core ReAct Loop
    # ------------------------------------------------------------------
    def _investigate(
        self, alert: Dict[str, Any], investigation_id: str, memory: Optional[CaseMemory] = None
    ) -> List[ReasoningStep]:
        """
        Run the multi-step ReAct reasoning loop for one alert.
        Publishes each step to the out bus and returns the full step list.
        """
        self.memory = memory
        steps: List[ReasoningStep] = []
        chat = self.model.start_chat(history=[])

        # Step 0: inject the alert and hive context
        hive_context = ""
        if self.memory and self.memory.findings:
            hive_context = "\n[HIVE_MEMORY] Previous findings for this case:\n"
            for f in self.memory.findings:
                hive_context += f"- {f['agent']}: {f['content']}\n"

        initial_prompt = self._build_initial_prompt(alert, investigation_id) + hive_context
        messages = [initial_prompt]
        current_message = initial_prompt

        for step_num in range(1, self.max_steps + 1):
            t_start = time.monotonic()

            try:
                response = chat.send_message(current_message)
                raw = response.text.strip()
            except Exception as exc:
                logger.error(f"LLM call failed on step {step_num}: {exc}")
                error_step = self._make_step(
                    investigation_id=investigation_id,
                    type="ERROR",
                    content=f"LLM error: {exc}",
                    confidence=0,
                )
                self._publish_step(error_step)
                steps.append(error_step)
                break

            duration_s = time.monotonic() - t_start

            # Parse LLM response
            parsed = self._parse_llm_response(raw)
            step_type = parsed.get("type", "THOUGHT")

            step = self._make_step(
                investigation_id=investigation_id,
                type=step_type,
                content=parsed.get("content", raw),
                tool=parsed.get("tool"),
                tool_args=parsed.get("args"),
                mitre=parsed.get("mitre"),
                confidence=parsed.get("confidence", 75),
                duration=f"{duration_s:.1f}s",
                reasoning=parsed.get("reasoning", ""),
            )
            steps.append(step)
            self._publish_step(step)
            logger.info(f"[{investigation_id}] Step {step_num}: {step_type}")

            # If CONCLUSION reached, we're done
            if step_type == "CONCLUSION":
                logger.info(f"Investigation {investigation_id} concluded by {self.agent_name}.")
                if self.memory:
                    self.memory.add_finding(
                        self.agent_name, 
                        step.content, 
                        mitre=step.mitre
                    )
                    self.memory.conclusion_consensus.append(self.agent_name)
                break

            # If ACTION, dispatch the tool and inject the OBSERVATION
            if step_type == "ACTION":
                tool_name = parsed.get("tool", "")
                tool_args  = parsed.get("args", {})

                obs_text = self.tools.dispatch(tool_name, tool_args, investigation_id=investigation_id)

                obs_step = self._make_step(
                    investigation_id=investigation_id,
                    type="OBSERVATION",
                    content=obs_text,
                    tool=tool_name,
                    tool_result=obs_text,
                    confidence=100,
                    duration="—",
                )
                steps.append(obs_step)
                self._publish_step(obs_step)
                logger.info(f"[{investigation_id}] OBSERVATION from {tool_name}")

                # Feed observation back as the next message
                current_message = f"OBSERVATION: {obs_text}\n\nContinue your investigation."
            else:
                # THOUGHT — ask LLM to continue
                current_message = "Continue."

        else:
            # Hit step limit — ask for a forced conclusion
            logger.warning(
                f"Investigation {investigation_id} hit max_steps={self.max_steps}. Forcing conclusion."
            )
            try:
                resp = chat.send_message(
                    "You have reached the step limit. Issue a CONCLUSION step summarising your findings."
                )
                parsed = self._parse_llm_response(resp.text.strip())
                conclusion = self._make_step(
                    investigation_id=investigation_id,
                    type="CONCLUSION",
                    content=parsed.get("content", "Investigation complete (step limit reached)."),
                    mitre=parsed.get("mitre"),
                    confidence=parsed.get("confidence", 60),
                    reasoning=parsed.get("reasoning", ""),
                    duration="—",
                )
                steps.append(conclusion)
                self._publish_step(conclusion)
            except Exception as exc:
                logger.error(f"Forced conclusion failed: {exc}")

        return steps

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_initial_prompt(
        self, alert: Dict[str, Any], investigation_id: str
    ) -> str:
        return (
            f"NEW INVESTIGATION: {investigation_id}\n"
            f"Alert:\n{json.dumps(alert, indent=2)}\n\n"
            "Begin your investigation with a THOUGHT step."
        )

    def _parse_llm_response(self, raw: str) -> Dict[str, Any]:
        """Parse LLM JSON response. Returns empty dict on failure."""
        try:
            # Strip markdown code fences if the model wraps them despite mime type
            if raw.startswith("```"):
                raw = "\n".join(raw.splitlines()[1:])
                raw = raw.rstrip("`").rstrip()
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"LLM returned non-JSON: {raw[:120]}…")
            return {"type": "THOUGHT", "content": raw, "confidence": 50}

    def _make_step(self, investigation_id: str, **kwargs) -> ReasoningStep:
        return ReasoningStep(
            investigation_id=investigation_id,
            agent=self.agent_name,
            **kwargs,
        )

    def _publish_step(self, step: ReasoningStep) -> None:
        """Push a reasoning step to the investigation_reasoning bus."""
        # Use asdict with a hint or just a normal dict comprehension if needed
        payload = asdict(step)
        self.out_bus.push(payload)

    def _generate_investigation_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4()).split("-", 1)[0].upper()
        return f"INC-{ts}-{short_uuid}"

    def _save_investigation(
        self,
        investigation_id: str,
        alert: Dict[str, Any],
        steps: List[ReasoningStep],
    ) -> None:
        """Persist a complete investigation record to disk."""
        record = {
            "investigation_id": investigation_id,
            "agent": self.agent_name,
            "started_at": datetime.utcnow().isoformat(),
            "alert": alert,
            "total_steps": len(steps),
            "steps": [asdict(s) for s in steps],
            "status": "CONCLUDED" if any(s.type == "CONCLUSION" for s in steps) else "INCOMPLETE",
        }
        safe_id = investigation_id.replace(":", "-")
        path = os.path.join(INVESTIGATION_LOG_DIR, f"{safe_id}.json")
        with open(path, "w") as fh:
            json.dump(record, fh, indent=2)
        logger.info(f"Investigation saved → {path}")

    # ------------------------------------------------------------------
    # Continuous polling mode
    # ------------------------------------------------------------------
    def start(self) -> None:
        """
        Run the Investigator in daemon mode, polling the triage bus on a
        configurable interval. Blocks the calling thread.
        """
        interval = self.cfg.get("poll_interval_seconds", 15)
        logger.info(
            f"InvestigatorAgent starting in daemon mode — "
            f"polling every {interval}s on 'triage_alerts' bus."
        )
        try:
            while True:
                count = self.run_cycle()
                if count > 0:
                    logger.info(f"Completed {count} investigation(s) this cycle.")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("InvestigatorAgent stopped by user.")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RCA Investigator Agent")
    parser.add_argument(
        "--mode",
        choices=["daemon", "once", "test"],
        default="once",
        help=(
            "daemon: poll triage bus continuously | "
            "once: process all pending alerts and exit | "
            "test: run a synthetic alert end-to-end"
        ),
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to investigator_config.json",
    )
    args = parser.parse_args()

    agent = InvestigatorAgent(config_path=args.config)

    if args.mode == "daemon":
        agent.start()

    elif args.mode == "once":
        n = agent.run_cycle()
        print(f"Completed {n} investigation(s).")

    elif args.mode == "test":
        # Synthetic critical alert for local testing without a real bus
        SYNTHETIC_ALERT = {
            "timestamp": datetime.utcnow().isoformat(),
            "rule_id": "RULE_101",
            "rule_name": "Anomalous PowerShell + LSASS Dump",
            "severity": "CRITICAL",
            "classification": "malicious",
            "source_ip": "192.168.1.105",
            "description": (
                "svchost.exe spawned PowerShell with a base64-encoded payload "
                "and subsequently accessed LSASS memory. Cobalt Strike beacon "
                "pattern with 60-second beaconing interval detected."
            ),
            "nist_control": "3.14.6",
            "confidence": 0.92,
        }
        print(f"\n{'='*60}")
        print("SYNTHETIC ALERT TEST — InvestigatorAgent")
        print(f"{'='*60}\n")

        steps = agent.run_once_on_alert(SYNTHETIC_ALERT)

        print(f"\n{'='*60}")
        print(f"Investigation complete — {len(steps)} reasoning steps")
        print(f"{'='*60}\n")

        for i, s in enumerate(steps, 1):
            print(f"[{i}] {s.type:12s} | {s.agent} | {s.timestamp}")
            print(f"     {s.content[:120]}")
            if s.mitre:
                print(f"     MITRE: {s.mitre}  Confidence: {s.confidence}%")
            print()
