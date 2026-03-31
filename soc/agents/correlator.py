"""
SENTINEL-CORRELATOR: Intelligent Incident Grouping Engine.
Detects multi-stage attack chains across distributed alerts using Graph Mathematics.

Features:
- [IQ] GraphML Subgraph Clustering (NetworkX).
- [EQ] Temporal Decay of abandoned Entity Nodes (48h rolling window).
- [SQ] Infinite Connection Strength parsing (Property, Temporal, Behavioral Linkage).
- [VQ] Autonomous 'Mega-Incident' Promotion.

# Satisfies NIST 800-171 Rev 3:
# 3.3.5 - Correlate audit record review for investigation and response.
# 3.14.6 - Monitor the information system to detect and respond to attacks.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import networkx as nx

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Correlator - %(message)s",
)
logger = logging.getLogger(__name__)

GRAPHML_OUTPUT_PATH = get_soc_path("reports", "active_campaigns.graphml")

class CorrelatorAgent:
    """
    Intelligent Incident Grouping Engine. Connects disconnected alerts into unified Campaigns.
    """

    def __init__(self):
        self.in_bus = EventBus("raw_alerts") 
        self.out_bus = EventBus("triage_alerts") 
        self.intel_bus = EventBus("intel_feedback") 
        
        self.graph = nx.Graph()
        self.rolling_window_seconds = 172800 # 48 hours temporal decay
        self.promotion_threshold = 100 # Cumulative score required to promote a subgraph
        
        # Track which subgraphs we've already promoted to avoid spamming the same incident
        self.promoted_signatures: Set[str] = set()
        
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] GraphML Correlator Engine activated.")
        
        tasks = [
            asyncio.create_task(self._process_stream()),
            asyncio.create_task(self._cleanup_loop())
        ]
        await asyncio.gather(*tasks)

    def _extract_entities(self, alert: Dict[str, Any]) -> List[tuple]:
        """Extracts unique nodes from a noisy telemetry dictionary."""
        entities = []
        if "source_ip" in alert and alert["source_ip"]:
            entities.append((alert["source_ip"], "IP"))
        if "dest_ip" in alert and alert["dest_ip"]:
            entities.append((alert["dest_ip"], "IP"))
        if "user" in alert and alert["user"]:
            entities.append((alert["user"], "USER"))
        if "file_hash" in alert and alert["file_hash"]:
            entities.append((alert["file_hash"], "HASH"))
        if "process_name" in alert and alert["process_name"]:
            entities.append((alert["process_name"], "PROCESS"))
        return entities

    def _parse_severity(self, alert: Dict[str, Any]) -> int:
        sev = alert.get("severity", "LOW")
        if str(sev).upper() == "CRITICAL": return 80
        if str(sev).upper() == "HIGH": return 50
        if str(sev).upper() == "MEDIUM": return 20
        return 10

    async def _process_stream(self):
        """[IQ] [SQ] Consume alert stream and weave the GraphML Intelligence Fabric."""
        while self.is_running:
            alert = await asyncio.to_thread(self.in_bus.pop)
            if alert:
                entities = self._extract_entities(alert)
                if len(entities) < 2:
                    continue # Not enough data to draw an edge
                    
                rule_name = alert.get("rule_name", alert.get("event_type", "Unknown Event"))
                severity_score = self._parse_severity(alert)
                now = time.time()
                
                # Insert Nodes
                for node_id, node_type in entities:
                    if not self.graph.has_node(node_id):
                        self.graph.add_node(node_id, type=node_type, risk_score=0, event_count=0)
                    
                    self.graph.nodes[node_id]["last_seen"] = now
                    self.graph.nodes[node_id]["risk_score"] += severity_score
                    self.graph.nodes[node_id]["event_count"] += 1
                
                # Draw Edges (Complete subgraph for this specific alert)
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        u = entities[i][0]
                        v = entities[j][0]
                        
                        if not self.graph.has_edge(u, v):
                            self.graph.add_edge(u, v, weight=1, last_seen=now, events=[])
                            
                        # Update Edge
                        self.graph[u][v]["weight"] += 1
                        self.graph[u][v]["last_seen"] = now
                        
                        # Store the behavioral linkage
                        if rule_name not in self.graph[u][v]["events"]:
                            self.graph[u][v]["events"].append(rule_name)
                            
                # Instantly evaluate if this new linkage formed a Campaign
                await self._evaluate_clusters()
            else:
                await asyncio.sleep(1)

    async def _evaluate_clusters(self):
        """
        [IQ] Identify Subgraph mathematical 'Islands'.
        Calculates cumulative Connection Strength across Property Similarity and Behavioral Linkage.
        """
        # Get all isolated island clusters in the graph
        clusters = list(nx.connected_components(self.graph))
        
        for cluster_nodes in clusters:
            if len(cluster_nodes) < 2:
                continue
                
            subgraph = self.graph.subgraph(cluster_nodes)
            
            # Behavioral Linkage Phase: Re-calculate total risk
            cumulative_risk = sum(nx.get_node_attributes(subgraph, "risk_score").values())
            
            # Temporal Proximity: Extracted trivially because dead edges are pruned in background
            # Property Similarity: Extracted trivially by graph structure handling bridging nodes
            
            if cumulative_risk >= self.promotion_threshold:
                # Generate a unique mathematical signature for this cluster
                sorted_nodes = sorted(list(cluster_nodes))
                cluster_signature = "-".join(sorted_nodes)
                
                if cluster_signature in self.promoted_signatures:
                    continue # We already fired a mega-incident for this exact grouping
                
                self.promoted_signatures.add(cluster_signature)
                await self._promote_to_incident(subgraph, cumulative_risk)

    async def _promote_to_incident(self, subgraph: nx.Graph, score: int):
        """[VQ] Emit a high-fidelity correlated mega-incident based on Graph Analytics."""
        nodes = list(subgraph.nodes(data=True))
        edges = list(subgraph.edges(data=True))
        
        # Analyze Behavioral Linkage (Kill Chain Stages)
        stages = set()
        for u, v, data in edges:
            for event in data.get("events", []):
                e_lower = event.lower()
                if "scan" in e_lower or "recon" in e_lower: stages.add("RECON")
                elif "smb" in e_lower or "login" in e_lower or "lateral" in e_lower: stages.add("LATERAL")
                elif "exfil" in e_lower or "upload" in e_lower: stages.add("EXFIL")
        
        active_stage = "UNKNOWN"
        if "RECON" in stages: active_stage = "RECON"
        if "LATERAL" in stages: active_stage = "LATERAL"
        if "EXFIL" in stages: active_stage = "EXFIL"
                
        logger.info(f"[VQ] PROMOTING GRAPHML CAMPAIGN! Nodes: {len(nodes)}, Cum. Risk: {score}, Stage: {active_stage}")
        
        # Format the nodes for easy triage reading
        involved_ips = [n[0] for n in nodes if n[1].get("type") == "IP"]
        involved_users = [n[0] for n in nodes if n[1].get("type") == "USER"]
        
        correlated_alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "CORR_GRAPHML_CAMPAIGN",
            "rule_name": f"Intelligent Incident Grouping: Subgraph Density Exceeded Threshold",
            "severity": "CRITICAL",
            "description": (
                f"Graph Analytics Engine dynamically grouped {len(nodes)} distinct entities into a unified Attack Campaign. "
                f"Detected Stages: {active_stage}. Involved IPs: {involved_ips}. Involved Users: {involved_users}. "
                f"This alerts was mathematically clustered via property similarity and behavioral linkage."
            ),
            "correlation_strength": min(score / 200.0, 1.0), # Normalize up to 1.0
            "subgraph_size": len(nodes),
            "involved_entities": [n[0] for n in nodes]
        }
        self.out_bus.push(correlated_alert)
        
        # Feed high-confidence Indicators back into the Intelligence Bus
        hashes = [n[0] for n in nodes if n[1].get("type") == "HASH"]
        for malicious_ip in involved_ips:
            self.intel_bus.push({
                "entity_id": malicious_ip,
                "file_hashes": hashes,
                "intelligence_type": "GRAPHML_CAMPAIGN_NODE",
                "confidence": min(score / 200.0, 1.0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    async def _cleanup_loop(self):
        """[EQ] Temporal Decay Phase. Prune dead leaf nodes and brittle edges."""
        while self.is_running:
            await asyncio.sleep(60) # Scan every 60s
            now = time.time()
            
            stale_edges = []
            for u, v, data in self.graph.edges(data=True):
                if (now - data.get("last_seen", 0)) > self.rolling_window_seconds:
                    stale_edges.append((u, v))
            
            for u, v in stale_edges:
                self.graph.remove_edge(u, v)
                
            stale_nodes = []
            for n, data in self.graph.nodes(data=True):
                # A node dies if it was last seen 48 hours ago AND it has zero edges left
                if (now - data.get("last_seen", 0)) > self.rolling_window_seconds:
                    if self.graph.degree(n) == 0:
                        stale_nodes.append(n)
                        
            for n in stale_nodes:
                self.graph.remove_node(n)
                
            if len(stale_edges) > 0 or len(stale_nodes) > 0:
                logger.info(f"[EQ] Temporal Decay activated: Pruned {len(stale_edges)} edges & {len(stale_nodes)} orphaned nodes.")
            
            # Reset promoted signatures occasionally to allow re-alerting if campaign worsens
            if len(self.promoted_signatures) > 100:
                self.promoted_signatures.clear()
            
            self._persist_state()

    def _persist_state(self):
        """Export the active Intelligence Fabric into the .graphml format for external analysis."""
        try:
            # We must convert complex types (like lists) to strings for proper GraphML XML serialization
            export_graph = self.graph.copy()
            for u, v, data in export_graph.edges(data=True):
                if "events" in data:
                    data["events"] = ",".join(data["events"])
                    
            nx.write_graphml(export_graph, GRAPHML_OUTPUT_PATH)
        except Exception as e:
            logger.error(f"Failed to export GraphML context: {e}")

if __name__ == "__main__":
    correlator = CorrelatorAgent()
    asyncio.run(correlator.run())
