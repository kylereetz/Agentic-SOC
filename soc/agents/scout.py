"""
RCA Scout Agent: Scheduled Asset Inventory Maintenance.
Runs on a configurable 1–4 hour loop to maintain a real-time asset inventory.
Each cycle:
  1. Runs passive sniffing + active ARP + ICMP via SentinelEngine
  2. Optionally probes industrial protocols via IndustrialScanner
  3. Diffs the new snapshot against the previous one
  4. Persists a timestamped JSON snapshot
  5. Emits structured diff events for the Triage agent

# Satisfies NIST 800-171 Rev 3:
# 3.4.1  - Establish and maintain baseline configurations and inventories.
# 3.12.3 - Monitor security controls on an ongoing basis.
# 3.14.6 - Monitor organizational systems to detect attacks.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import schedule

from engine.core.sentinel import SentinelEngine
from engine.core.industrial import IndustrialScanner
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Scout - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_PATH = get_soc_path("configs", "scout_config.json")


def _load_config(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load Scout configuration from JSON."""
    try:
        with open(path, "r") as fh:
            cfg = json.load(fh)
            logger.info(f"Scout config loaded from {path}")
            return cfg
    except FileNotFoundError:
        logger.warning(f"Config not found at {path} — using defaults.")
        return {}


# ---------------------------------------------------------------------------
# Inventory diffing
# ---------------------------------------------------------------------------
class InventoryDiff:
    """
    Compares two inventory snapshots and categorises changes.

    # Satisfies NIST 800-171 3.4.1 (inventory tracking)
    """

    def __init__(
        self,
        previous: Dict[str, Dict[str, str]],
        current: Dict[str, Dict[str, str]],
    ):
        prev_ips = set(previous.keys())
        curr_ips = set(current.keys())

        self.new_assets: List[Dict[str, str]] = [
            current[ip] for ip in (curr_ips - prev_ips)
        ]
        self.missing_assets: List[Dict[str, str]] = [
            previous[ip] for ip in (prev_ips - curr_ips)
        ]
        self.changed_assets: List[Dict[str, Any]] = []

        for ip in prev_ips & curr_ips:
            if previous[ip] != current[ip]:
                self.changed_assets.append(
                    {"ip": ip, "before": previous[ip], "after": current[ip]}
                )

    @property
    def has_changes(self) -> bool:
        return bool(self.new_assets or self.missing_assets or self.changed_assets)

    def to_events(self) -> List[Dict[str, Any]]:
        """
        Convert the diff into structured events consumable by the
        Triage agent via the Event Bus.
        """
        events: List[Dict[str, Any]] = []
        ts = datetime.utcnow().isoformat()

        for asset in self.new_assets:
            events.append({
                "timestamp": ts,
                "event_type": "asset_new",
                "severity": "WARNING",
                "ip": asset.get("ip_address"),
                "mac": asset.get("mac_address"),
                "detail": "New asset appeared on network",
            })

        for asset in self.missing_assets:
            events.append({
                "timestamp": ts,
                "event_type": "asset_missing",
                "severity": "INFO",
                "ip": asset.get("ip_address"),
                "mac": asset.get("mac_address"),
                "detail": "Previously known asset no longer responding",
            })

        for change in self.changed_assets:
            events.append({
                "timestamp": ts,
                "event_type": "asset_changed",
                "severity": "WARNING",
                "ip": change["ip"],
                "before": change["before"],
                "after": change["after"],
                "detail": "Asset attributes changed between scans",
            })

        return events

    def summary(self) -> str:
        return (
            f"New: {len(self.new_assets)}, "
            f"Missing: {len(self.missing_assets)}, "
            f"Changed: {len(self.changed_assets)}"
        )


