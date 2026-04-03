"""
SENTINEL-ENDPOINT-ANALYST
Dedicated agent for real-time host execution monitoring (Sysmon EID 1, EID 8, etc).
"""
import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault
from engine.core.llm_client import LLMClient

logger = logging.getLogger("RCA-EndpointAnalyst")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Endpoint Analyst - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class EndpointAnalystAgent:
    def __init__(self):
        self.in_bus = EventBus("endpoint_telemetry")
        self.out_bus = EventBus("triage_alerts")
        self.is_running = False
        self.agent_id = "SENTINEL-ENDPOINT-ANALYST"
        
        self.llm_client = LLMClient()
        
        # UEBA Configuration
        self.jaccard_threshold = float(os.environ.get("JACCARD_THRESHOLD", 0.7))
        self.user_vectors: Dict[str, Set[str]] = {}
        self.clusters: List[Set[str]] = []
        self._init_db()

    def _init_db(self):
        """[SQ] Setup Zero-Trust database connection for persistent behavioral memory."""
        from soc.network.service_mesh import ServiceMesh
        db_path = get_soc_path("reports", "endpoint_clustering.db")
        self.conn = ServiceMesh.connect_db(client_identity="endpoint_analyst", db_path=db_path, negotiated_cipher="TLS_AES_256_GCM_SHA384")
        self.conn.row_factory = __import__('sqlite3').Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_processes (
                username TEXT,
                process TEXT,
                PRIMARY KEY (username, process)
            )
        """)
        self.conn.commit()

        # Hydrate active memory
        cursor = self.conn.execute("SELECT username, process FROM user_processes")
        for row in cursor:
            u, p = row["username"], row["process"]
            if u not in self.user_vectors:
                self.user_vectors[u] = set()
            self.user_vectors[u].add(p)
            
        self._recalculate_clusters_sync()

    def _jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        """Calculate the structural overlap between two executable footprints."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union

    def _recalculate_clusters_sync(self):
        """[IQ] Mathematically cluster users loosely based on K-Medoids/Jaccard mapping."""
        users = list(self.user_vectors.keys())
        new_clusters = []
        assigned = set()
        
        for idx, u1 in enumerate(users):
            if u1 in assigned:
                continue
                
            current_cluster = {u1}
            assigned.add(u1)
            
            for u2 in users[idx+1:]:
                if u2 in assigned:
                    continue
                
                # If User 2 shares 70% of User 1's behavioral footprint, bind them.
                sim = self._jaccard_similarity(self.user_vectors[u1], self.user_vectors[u2])
                if sim >= self.jaccard_threshold:
                    current_cluster.add(u2)
                    assigned.add(u2)
                    
            new_clusters.append(current_cluster)
            
        self.clusters = new_clusters
        logger.info(f"[IQ] Rebalanced Peer Groups. Unified {len(users)} users into {len(self.clusters)} mathematical clusters.")

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Endpoint Analyst started, listening to endpoint_telemetry.")
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(1.0)
                
    async def _process_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type", "unknown")
        command_line = event.get("command_line", "").lower()
        process_name = event.get("process_name", "").lower()
        user = event.get("user", "")

        # UEBA Zero-Config Peer Group Deviation Check
        if user and process_name:
            is_new_process = False
            if user not in self.user_vectors:
                self.user_vectors[user] = set()
            
            if process_name not in self.user_vectors[user]:
                self.user_vectors[user].add(process_name)
                is_new_process = True
                
                # Persist to SQLite Memory
                try:
                    self.conn.execute("INSERT OR IGNORE INTO user_processes (username, process) VALUES (?, ?)", (user, process_name))
                    self.conn.commit()
                except Exception as e:
                    logger.error(f"DB Insert Flow Error: {e}")

            if is_new_process:
                my_cluster = None
                for c in self.clusters:
                    if user in c:
                        my_cluster = c
                        break
                
                # Mathematical Anomaly Check: Is this process entirely foreign to my entire peer group?
                if my_cluster and len(my_cluster) >= 2:
                    peer_group_dev = True
                    for peer in my_cluster:
                        if peer != user and process_name in self.user_vectors.get(peer, set()):
                            peer_group_dev = False
                            break
                            
                    if peer_group_dev:
                        reason = f"PEER GROUP DEVIATION: User '{user}' executed '{process_name}', which has " \
                                 f"never been executed by anyone else in their naturally mapped Behavioral Cluster ({len(my_cluster)} members)."
                        
                        await self._escalate(event, "CRITICAL", reason, 0.95, rule_id="PEER_GROUP_DEVIATION", override_name="Behavioral Peer Deviation")
                        return
                
                self._recalculate_clusters_sync()
        
        # Heuristic 1: Encoded PowerShell (EID 1)
        if event_type == "sysmon" and event.get("eid") == 1:
            if "powershell" in event.get("process_name", "").lower():
                if "-enc" in command_line or "-encodedcommand" in command_line or "hidden" in command_line:
                    await self._escalate(event, "WARNING", "Heuristic: Obfuscated PowerShell execution detected natively.", 0.9)
                    return
        
        # Heuristic 2: Memory Injection (EID 8)
        if event_type == "sysmon" and event.get("eid") == 8:
            await self._escalate(event, "CRITICAL", "Heuristic: Remote Thread Creation (Code Injection) detected natively.", 0.95)
            return

        # LLM Fallback Analysis for ambiguous behavioral chains
        if command_line:
            prompt = f"""
            Analyze this command line for malicious intent. Look for lateral movement, recon, or defense evasion.
            Event: {json.dumps(event)}
            Reply purely in JSON: {{"malicious": true/false, "reason": "...", "severity": "WARNING"}}
            """
            try:
                res = await self.llm_client.generate_json(prompt)
                
                if res.get("malicious"):
                    await self._escalate(event, res.get("severity", "WARNING"), f"LLM Match: {res.get('reason')}", 0.8)
            except Exception as e:
                logger.error(f"[!] LLM Parsing failed for Endpoint Analyst: {e}")

    async def _escalate(self, event: Dict[str, Any], severity: str, reason: str, confidence: float, rule_id: str = "EP_001", override_name: str = "Endpoint Behavioral Anomaly"):
        # Package and ship directly to Triage
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": rule_id,
            "rule_name": override_name,
            "severity": severity,
            "classification": "malicious" if severity == "CRITICAL" else "suspicious",
            "source_ip": event.get("source_ip", "Unknown"),
            "description": reason,
            "nist_control": "3.14.6",
            "mitre_ttp": event.get("mitre_ttp", "T1059"),
            "raw_event": event,
            "confidence": confidence,
            "agent_id": self.agent_id,
            "evidence_array": [hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()],
            "vector_id": "endpoint_behavior_vector"
        }
        self.out_bus.push(alert)
        logger.warning(f"[{severity}] Endpoint Analyst Escalated to Triage: {reason}")

if __name__ == "__main__":
    agent = EndpointAnalystAgent()
    asyncio.run(agent.run())
