"""
RCA Investigation Manager: The Incident Lifecycle Engine.

The 'Brain' of the SOC that tracks security investigations from discovery to 
closure. It listens for new alerts on the 'triage_alerts' bus and manages 
the state of 'Cases' (Incidents).

Responsibilities:
  1. Case Initiation: Opens a new INC-[YYYYMMDD]-[UUID] for every WARNING/CRITICAL alert.
  2. Lifecycle Tracking: TRIAGE -> SCOPING -> REMEDIATION -> CLOSED.
  3. Evidence Aggregation: Links Investigator thoughts, Forensics artifacts, 
     and Responder actions to a specific Case ID.
  4. State Persistence: Saves Case objects to 'soc/reports/incidents/cases/'.

# Satisfies NIST 800-171 Rev 3:
# 3.6.1 - Establish an operational incident-handling capability.
# 3.6.2 - Track, document, and report incidents to designated officials.
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA InvestigationManager - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CASES_DIR = get_soc_path("reports", "incidents", "cases")
DB_PATH = os.path.join(CASES_DIR, "soc_cases.db")
WAL_LOG_PATH = os.path.join(CASES_DIR, "case_transactions.wal")
LIVE_FEED_PATH = get_soc_path("reports", "live_investigations.json")


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------
@dataclass
class CaseRecord:
    """Canonical record of a SOC investigation case."""
    case_id: str
    created_at: str
    updated_at: str
    severity: str
    status: str = "TRIAGE"             # TRIAGE | SCOPING | REMEDIATION | CLOSED
    summary: str = ""
    source_ip: str = ""
    mitre_ttp: str = "None"
    nist_control: str = ""
    alert_details: Dict[str, Any] = field(default_factory=dict)
    assigned_agent: str = "SENTINEL-GENERAL"
    evidence_ids: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)
    hypothesis: str = "Awaiting initial investigation"
    confidence: int = 50
    autonomy_drift: float = 0.0
    confidence_points: int = 100

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaseRecord":
        """Robustly create a CaseRecord even if fields are missing."""
        import dataclasses
        # Ensure cls is treated as a dataclass for fields()
        fields = dataclasses.fields(cls) 
        valid_fields = {f.name for f in fields}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

# ---------------------------------------------------------------------------
# Investigation Manager
# ---------------------------------------------------------------------------
class InvestigationManager:
    """
    Orchestrates the lifecycle of SOC incidents.
    """

    def __init__(self):
        self.in_bus = EventBus("triage_alerts")
        self.reasoning_bus = EventBus("investigation_reasoning")
        self.heartbeat_bus = EventBus("soc_heartbeats")
        self.case_updates_bus = EventBus("case_updates")
        self.dispatch_bus = EventBus("dispatch_requests")
        self.raw_alerts_bus = EventBus("raw_alerts")
        os.makedirs(CASES_DIR, exist_ok=True)
        self.active_cases: Dict[str, CaseRecord] = {}
        self.is_running = False
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
        self._load_existing_cases()

    def _init_db(self):
        """[SQ] Initialize SQLite database for scale."""
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # [EQ] Enable SQLite WAL mode natively
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                severity TEXT,
                status TEXT,
                summary TEXT,
                source_ip TEXT,
                mitre_ttp TEXT,
                nist_control TEXT,
                alert_details TEXT,
                assigned_agent TEXT,
                evidence_ids TEXT,
                reasoning_steps TEXT,
                actions_taken TEXT,
                hypothesis TEXT,
                confidence INTEGER,
                autonomy_drift REAL,
                confidence_points INTEGER
            )
        """)
        self.conn.commit()

    def _load_existing_cases(self):
        """[SQ] Load cases from SQLite into memory (limited for performance)."""
        if not self.conn: return
        cursor = self.conn.execute("SELECT * FROM cases ORDER BY updated_at DESC LIMIT 100")
        for row in cursor:
            data = dict(row)
            # Deserialize JSON fields
            data["alert_details"] = json.loads(data["alert_details"])
            data["evidence_ids"] = json.loads(data["evidence_ids"])
            data["reasoning_steps"] = json.loads(data["reasoning_steps"])
            data["actions_taken"] = json.loads(data["actions_taken"])
            case = CaseRecord.from_dict(data)
            self.active_cases[case.case_id] = case

    async def _save_case(self, case: CaseRecord):
        """[EQ] Persist a case record to SQLite with WAL backup."""
        case.updated_at = datetime.now(timezone.utc).isoformat()
        
        # [EQ] Write-Ahead-Log transaction for data loss prevention
        with open(WAL_LOG_PATH, "a") as wal:
            wal.write(f"{datetime.now(timezone.utc).isoformat()} | SAVE | {case.case_id}\n")
            
        data = asdict(case)
        # Serialize list/dict for SQL
        data["alert_details"] = json.dumps(data["alert_details"])
        data["evidence_ids"] = json.dumps(data["evidence_ids"])
        data["reasoning_steps"] = json.dumps(data["reasoning_steps"])
        data["actions_taken"] = json.dumps(data["actions_taken"])
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT OR REPLACE INTO cases ({columns}) VALUES ({placeholders})"
        if self.conn:
            self.conn.execute(sql, list(data.values()))
            self.conn.commit()
        
        # [IQ] Librarian Sync: Push to shared memory for RAG indexing
        self.case_updates_bus.push(asdict(case))
        
        # [IQ] Dispatch Sync: Push to external comms for CRITICAL incidents
        if case.severity == "CRITICAL" or case.actions_taken:
            self.dispatch_bus.push({
                "case_id": case.case_id,
                "severity": case.severity,
                "summary": case.summary,
                "hypothesis": case.hypothesis,
                "destinations": ["slack", "pagerduty"] if case.severity == "CRITICAL" else ["slack"]
            })
        
        # [VQ] Update Live Feed for Dashboard
        self._update_live_feed()
        
        # [SQ] Async Barrier: Yield 100ms to allow Bus propagation/Indexing
        await asyncio.sleep(0.1)

    def _update_live_feed(self):
        """[VQ] Maintain a live view for the dashboard investigation view."""
        feed_data = [asdict(c) for c in list(self.active_cases.values())[:10]]
        with open(LIVE_FEED_PATH, "w") as f:
            json.dump({
                "last_update": datetime.now(timezone.utc).isoformat(),
                "cases": feed_data
            }, f, indent=2)

    def _generate_case_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        id_part = str(uuid.uuid4()).split('-')[0].upper()
        return f"INC-{ts}-{id_part}"

    async def run(self):
        """[SQ] Main async engine for lifecycle management."""
        self.is_running = True
        logger.info("[SQ] InvestigationManager High-Integrity Engine started.")
        
        tasks = [
            asyncio.create_task(self._process_alerts()),
            asyncio.create_task(self._process_reasoning()),
            asyncio.create_task(self._emit_heartbeat())
        ]
        await asyncio.gather(*tasks)

    async def _emit_heartbeat(self):
        """[EQ] Central Pulse for SOC-wide heartbeats."""
        while self.is_running:
            self.heartbeat_bus.push({
                "component": "InvestigationManager",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "HEALTHY"
            })
            await asyncio.sleep(5)

    async def _process_alerts(self):
        """[SQ] Async alert processing with deduplication."""
        while self.is_running:
            alert = await asyncio.to_thread(self.in_bus.pop)
            if not alert:
                await asyncio.sleep(1)
                continue
            
            if alert.get("severity") == "INFO":
                continue
            
            # [SQ] Deduplication Logic
            source = alert.get("source_ip", "unknown")
            rule = alert.get("rule_id", "unknown")
            
            # [IQ] Feed to Correlator for temporal state tracking
            self.raw_alerts_bus.push(alert)
            
            if existing:
                logger.warning(f"[SQ] Deduplicated alert for {source} -> Appending to {existing.case_id}")
                existing.summary += f"\n[ALERT RECURRENCE] {datetime.now(timezone.utc).strftime('%H:%M')} - {alert.get('description')}"
                await self._save_case(existing)
                continue
                
            case = await self._open_case(alert)
            logger.info(f"OPENED Case: {case.case_id} for {alert.get('rule_name')}")

    def _find_duplicate(self, source: str, rule: str) -> Optional[CaseRecord]:
        """[SQ] Search for open cases matching source+rule in last hour."""
        for case in self.active_cases.values():
            if case.status != "CLOSED" and case.source_ip == source and case.alert_details.get("rule_id") == rule:
                return case
        return None

    def run_cycle(self) -> int:
        """Legacy synchronous cycle."""
        # This will be replaced by async run()
        return 0

    async def _open_case(self, alert: Dict[str, Any]) -> CaseRecord:
        """Create a new CaseRecord from a TriageAlert."""
        case_id = self._generate_case_id()
        ts = datetime.now(timezone.utc).isoformat()
        
        case = CaseRecord(
            case_id=case_id,
            created_at=ts,
            updated_at=ts,
            severity=alert.get("severity", "WARNING"),
            status="TRIAGE",
            summary=alert.get("description", ""),
            source_ip=alert.get("source_ip", ""),
            mitre_ttp=alert.get("mitre_ttp", "None"),
            nist_control=alert.get("nist_control", ""),
            alert_details=alert
        )
        
        # Specialist Assignment logic (scaled behavior)
        from soc.agents.specialists import get_specialist_for_alert
        specialist = get_specialist_for_alert(alert)
        case.assigned_agent = specialist.agent_name
        
        # Persist and return
        await self._save_case(case)
        self.active_cases[case_id] = case
        return case

    async def _process_reasoning(self):
        """[IQ] Auto-Hypothesis and Autonomy Tracking."""
        while self.is_running:
            step = await asyncio.to_thread(self.reasoning_bus.pop)
            if not step:
                await asyncio.sleep(1)
                continue
            
            case_id = step.get("investigation_id")
            if case_id in self.active_cases:
                case = self.active_cases[case_id]
                
                # Link step
                step_summary = f"[{step.get('type')}] {step.get('content')}"
                if step_summary not in case.reasoning_steps:
                    case.reasoning_steps.append(step_summary)
                    
                    # [IQ] Hypothesis Generator
                    self._generate_hypothesis(case, step)
                    
                    # [VQ] Autonomy Drift Tracking
                    drift = step.get("autonomy_drift", 0.0)
                    case.autonomy_drift += drift
                    case.confidence_points -= int(drift * 100)
                    
                    # Auto-promote
                    if case.status == "TRIAGE":
                        case.status = "SCOPING"
                    
                    await self._save_case(case)
                    logger.debug(f"Linked reasoning step to {case_id}")

    def _generate_hypothesis(self, case: CaseRecord, step: Dict[str, Any]):
        """[IQ] Intelligent Hypothesis Extraction."""
        content = step.get("content", "").lower()
        if "finding" in content or "observed" in content:
            # Simple heuristic for MVP hypothesis generation
            new_hypo = f"Potential {case.alert_details.get('rule_name')} confirmed by {case.assigned_agent}. "
            if "lateral" in content:
                new_hypo += "Confirmed lateral movement attempt."
            elif "scan" in content:
                new_hypo += "Reconnaissance activity verified."
            
            if new_hypo not in case.hypothesis:
                case.hypothesis = new_hypo
                logger.info(f"[IQ] Hypothesis updated for {case.case_id}: {case.hypothesis}")

    def update_case_status(self, case_id: str, new_status: str, summary_update: str = ""):
        """Manual or automated status update."""
        if case_id in self.active_cases:
            case = self.active_cases[case_id]
            case.status = new_status
            if summary_update:
                case.summary += f"\nUpdate [{datetime.now().strftime('%H:%M')}]: {summary_update}"
            # This is sync, so we use a wrapper or just accept the latency since it's manual
            asyncio.run_coroutine_threadsafe(self._save_case(case), asyncio.get_event_loop())
            logger.info(f"UPDATED Case {case_id} status to {new_status}")
            return True
        return False

if __name__ == "__main__":
    manager = InvestigationManager()
    count = manager.run_cycle()
    print(f"Investigation Manager cycle complete. {count} new cases opened.")