# ---------------------------------------------------------------------------
# Scout Agent
# ---------------------------------------------------------------------------
class ScoutAgent:
    """
    Autonomous scheduled scanner that maintains a living asset inventory.

    # Satisfies NIST 800-171 3.4.1 and 3.12.3
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.cfg = _load_config(config_path)
        # Standard reports path via bootstrap
        self.snapshot_dir = get_soc_path("reports", "inventory")
        
        # Inter-agent communication via Event Bus
        self.bus = EventBus("discovery_events")
        
        self.previous_inventory: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Single scan cycle
    # ------------------------------------------------------------------
    def _run_scan_cycle(self) -> None:
        """Execute one full discovery cycle and persist results."""
        logger.info("Scout scan cycle starting …")

        # --- Network discovery ---
        sentinel = SentinelEngine()
        sentinel.passive_sniffing(
            timeout=self.cfg.get("passive_timeout_seconds", 15),
            packet_count=self.cfg.get("passive_packet_count", 200),
        )

        for subnet in self.cfg.get("target_subnets", []):
            sentinel.active_arp_scan(
                target_subnet=subnet,
                timeout=self.cfg.get("arp_timeout_seconds", 3),
            )

        # ICMP sweep on discovered IPs
        discovered_ips = list(sentinel.get_inventory().keys())
        if discovered_ips:
            sentinel.icmp_sweep(
                discovered_ips,
                timeout=self.cfg.get("icmp_timeout_seconds", 1),
            )

        # --- Industrial discovery (optional) ---
        if self.cfg.get("enable_industrial", False):
            ind_scanner = IndustrialScanner(
                inter_probe_delay=self.cfg.get(
                    "industrial_probe_delay_seconds", 0.5
                )
            )
            ot_assets = ind_scanner.scan_targets(
                targets=discovered_ips,
                protocols=self.cfg.get(
                    "industrial_protocols", ["modbus", "ethernetip"]
                ),
            )
            # Merge OT metadata
            for asset in ot_assets:
                inv = sentinel.get_inventory()
                if asset.ip_address in inv:
                    inv[asset.ip_address]["ot_protocol"] = asset.protocol
                    inv[asset.ip_address]["ot_device_info"] = asset.device_info

        current_inventory = sentinel.get_inventory()

        # --- Diff & Bus Push ---
        diff = InventoryDiff(self.previous_inventory, current_inventory)
        if diff.has_changes:
            logger.info(f"Inventory changes detected — {diff.summary()}")
            events = diff.to_events()
            for event in events:
                self.bus.push(event)
            logger.info(f"Pushed {len(events)} events to discovery_events bus.")
        else:
            logger.info("No inventory changes since last cycle.")

        # --- Persist snapshot ---
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_path = os.path.join(
            self.snapshot_dir, f"inventory_{ts}.json"
        )
        with open(snapshot_path, "w") as fh:
            json.dump(current_inventory, fh, indent=2)
        logger.info(f"Snapshot saved → {snapshot_path}")

        # --- Housekeeping: prune old snapshots ---
        self._prune_snapshots()

        self.previous_inventory = current_inventory
        logger.info("Scout scan cycle complete.")

    def _prune_snapshots(self) -> None:
        """Keep only the N most recent snapshots."""
        max_keep = self.cfg.get("max_snapshots_retained", 168)
        files = sorted(
            [
                f
                for f in os.listdir(self.snapshot_dir)
                if f.startswith("inventory_") and f.endswith(".json")
            ]
        )
        if len(files) > max_keep:
            num_to_delete = len(files) - max_keep
            for i in range(num_to_delete):
                old = files[i]
                os.remove(os.path.join(self.snapshot_dir, old))
                logger.debug(f"Pruned old snapshot: {old}")

    # ------------------------------------------------------------------
    # Scheduler loop
    # ------------------------------------------------------------------
    def start(self) -> None:
        """
        Start the Scout agent on a recurring schedule.
        Blocks the current thread.
        """
        interval = self.cfg.get("scan_interval_hours", 2)
        logger.info(f"Scout agent starting — interval: every {interval} hour(s)")

        # Run once immediately
        self._run_scan_cycle()

        # Schedule subsequent runs
        schedule.every(interval).hours.do(self._run_scan_cycle)

        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 s
        except KeyboardInterrupt:
            logger.info("Scout agent stopped by user.")

    def run_once(self) -> None:
        """Run a single scan cycle (useful for testing / CLI)."""
        self._run_scan_cycle()

    def get_latest_events(self) -> List[Dict[str, Any]]:
        """
        [DEPRECATED] Use the Event Bus instead.
        Returns empty list as events are now streamed to the bus.
        """
        logger.warning("get_latest_events() is deprecated. Use EventBus('discovery_events') instead.")
        return []


if __name__ == "__main__":
    agent = ScoutAgent()
    agent.run_once()
