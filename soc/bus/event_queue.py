"""
RCA Event Bus: File-Backed Inter-Agent Queue.
Provides a lightweight, durable mechanism for agents to communicate
without direct dependencies on each other's file paths.

Channels:
  discovery_events — Scout (push) -> Triage (pop)
  triage_alerts    — Triage (push) -> Responder (pop)
  patch_manifests — Patch Pilot (push) -> Responder (pop)

Usage:
    from soc.bus.event_queue import EventBus
    bus = EventBus("discovery_events")
    bus.push({"ip": "192.168.1.1", "event": "asset_new"})
    
    # In another process
    event = bus.pop()
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Base soc path
_SOC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUS_ROOT = os.path.join(_SOC_ROOT, "bus")

logger = logging.getLogger(__name__)


class EventBus:
    """
    A simple, file-based FIFO queue per channel.
    Each event is a JSON file named with its timestamp.
    """

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.channel_dir = os.path.join(_BUS_ROOT, channel_name)
        self.processed_dir = os.path.join(self.channel_dir, "processed")
        
        # Ensure directories exist (failsafe if bootstrap wasn't run)
        os.makedirs(self.processed_dir, exist_ok=True)

    def push(self, payload: Dict[str, Any]) -> str:
        """
        Push an event onto the channel.
        Returns the filename created.
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"event_{ts}.json"
        filepath = os.path.join(self.channel_dir, filename)

        with open(filepath, "w") as fh:
            json.dump(payload, fh, indent=2)

        logger.debug(f"Bus [{self.channel_name}] PUSH: {filename}")
        return filename

    def pop(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve and 'acknowledge' the oldest event in the channel.
        Moves the file to the 'processed' subdirectory.
        """
        # List all event files in the channel (not including the processed dir)
        files = sorted([
            f for f in os.listdir(self.channel_dir)
            if f.startswith("event_") and f.endswith(".json")
        ])

        if not files:
            return None

        filename = files[0]
        src_path = os.path.join(self.channel_dir, filename)
        dst_path = os.path.join(self.processed_dir, filename)

        try:
            with open(src_path, "r") as fh:
                payload = json.load(fh)
            
            # Move to processed
            os.replace(src_path, dst_path)
            logger.debug(f"Bus [{self.channel_name}] POP: {filename}")
            return payload

        except Exception as exc:
            logger.error(f"Bus [{self.channel_name}] POP error on {filename}: {exc}")
            return None

    def peek(self) -> Optional[Dict[str, Any]]:
        """See the oldest event without moving it to processed."""
        files = sorted([
            f for f in os.listdir(self.channel_dir)
            if f.startswith("event_") and f.endswith(".json")
        ])

        if not files:
            return None

        filepath = os.path.join(self.channel_dir, files[0])
        try:
            with open(filepath, "r") as fh:
                return json.load(fh)
        except Exception:
            return None

    def size(self) -> int:
        """Return the count of pending events in the channel."""
        return len([
            f for f in os.listdir(self.channel_dir)
            if f.startswith("event_") and f.endswith(".json")
        ])


if __name__ == "__main__":
    # Internal test
    logging.basicConfig(level=logging.DEBUG)
    test_bus = EventBus("test_channel")
    fn = test_bus.push({"test": True, "time": time.time()})
    print(f"Pushed: {fn}")
    p = test_bus.pop()
    print(f"Popped: {p}")
