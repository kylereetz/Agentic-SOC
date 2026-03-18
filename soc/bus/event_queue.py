"""
RCA Event Bus: File-Backed Inter-Agent Queue.
Provides a lightweight, durable mechanism for agents to communicate
without direct dependencies on each other's file paths.

Channels:
  discovery_events — Scout (push) -> Triage (pop)
  triage_alerts    — Triage (push) -> Responder (pop) -> Investigator (pop)
  investigation_reasoning — Investigator (push) -> UI (pop) / Audit (pop)
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
import hmac
import hashlib
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# Base soc path
_SOC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUS_ROOT = os.path.join(_SOC_ROOT, "bus")

logger = logging.getLogger(__name__)

class EventBus:
    """
    A secured, file-based FIFO queue per channel.
    Each event is encrypted (Fernet) and signed (HMAC-SHA256).
    """

    def __init__(self, channel_name: str):
        self.channel_name = channel_name
        self.channel_dir = os.path.join(_BUS_ROOT, channel_name)
        self.processed_dir = os.path.join(self.channel_dir, "processed")
        
        # [Hardening] Security Keys
        self.bus_key = os.environ.get("SOC_BUS_KEY")
        self.cipher = None
        
        if self.bus_key and Fernet:
            try:
                # Ensure key is valid Fernet (32 bit base64)
                key_encoded = self.bus_key.encode()
                self.cipher = Fernet(key_encoded)
                logger.info(f"Bus [{channel_name}] initialized with Encryption-at-Rest.")
            except Exception as e:
                logger.error(f"Invalid SOC_BUS_KEY: {e}. Falling back to plain-text (UNSAFE).")
        elif not Fernet:
            logger.warning(f"Bus [{channel_name}] 'cryptography' library missing. Using plain-text (UNSAFE).")
        else:
            logger.warning(f"Bus [{channel_name}] NO SOC_BUS_KEY FOUND. Using plain-text (UNSAFE).")

        # Ensure directories exist
        os.makedirs(self.processed_dir, exist_ok=True)

    def _sign(self, data: bytes) -> str:
        """Create an HMAC-SHA256 signature."""
        if not self.bus_key:
            return "unsigned"
        key_bytes = self.bus_key.encode()
        return hmac.new(key_bytes, data, hashlib.sha256).hexdigest()

    def _verify(self, data: bytes, signature: str) -> bool:
        """Verify the HMAC signature."""
        if not self.bus_key:
            return True # In unsafe mode, we skip verification
        expected = self._sign(data)
        return hmac.compare_digest(expected, signature)

    def push(self, payload: Dict[str, Any]) -> str:
        """
        Push a secured event onto the channel.
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"event_{ts}.json"
        filepath = os.path.join(self.channel_dir, filename)

        raw_json = json.dumps(payload).encode()
        
        # [Hardening] Encrypt and Sign
        if self.cipher and self.bus_key:
            encrypted_data = self.cipher.encrypt(raw_json)
            signature = self._sign(encrypted_data)
            storage_obj = {
                "version": "2.0",
                "secure": True,
                "payload": encrypted_data.decode(),
                "signature": signature
            }
        else:
            storage_obj = {
                "version": "1.0",
                "secure": False,
                "payload": payload, # Plain dict
                "signature": "unsigned"
            }

        with open(filepath, "w") as fh:
            json.dump(storage_obj, fh, indent=2)

        logger.debug(f"Bus [{self.channel_name}] PUSH: {filename} (Secure: {storage_obj['secure']})")
        return filename

    def pop(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve, verify, and decrypt the oldest event.
        """
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
                storage_obj = json.load(fh)
            
            # [Hardening] Verify and Decrypt
            if storage_obj.get("secure"):
                if not self.cipher or not self.bus_key:
                    raise PermissionError("Encrypted event detected but no SOC_BUS_KEY provided.")
                
                payload_str = storage_obj["payload"]
                signature = storage_obj["signature"]
                
                if not self._verify(payload_str.encode(), signature):
                    logger.critical(f"INTEGRITY FAILURE: Bus event {filename} has invalid signature!")
                    # Move to a quarantine folder? For now, move to processed but return None
                    os.replace(src_path, dst_path)
                    return None
                
                decrypted_json = self.cipher.decrypt(payload_str.encode())
                payload = json.loads(decrypted_json)
            else:
                payload = storage_obj["payload"]
            
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
