"""
GAGGLE-TOPOLOGY: The Asset Relationship Graph.
Tracks User -> Host, Host -> IP, and Host -> Service mappings.

# Satisfies NIST 800-171 Rev 3:
# 3.4.1 - Establish and maintain baseline configurations and inventories.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Set

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA TopologyMapper - %(message)s",
)
logger = logging.getLogger(__name__)

TOPOLOGY_PATH = get_soc_path("reports", "topology.json")

class TopologyMapper:
    """
    Maintains a live relationship graph of the network environment.
    """

    def __init__(self):
        self.discovery_bus = EventBus("discovery_events")
        self.identity_bus = EventBus("identity_events")
        self.network_bus = EventBus("network_telemetry")
        
        # Graph Structure: nodes and edges
        # nodes: { id: { type, label, metadata } }
        # edges: { id: { source, target, type } }
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, Dict[str, Any]] = {}
        
        self.lock = asyncio.Lock()
        self.is_running = False
        
        # [IQ] Doctrine Reference: GAGGLE-TOPOLOGY
        logger.info(f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_gaggle_topology.md')}")
        
        self._load_topology()

    def _load_topology(self):
        """Load existing graph from disk."""
        if os.path.exists(TOPOLOGY_PATH):
            try:
                with open(TOPOLOGY_PATH, "r") as f:
                    data = json.load(f)
                    self.nodes = data.get("nodes", {})
                    self.edges = data.get("edges", {})
                logger.info(f"Loaded topology with {len(self.nodes)} nodes and {len(self.edges)} edges.")
            except Exception as e:
                logger.error(f"Failed to load topology: {e}")

    def _save_topology(self):
        """Persist graph to disk."""
        try:
            with open(TOPOLOGY_PATH, "w") as f:
                json.dump({
                    "nodes": self.nodes,
                    "edges": self.edges,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save topology: {e}")

    async def run(self):
        """Main loop for the Topology Mapper."""
        self.is_running = True
        logger.info("[SQ] Topology Mapper started.")
        
        tasks = [
            asyncio.create_task(self._monitor_discovery()),
            asyncio.create_task(self._monitor_identity()),
            asyncio.create_task(self._monitor_network())
        ]
        await asyncio.gather(*tasks)

    async def _monitor_discovery(self):
        """Ingest new assets from Scout/Sentinel."""
        while self.is_running:
            event = await asyncio.to_thread(self.discovery_bus.pop)
            if event:
                ip = event.get("ip_address")
                mac = event.get("mac_address")
                async with self.lock:
                    self._add_node(ip, "Host", ip, {"mac": mac})
                self._save_topology()
                logger.info(f"Topology: Added Host node for {ip}")
            else:
                await asyncio.sleep(0.1)

    async def _monitor_identity(self):
        """Ingest User-to-Host mappings from Logon events."""
        while self.is_running:
            event = await asyncio.to_thread(self.identity_bus.pop)
            if event:
                user = event.get("username")
                host = event.get("host_ip") or event.get("hostname")
                if user and host:
                    async with self.lock:
                        self._add_node(user, "User", user)
                        self._add_node(host, "Host", host)
                        self._add_edge(user, host, "LOGGED_INTO")
                    self._save_topology()
                    logger.info(f"Topology: Linked User {user} to Host {host}")
            else:
                await asyncio.sleep(0.1)

    async def _monitor_network(self):
        """Ingest Host-to-Host communication mappings."""
        while self.is_running:
            event = await asyncio.to_thread(self.network_bus.pop)
            if event:
                src = event.get("src_ip")
                dst = event.get("dst_ip")
                proto = event.get("protocol")
                if src and dst:
                    async with self.lock:
                        self._add_node(src, "Host", src)
                        self._add_node(dst, "Host", dst)
                        self._add_edge(src, dst, f"COMMUNICATED_{proto}")
                    self._save_topology()
            else:
                await asyncio.sleep(0.5)

    def _add_node(self, node_id: str, type: str, label: str, metadata: Dict = None):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": type,
                "label": label,
                "metadata": metadata or {},
                "first_seen": datetime.now(timezone.utc).isoformat()
            }

    def _add_edge(self, source: str, target: str, edge_type: str):
        edge_id = f"{source}->{target}:{edge_type}"
        if edge_id not in self.edges:
            self.edges[edge_id] = {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "last_seen": datetime.now(timezone.utc).isoformat()
            }

    def get_topology(self) -> Dict[str, Any]:
        """Return the current graph in a ReactFlow compatible format."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges.values())
        }

if __name__ == "__main__":
    mapper = TopologyMapper()
    asyncio.run(mapper.run())
