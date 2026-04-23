"""
RCA Triage Agent: IT Noise vs. OT Threat Classifier.
Ingests events from the Scout agent (inventory diffs) and raw packet
metadata, then applies a deterministic rule engine to classify each
event as:
  - INFO     (benign IT noise)
  - WARNING  (suspicious, needs investigation)
  - CRITICAL (likely malicious OT activity)

Rules are loaded from triage_rules.json so clients can tune
thresholds without modifying code.

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organisational systems to detect attacks.
# 3.14.3 - Monitor system security alerts and take action in response.
# 3.6.1  - Establish an operational incident-handling capability.
# 3.3.5  - Correlate audit record review for investigation and response.
"""

import ipaddress
import json
import logging
import os
import asyncio
import hashlib
import random
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.agents.intelligence.fuzzy_evaluator import FuzzyThreatEvaluator
from soc.utils.audio import play_critical_alert, play_milestone_learning

logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = get_soc_path("configs", "triage_rules.json")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class TriageAlert:
    """A single classified alert."""
    timestamp: str
    rule_id: str
    rule_name: str
    severity: str           # INFO, WARNING, CRITICAL
    classification: str     # benign, suspicious, malicious
    source_ip: str
    description: str
    nist_control: str
    mitre_ttp: str = "None"
    raw_event: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0–1.0
    semantic_detail: str = "No detail."
    vector_id: str = "unknown"
    is_correlated: bool = False
    suppression_status: str = "none" # none, suppressed, auto_tuned


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
class TriageEngine:
    """
    Deterministic rule engine that evaluates Scout events against
    configurable JSON rules.

    # Satisfies NIST 800-171 3.14.6 and 3.14.3
    """

    def __init__(self, rules_path: str = DEFAULT_RULES_PATH):
        self.rules: List[Dict[str, Any]] = []
        self.whitelisted_sources: List[str] = []
        self.ot_subnets: List[str] = []
        self.printer_prefixes: List[str] = []
        
        # [IQ] Stateful state
        self.alert_history: Dict[str, List[TriageAlert]] = {}
        self.noise_counters: Dict[str, Dict[str, int]] = {} # IP -> rule_id -> count
        self.known_bad_entities: Dict[str, float] = {} # entity_id -> confidence
        self.known_bad_hashes: Dict[str, float] = {} # file_hash -> confidence
        
        self.fuzzy_evaluator = FuzzyThreatEvaluator()
        
        # [IQ] Layer 4: MARL properties
        self.qtable_path = get_soc_path("configs", "triage_qtable.json")
        self.q_table: Dict[str, Dict[str, float]] = self._load_qtable()
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.05
        
        self._load_rules(rules_path)

    def _load_qtable(self) -> Dict[str, Dict[str, float]]:
        if os.path.exists(self.qtable_path):
            try:
                with open(self.qtable_path, "r") as fh:
                    return json.load(fh)
            except Exception:
                pass
        return {}

    def save_qtable(self):
        with open(self.qtable_path, "w") as fh:
            json.dump(self.q_table, fh, indent=2)

    def _load_rules(self, path: str) -> None:
        """Load triage rules from JSON config."""
        try:
            with open(path, "r") as fh:
                data = json.load(fh)
                self.rules = data.get("rules", [])
                self.whitelisted_sources = data.get("whitelisted_sources", [])
                self.ot_subnets = data.get("ot_subnets", [])
                self.printer_prefixes = data.get("printer_mac_prefixes", [])
                logger.info(
                    f"Loaded {len(self.rules)} triage rules from {path}"
                )
        except FileNotFoundError:
            logger.error(f"Triage rules not found: {path}")
        except Exception as exc:
            logger.error(f"Failed to load triage rules: {exc}")

    # ------------------------------------------------------------------
    # IP / MAC helpers
    # ------------------------------------------------------------------
    def _is_ot_subnet(self, ip: str) -> bool:
        """Check if an IP falls within a configured OT subnet."""
        try:
            addr = ipaddress.ip_address(ip)
            return any(
                addr in ipaddress.ip_network(subnet, strict=False)
                for subnet in self.ot_subnets
            )
        except ValueError:
            return False

    def _is_printer_mac(self, mac: str) -> bool:
        """Check if a MAC address matches a known printer OUI prefix."""
        if not mac:
            return False
        mac_upper = mac.upper().replace("-", ":")
        return any(
            mac_upper.startswith(prefix.upper())
            for prefix in self.printer_prefixes
        )

    def _is_whitelisted(self, ip: str) -> bool:
        """Check if a source IP is whitelisted."""
        return ip in self.whitelisted_sources

    # ------------------------------------------------------------------
    # Core classification
    # ------------------------------------------------------------------
    def classify_event(self, event: Dict[str, Any]) -> Optional[TriageAlert]:
        """
        Evaluate a single event against all loaded rules.
        Returns the highest-severity matching alert, or None if no rule matches.

        # Satisfies NIST 800-171 3.14.6
        """
        # [OCSF Compatibility] Normalize OCSF payload fields to legacy fields for the rule engine
        if "ocsf_class_uid" in event:
            event_type_map = {3002: "authentication", 4001: "network_activity", 9999: "proprietary_ot"}
            event["event_type"] = event_type_map.get(event["ocsf_class_uid"], "unknown_ocsf")
            
            # Extract IP
            if "src_endpoint" in event and event["src_endpoint"]:
                event["ip"] = event["src_endpoint"].get("ip", "")
                
            # Bring unmapped context to the top level for rules
            unmapped = event.get("unmapped", {})
            event["semantic_detail"] = unmapped.get("inferred_meaning", event.get("message", "OCSF Event"))
                
        best_match: Optional[TriageAlert] = None
        severity_order = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}

        for rule in self.rules:
            pattern = rule.get("pattern", {})
            matched = True

            # Match by event_type
            if "event_type" in pattern:
                if event.get("event_type") != pattern["event_type"]:
                    matched = False

            # Match by changed_field (e.g., mac_address, hostname)
            if "changed_field" in pattern and matched:
                if event.get("changed_field") != pattern["changed_field"]:
                    matched = False

            # Match by MAC prefix (e.g. printer detection)
            if "mac_prefix" in pattern and matched:
                mac = event.get("mac", "")
                if not any(
                    mac.upper().startswith(p.upper())
                    for p in pattern["mac_prefix"]
                ):
                    matched = False

            # Match by subnet
            if "subnet_match" in pattern and matched:
                ip = event.get("ip", "")
                try:
                    addr = ipaddress.ip_address(ip)
                    if not any(
                        addr in ipaddress.ip_network(s, strict=False)
                        for s in pattern["subnet_match"]
                    ):
                        matched = False
                except ValueError:
                    matched = False

            # Match by protocol
            if "protocol" in pattern and matched:
                if event.get("protocol") != pattern["protocol"]:
                    matched = False

            # Match by function codes (Modbus)
            if "function_codes" in pattern and matched:
                fc = event.get("function_code")
                if fc not in pattern["function_codes"]:
                    matched = False

            # Match by whitelisted source
            if "source_whitelisted" in pattern and matched:
                ip = event.get("ip", "")
                is_wl = self._is_whitelisted(ip)
                if pattern["source_whitelisted"] != is_wl:
                    matched = False

            if matched:
                alert = TriageAlert(
                    timestamp=event.get(
                        "timestamp", datetime.now(timezone.utc).isoformat()
                    ),
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    severity=rule["severity"],
                    classification=rule["classification"],
                    source_ip=event.get("ip", "Unknown"),
                    description=rule["description"],
                    nist_control=rule.get("nist_control", ""),
                    mitre_ttp=rule.get("mitre_ttp", "None"),
                    raw_event=event,
                    semantic_detail=event.get("semantic_detail", "No detail.")
                )
                
                # [IQ] Add vector_id (pattern hash)
                pattern_str = json.dumps(rule.get("pattern", {}), sort_keys=True)
                alert.vector_id = hashlib.md5(pattern_str.encode()).hexdigest()

                # [EQ] Apply Auto-Tuning / Noise Suppression
                alert = self._apply_auto_tuning(alert)

                # [IQ] Apply Temporal Correlation
                alert = self._check_correlation(alert)

                # Keep the highest severity match
                if best_match is None or severity_order.get(
                    alert.severity, 0
                ) > severity_order.get(best_match.severity, 0):
                    best_match = alert

        # [IQ] Intel Scouter: Boost severity if entity is known bad
        if best_match:
            ip = best_match.source_ip
            file_hash = event.get("file_hash")
            boost = False

            if ip in self.known_bad_entities or (file_hash and file_hash in self.known_bad_hashes):
                boost = True

            if boost and best_match.severity != "CRITICAL":
                old_sev = best_match.severity
                best_match.severity = "CRITICAL" if old_sev == "WARNING" else "WARNING"
                best_match.description += f" [INTEL BOOST from {old_sev}]"
                logger.info(f"[IQ] Boosted {best_match.source_ip} to {best_match.severity}")

        # [IQ] Fuzzy Logic Override (FTSE)
        if best_match:
            metrics = {}

            # Gather generic contextual math metrics pushed from Scout, Sieve, Gatekeeper, EndpointAnalyst, etc.
            if "time_series_math" in event.get("unmapped", {}):
                math_dict = event["unmapped"]["time_series_math"]
                if "sigma_deviation" in math_dict: metrics["entropy_sigma"] = math_dict["sigma_deviation"]
                if "resource_variance" in math_dict: metrics["resource_variance"] = math_dict["resource_variance"]
                if "lineage_depth" in math_dict: metrics["process_lineage_depth"] = math_dict["lineage_depth"]
            
            if "out_degree" in event.get("unmapped", {}):
                metrics["out_degree"] = event["unmapped"]["out_degree"]
            if "in_degree_velocity" in event.get("unmapped", {}):
                metrics["in_degree_velocity"] = event["unmapped"]["in_degree_velocity"]
            if "asymmetry_ratio" in event.get("unmapped", {}):
                metrics["payload_asymmetry"] = event["unmapped"]["asymmetry_ratio"]
            if "subnet_velocity" in event.get("unmapped", {}):
                metrics["subnet_velocity"] = event["unmapped"]["subnet_velocity"]
            if "token_access_freq" in event.get("unmapped", {}):
                metrics["token_access_freq"] = event["unmapped"]["token_access_freq"]

            # Authentications mapping to failed_logins metric
            logins = 0
            if best_match.source_ip in self.alert_history:
                for a in self.alert_history[best_match.source_ip]:
                    if "auth" in a.rule_id.lower() or "login" in a.rule_id.lower() or "fail" in a.description.lower():
                        logins += 1
            if event.get("event_type") == "authentication" and str(event.get("action", "")).lower() == "failed":
                logins += 1
            
            if logins > 0:
                metrics["failed_logins"] = logins

            if metrics:
                threat_score = self.fuzzy_evaluator.evaluate(metrics)
                
                fuzzy_sev = "INFO"
                if threat_score >= 0.8:
                    fuzzy_sev = "CRITICAL"
                elif threat_score >= 0.6:
                    fuzzy_sev = "WARNING"
                elif threat_score >= 0.3:
                    fuzzy_sev = "WARNING"

                if severity_order.get(fuzzy_sev, 0) > severity_order.get(best_match.severity, 0):
                    old_sev = best_match.severity
                    best_match.severity = fuzzy_sev
                    best_match.description = f"[FTSE Override] {best_match.description} (Threat Score: {threat_score:.2f}, escalated from {old_sev})"
                    logger.info(f"[IQ] Fuzzy Logic Overrode severity to {fuzzy_sev} for {best_match.source_ip}. Driving Metrics: {list(metrics.keys())}")

        # [IQ] Layer 4: MARL Epsilon-Greedy Policy
        if best_match:
            q_state_key = f"{best_match.rule_id}_{best_match.severity}"
            if q_state_key in self.q_table:
                q_state = self.q_table[q_state_key]
                # Epsilon Exploration
                if random.random() > self.epsilon:
                    # Exploitation: Follow Q-Table Max decisively
                    if q_state["SUPPRESS"] > q_state["ESCALATE"] + 0.1:
                        old_sev = best_match.severity
                        if best_match.severity == "CRITICAL":
                            best_match.severity = "WARNING"
                        elif best_match.severity == "WARNING":
                            best_match.severity = "INFO"
                        best_match.description += f" [MARL Action: SUPPRESSED from {old_sev} due to historical Q-Value aversion]."
                        logger.info(f"[MARL] Suppressed {q_state_key} for {best_match.source_ip}")
                    elif q_state["ESCALATE"] > q_state["SUPPRESS"] + 0.1:
                        old_sev = best_match.severity
                        best_match.severity = "CRITICAL"
                        if old_sev != "CRITICAL":
                            best_match.description += f" [MARL Action: ESCALATED from {old_sev} due to historical Q-Value reinforcement]."
                            logger.info(f"[MARL] Escalated {q_state_key} for {best_match.source_ip}")
                else:
                    best_match.description += " [MARL: Random Exploration Selected (Epsilon).]"

        # [SECURITY] Structural Is_Stateful Check (Anti-Spoofing DoS Mitigation)
        if best_match and best_match.severity == "CRITICAL":
            is_stateful = self._verify_stateful_correlation(event)
            if not is_stateful:
                logger.warning(
                    f"[SECURITY_OVERRIDE] {best_match.source_ip} alert downgraded from CRITICAL to WARNING: "
                    f"No stateful connection or EDR corroboration (Spoofing Protection)."
                )
                best_match.severity = "WARNING"
                best_match.description += " [SYSTEM OVERRIDE: Downgraded to WARNING due to lack of stateful connection or EDR corroboration (Spoofing Protection)]."
                if best_match.classification == "malicious":
                    best_match.classification = "suspicious"

        return best_match

    def _apply_auto_tuning(self, alert: TriageAlert) -> TriageAlert:
        """[EQ] Downgrade recurring low-level alerts from the same source."""
        ip = alert.source_ip
        rid = alert.rule_id
        
        if ip not in self.noise_counters:
            self.noise_counters[ip] = {}
        
        self.noise_counters[ip][rid] = self.noise_counters[ip].get(rid, 0) + 1
        
        # If > 50 hits of a WARNING rule, downgrade to INFO
        if self.noise_counters[ip][rid] > 50 and alert.severity == "WARNING":
            alert.severity = "INFO"
            alert.suppression_status = "auto_tuned"
            alert.description += " (Auto-tuned: noisy source)"
            
        return alert

    def _check_correlation(self, alert: TriageAlert) -> TriageAlert:
        """[IQ] Multi-stage attack detection."""
        ip = alert.source_ip
        now = datetime.fromisoformat(alert.timestamp)
        
        if ip not in self.alert_history:
            self.alert_history[ip] = []
            
        # Clean old history (24h)
        self.alert_history[ip] = [
            a for a in self.alert_history[ip] 
            if (now - datetime.fromisoformat(a.timestamp)) < timedelta(hours=24)
        ]
        
        # If we have multiple unique WARNINGs from same IP, upgrade to CRITICAL
        unique_rules = {a.rule_id for a in self.alert_history[ip]}
        unique_rules.add(alert.rule_id)
        
        if len(unique_rules) >= 2 and alert.severity == "WARNING":
            alert.severity = "CRITICAL"
            alert.is_correlated = True
            alert.description = f"[CORRELATED] {alert.description}"
            
        self.alert_history[ip].append(alert)
        return alert

    def _verify_stateful_correlation(self, event: Dict[str, Any]) -> bool:
        """
        [SECURITY] Anti-Spoofing DoS Protection.
        Verifies if an event has a completed TCP handshake or EDR correlation.
        Connectionless protocols (UDP/ICMP/Raw) without EDR data are unverified.
        """
        # 1. Check for explicit EDR correlation flag
        if event.get("edr_correlated") is True:
            return True
            
        # 2. Check protocol statefulness
        protocol = str(event.get("protocol", "")).upper()
        if protocol == "TCP":
            flags = str(event.get("flags", "")).upper()
            # If it's TCP, we need evidence of an established connection
            if "ACK" in flags or "PSH" in flags or "FIN" in flags or "RST" in flags:
                return True
                
        # 3. Connectionless/uncorroborated
        return False


