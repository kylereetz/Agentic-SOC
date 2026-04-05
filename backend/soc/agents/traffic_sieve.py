"""
GAGGLE-TRAFFIC-SIEVE: Netflow Analysis & Graph-based Exfiltration Detection.
Identifies anomalous paths and deviations in structural edge formations.

IQ Capabilities:
- Graph Storage & Edge Maintenance.
- Novel Path Detection (Structural Shifts).
- Outbound Degree Centrality Spikes.

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organizational systems to detect attacks.
"""

import asyncio
import json
import logging
import time
import os
import math
from datetime import datetime, timezone
from typing import Any, Dict

import networkx as nx

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.graph_persistence import GraphPersistenceManager
from soc.security.ocsf_schema import OCSFNetworkActivity, OCSFMetadata, OCSFEndpoint

logger = logging.getLogger("RCA-TrafficSieve")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA TrafficSieve - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Configurable Learning Period (0 enforces rules immediately for Lab Tests)
LEARNING_PERIOD_SECONDS = int(os.environ.get("SIEVE_LEARNING_PERIOD", 72 * 3600)) 

class TrafficSieveAgent:
    """
    Monitors network telemetry utilizing a structural graph engine.
    """
    def __init__(self):
        self.net_bus = EventBus("network_telemetry")
        # Route to discovery_events so Triage handles it properly, just like LogGuardian
        self.out_bus = EventBus("discovery_events")
        self.is_running = False
        
        # Initialize Graph Engine
        self.graph = GraphPersistenceManager.load_graph()
        self.start_time = time.time()
        self.last_save_time = time.time()

    async def run(self):
        self.is_running = True
        logger.info(f"[SQ] Traffic-Sieve Graph Specialist started. Learning Window: {LEARNING_PERIOD_SECONDS}s")
        
        while self.is_running:
            net_event = await asyncio.to_thread(self.net_bus.pop)
            if net_event:
                await self._analyze_graph_flow(net_event)
            else:
                await asyncio.sleep(0.5)
                
            # Periodically save the graph every minute
            if time.time() - self.last_save_time > 60:
                GraphPersistenceManager.save_graph(self.graph)
                self.last_save_time = time.time()

    async def _analyze_graph_flow(self, flow: Dict[str, Any]):
        src_ip = flow.get("src_ip", "")
        dst_ip = flow.get("dst_ip", "")
        dst_port = flow.get("dst_port", 0)
        bytes_sent = flow.get("bytes", 0)
        protocol = flow.get("protocol", "TCP")
        now = time.time()

        if not src_ip or not dst_ip:
            return  # Invalid flow telemetry

        is_learning_mode = (now - self.start_time) < LEARNING_PERIOD_SECONDS

        # 1. Update Graph Topology
        if not self.graph.has_node(src_ip):
            self.graph.add_node(src_ip, type="host", first_seen=now)
            
        if not self.graph.has_node(dst_ip):
            self.graph.add_node(dst_ip, type="host", first_seen=now)

        novel_edge = False
        volumetric_spike = False
        v_details = {}
        entropy_spike = False
        e_details = {}
        
        if self.graph.has_edge(src_ip, dst_ip):
            edge_data = self.graph[src_ip][dst_ip]
            
            if "byte_bins_window" not in edge_data:
                edge_data["byte_bins_window"] = []
                edge_data["entropy_count"] = 0
                edge_data["entropy_mean"] = 0.0
                edge_data["entropy_m2"] = 0.0

            # 1a. Shannon Entropy AETD logic
            if bytes_sent < 100:
                byte_bin = "<100B"
            elif bytes_sent < 1000:
                byte_bin = "100B-1KB"
            elif bytes_sent < 10000:
                byte_bin = "1KB-10KB"
            elif bytes_sent < 100000:
                byte_bin = "10KB-100KB"
            else:
                byte_bin = ">100KB"
            
            edge_data["byte_bins_window"].append(byte_bin)
            if len(edge_data["byte_bins_window"]) > 50:
                edge_data["byte_bins_window"].pop(0)

            window = edge_data["byte_bins_window"]
            if len(window) >= 20: 
                counts = {}
                for b in window:
                    counts[b] = counts.get(b, 0) + 1
                    
                h_t = 0.0
                total_k = len(window)
                for freq in counts.values():
                    p_x = freq / total_k
                    h_t -= p_x * math.log2(p_x)
                    
                e_count = edge_data["entropy_count"] + 1
                old_h_mean = edge_data["entropy_mean"]
                new_h_mean = old_h_mean + (h_t - old_h_mean) / e_count
                h_m2 = edge_data["entropy_m2"] + (h_t - old_h_mean) * (h_t - new_h_mean)
                
                if e_count > 10:
                    h_var = h_m2 / e_count
                    h_std = h_var ** 0.5
                    if h_std > 0 and h_t > (old_h_mean + 3 * h_std):
                        entropy_spike = True
                        e_details = {
                            "shannon_entropy": round(h_t, 3),
                            "historical_mean": round(old_h_mean, 3),
                            "std_dev": round(h_std, 3),
                            "window_size": total_k,
                        }
                
                edge_data["entropy_count"] = e_count
                edge_data["entropy_mean"] = new_h_mean
                edge_data["entropy_m2"] = h_m2

            
            # Welford's online variance algorithm
            count = edge_data.get("connection_count", 0) + 1
            old_mean = edge_data.get("mean_bytes", 0.0)
            new_mean = old_mean + (bytes_sent - old_mean) / count
            m2 = edge_data.get("m2_bytes", 0.0) + (bytes_sent - old_mean) * (bytes_sent - new_mean)
            
            # Anomaly Tracking
            if count > 10:
                variance = m2 / count
                std_dev = variance ** 0.5
                
                # Anomaly Threshold: 3 Standard Deviations AND at least 1MB absolute difference
                if std_dev > 0 and bytes_sent > (old_mean + 3 * std_dev) and (bytes_sent - old_mean) > 1000000:
                    volumetric_spike = True
                    v_details = {
                        "historical_mean": round(old_mean, 2),
                        "std_dev": round(std_dev, 2),
                        "actual_bytes": bytes_sent,
                        "sigma_deviation": round((bytes_sent - old_mean) / std_dev, 1)
                    }
                    
            edge_data["last_seen"] = now
            edge_data["connection_count"] = count
            edge_data["bytes_transfer"] = edge_data.get("bytes_transfer", 0) + bytes_sent
            edge_data["mean_bytes"] = new_mean
            edge_data["m2_bytes"] = m2
            
            ports_seen = edge_data.get("ports", [])
            if dst_port not in ports_seen:
                novel_edge = True
                edge_data["ports"].append(dst_port)
        else:
            novel_edge = True
            byte_bin = "<100B" if bytes_sent < 100 else ("100B-1KB" if bytes_sent < 1000 else ("1KB-10KB" if bytes_sent < 10000 else ("10KB-100KB" if bytes_sent < 100000 else ">100KB")))
            self.graph.add_edge(
                src_ip, dst_ip, 
                first_seen=now, 
                last_seen=now, 
                connection_count=1,
                bytes_transfer=bytes_sent,
                ports=[dst_port],
                mean_bytes=float(bytes_sent),
                m2_bytes=0.0,
                byte_bins_window=[byte_bin],
                entropy_count=0,
                entropy_mean=0.0,
                entropy_m2=0.0
            )

        # 2. Heuristics & Anomalies
        if not is_learning_mode:
            await self._run_detection_algorithms(src_ip, dst_ip, dst_port, novel_edge, volumetric_spike, v_details, entropy_spike, e_details, protocol, flow)

    async def _run_detection_algorithms(self, src: str, dst: str, port: int, novel_edge: bool, volumetric_spike: bool, v_details: dict, entropy_spike: bool, e_details: dict, proto: str, raw: dict):
        """Analyzes updated graph metrics to trigger Structural or Centrality alerts."""
        alerts_fired = []
        
        # A. Structural Deviation (Zero-Day Path)
        if novel_edge:
            alerts_fired.append({
                "rule_id": "GRAPH_STRUCTURAL_SHIFT",
                "name": "Structural Relational Anomaly",
                "desc": f"Host established an entirely novel path to {dst} on port {port}."
            })
            
        # B. Out-Degree Centrality Spike (Lateral movement scanning)
        out_degree = self.graph.out_degree(src)
        if out_degree > 30: # Hardcoded heuristic spike threshold for lab demo
            alerts_fired.append({
                "rule_id": "GRAPH_CENTRALITY_SPIKE",
                "name": "Degree Centrality Spiked",
                "desc": f"Host outbound volume spike detected: {out_degree} distinct edges."
            })
            
        # C. Volumetric Anomaly (Time Series Data Exfiltration)
        if volumetric_spike:
            alerts_fired.append({
                "rule_id": "GRAPH_VOLUMETRIC_SPIKE",
                "name": "Volumetric Data Anomaly",
                "desc": f"Data transfer of {v_details.get('actual_bytes')} bytes exceeded historical normal of {v_details.get('historical_mean')} bytes by {v_details.get('sigma_deviation')} Sigma.",
                "details": v_details
            })
            
        # D. Shannon Entropy Spike (AETD - Obfuscated Payload Randomness)
        if entropy_spike:
            alerts_fired.append({
                "rule_id": "GRAPH_ENTROPY_SPIKE",
                "name": "Entropy-Based Anomaly",
                "desc": f"Payload size distribution exhibited critical uncertainty (Shannon Entropy: {e_details.get('shannon_entropy')}), exceeding historical threshold.",
                "details": e_details
            })
        
        for anomaly in alerts_fired:
            logger.warning(f"[IQ] {anomaly['name']} detected for {src}.")
            
            unmapped = {
                "graph_anomaly": anomaly["name"],
                "description": anomaly["desc"],
                "out_degree": out_degree,
                "rule_id": anomaly["rule_id"],
                "raw_netflow": raw
            }
            if "details" in anomaly:
                unmapped["time_series_math"] = anomaly["details"]
                
            ocsf_alert = OCSFNetworkActivity(
                metadata=OCSFMetadata(normalization_type="graph_engine"),
                time=time.time(),
                src_endpoint=OCSFEndpoint(ip=src),
                dst_endpoint=OCSFEndpoint(ip=dst, port=port),
                protocol=proto,
                action="Allowed", 
                unmapped=unmapped
            )
            self.out_bus.push(ocsf_alert.model_dump())

if __name__ == "__main__":
    sieve = TrafficSieveAgent()
    asyncio.run(sieve.run())