# ---------------------------------------------------------------------------
# Triage Agent (Bus-based I/O)
# ---------------------------------------------------------------------------
class TriageAgent:
    """
    Consumes events from the 'discovery_events' Bus channel and
    pushes classified alerts to the 'triage_alerts' Bus channel.

    # Satisfies NIST 800-171 3.6.1 (Incident handling)
    """

    def __init__(self, rules_path: str = DEFAULT_RULES_PATH):
        self.engine = TriageEngine(rules_path)
        self.in_bus = EventBus("discovery_events")
        self.out_bus = EventBus("triage_alerts")
        self.dlq_bus = EventBus("triage_dlq")
        self.intel_bus = EventBus("intel_feedback")
        self.marl_bus = EventBus("marl_rewards")
        
        # [IQ] Doctrine Reference: QUILL-TRIAGE
        logger.info(f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_quill_triage.md')}")
        
        self.report_path = get_soc_path("reports", "triage", "triage_alerts.db")
        self.alert_buffer = []
        self.last_flush = time.time()
        self.is_running = False
        self._init_db()

    def _init_db(self):
        """Initialise SQLite database in WAL mode."""
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        conn = sqlite3.connect(self.report_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                timestamp TEXT,
                rule_id TEXT,
                rule_name TEXT,
                severity TEXT,
                classification TEXT,
                source_ip TEXT,
                description TEXT,
                nist_control TEXT,
                mitre_ttp TEXT,
                confidence REAL,
                semantic_detail TEXT,
                vector_id TEXT,
                is_correlated BOOLEAN,
                suppression_status TEXT,
                raw_event TEXT
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON alerts (timestamp DESC);")
        conn.commit()
        conn.close()

    async def run(self):
        """Async main loop for Triage."""
        self.is_running = True
        logger.info("[SQ] Triage Agent started in async mode.")
        
        tasks = [
            asyncio.create_task(self._process_events()),
            asyncio.create_task(self._marl_worker()),
            asyncio.create_task(self._db_flush_worker())
        ]
        await asyncio.gather(*tasks)

    async def _db_flush_worker(self):
        """[SQ] Periodically flushes accumulated alerts to SQLite."""
        while self.is_running:
            await asyncio.sleep(1)
            now = time.time()
            if self.alert_buffer:
                if len(self.alert_buffer) >= 10000 or (now - self.last_flush) >= 60.0:
                    self._flush_buffer()
                    self.last_flush = time.time()

    def _flush_buffer(self):
        if not self.alert_buffer:
            return
        
        batch = self.alert_buffer[:]
        self.alert_buffer.clear()
        
        try:
            conn = sqlite3.connect(self.report_path)
            cursor = conn.cursor()
            rows = []
            for a in batch:
                s = self._serialise_alert(a)
                raw_e = json.dumps(a.raw_event) if hasattr(a, "raw_event") else "{}"
                rows.append((
                    s["timestamp"], s["rule_id"], s["rule_name"], s["severity"],
                    s["classification"], s["source_ip"], s["description"], s["nist_control"],
                    s["mitre_ttp"], s["confidence"], s["semantic_detail"], s["vector_id"],
                    s["is_correlated"], s["suppression_status"], raw_e
                ))
            
            cursor.executemany('''
                INSERT INTO alerts (
                    timestamp, rule_id, rule_name, severity, classification, source_ip, 
                    description, nist_control, mitre_ttp, confidence, semantic_detail, 
                    vector_id, is_correlated, suppression_status, raw_event
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', rows)
            
            conn.commit()
            conn.close()
            self._update_heatmap_feed(batch)
            logger.debug(f"[SQ] Flushed {len(batch)} alerts to SQLite.")
        except Exception as e:
            logger.error(f"Failed to flush triage database: {e}")

    async def _marl_worker(self):
        """Asynchronously updates the Hive Mind Q-Table based on downstream rewards."""
        logger.info("[MARL] Q-Learning Worker active.")
        while self.is_running:
            reward_event = await asyncio.to_thread(self.marl_bus.pop)
            if reward_event:
                q_state_key = reward_event.get("source_state")
                if not q_state_key:
                    # Backward compatibility safely assumed if rule missing context
                    q_state_key = reward_event.get("source_rule")
                    
                reward = float(reward_event.get("reward", 0.0))
                
                if q_state_key not in self.engine.q_table:
                    self.engine.q_table[q_state_key] = {"ESCALATE": 0.0, "SUPPRESS": 0.0}
                    
                # Bellman update for ESCALATE actions (Since Responder handles actions driven by escalations)
                old_q = self.engine.q_table[q_state_key]["ESCALATE"]
                new_q = old_q + self.engine.alpha * (reward - old_q)
                
                # [IQ] Audio Milestone Trigger: crossing 0.1 threshold (decile)
                if int(new_q * 10) > int(old_q * 10):
                    play_milestone_learning()
                    logger.info(f"[MARL] Q-Value Milestone Reached for {q_state_key}: {new_q}")
                
                self.engine.q_table[q_state_key]["ESCALATE"] = round(new_q, 3)
                
                # If reward is explicitly negative (human rejection), SUPPRESS implicitly gains relative expected value
                if reward < 0:
                    old_sup_q = self.engine.q_table[q_state_key]["SUPPRESS"]
                    self.engine.q_table[q_state_key]["SUPPRESS"] = round(old_sup_q + self.engine.alpha * (1.0 - old_sup_q), 3)
                
                self.engine.save_qtable()
                logger.debug(f"[MARL] Q-Table updated for {q_state_key}: {self.engine.q_table[q_state_key]}")
            else:
                await asyncio.sleep(2)

    async def _process_events(self):
        while self.is_running:
            # 1. Ingest ALL pending Intel Feedback before processing alerts
            while True:
                intel = await asyncio.to_thread(self.intel_bus.pop)
                if not intel:
                    break
                
                entity = intel.get("entity_id")
                hashes = intel.get("file_hashes", [])
                conf = intel.get("confidence", 1.0)
                if entity:
                    self.engine.known_bad_entities[entity] = conf
                for h in hashes:
                    self.engine.known_bad_hashes[h] = conf
                logger.info(f"[IQ] Intel Feedback incorporated for {entity} from Correlator")

            # 2. Process discovery events
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                alert = self.engine.classify_event(event)
                if alert:
                    if alert.severity == "INFO":
                        logger.info(f"[DLQ] Suppressed benign alert: {alert.rule_name}. Routing to DLQ.")
                        self.dlq_bus.push(self._serialise_alert(alert))
                        self._update_persistent_log([alert])
                    else:
                        self.out_bus.push(self._serialise_alert(alert))
                        self._update_persistent_log([alert])
                        
                        # [IQ] Audio Trigger: Critical Alert detected
                        if alert.severity == "CRITICAL":
                            play_critical_alert()

                        logger.info(
                            f"[{alert.severity}] {alert.rule_name} — "
                            f"{alert.source_ip}: {alert.description}"
                        )
                else:
                    logger.warning("[DLQ] Unclassified noise event. Routing to DLQ.")
                    self.dlq_bus.push(event)
            else:
                await asyncio.sleep(1)

    def _serialise_alert(self, a: TriageAlert) -> Dict[str, Any]:
        return {
            "timestamp": a.timestamp,
            "rule_id": a.rule_id,
            "rule_name": a.rule_name,
            "severity": a.severity,
            "classification": a.classification,
            "source_ip": a.source_ip,
            "description": a.description,
            "nist_control": a.nist_control,
            "mitre_ttp": a.mitre_ttp,
            "confidence": a.confidence,
            "semantic_detail": a.semantic_detail,
            "vector_id": a.vector_id,
            "is_correlated": a.is_correlated,
            "suppression_status": a.suppression_status,
        }

    def _update_persistent_log(self, new_alerts: List[TriageAlert]) -> None:
        """Add alerts to the memory buffer to be batched and saved to SQLite."""
        self.alert_buffer.extend(new_alerts)

    def _update_heatmap_feed(self, new_alerts: List[TriageAlert]) -> None:
        """[VQ] Maintain soc/reports/triage/triage_heatmap.json for Dashboard."""
        heatmap_path = get_soc_path("reports", "triage", "triage_heatmap.json")
        heatmap: Dict[str, Any] = {}
        if os.path.exists(heatmap_path):
            try:
                with open(heatmap_path, "r") as fh:
                    val = json.load(fh)
                    if isinstance(val, dict):
                        heatmap = val
            except Exception:
                heatmap = {}

        for a in new_alerts:
            # Aggregate risk by source IP / Subnet
            ip = a.source_ip
            if ip not in heatmap:
                heatmap[ip] = {"hits": 0, "max_severity": "INFO", "last_seen": ""}
            
            entry = heatmap[ip]
            entry["hits"] += 1
            entry["last_seen"] = a.timestamp
            
            # Simple severity upgrade logic
            sev_levels = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}
            cur_sev = entry.get("max_severity", "INFO")
            if sev_levels.get(a.severity, 0) > sev_levels.get(cur_sev, 0):
                entry["max_severity"] = a.severity

        with open(heatmap_path, "w") as fh:
            json.dump(heatmap, fh, indent=2)

    def summary(self, alerts: List[TriageAlert]) -> Dict[str, int]:
        """Quick count by severity."""
        return {
            "INFO": sum(1 for a in alerts if a.severity == "INFO"),
            "WARNING": sum(1 for a in alerts if a.severity == "WARNING"),
            "CRITICAL": sum(1 for a in alerts if a.severity == "CRITICAL"),
        }


if __name__ == "__main__":
    import asyncio
    agent = TriageAgent()
    asyncio.run(agent.run())
