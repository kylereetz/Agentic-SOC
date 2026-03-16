"""
RCA SOC Bootstrap: Environment & Directory Initialization.
Ensures all required data directories and inter-agent communication
paths exist before any SOC agents are started.

Directory Structure:
  soc/reports/
    inventory/    — Scout snapshots
    triage/       — Classified alerts
    patches/      — Remediation manifests
    incidents/    — Responder logs
    pdf/          — Auditor reports
  soc/bus/        — Inter-agent event queue folders

# Satisfies NIST 800-171 Rev 3:
# 3.4.1 - Establish and maintain baseline configurations and inventories.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Bootstrap - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Paths
# ---------------------------------------------------------------------------
SOC_ROOT = os.path.dirname(os.path.abspath(__file__))

REPORT_DIRS = [
    os.path.join(SOC_ROOT, "reports", "inventory"),
    os.path.join(SOC_ROOT, "reports", "triage"),
    os.path.join(SOC_ROOT, "reports", "patches"),
    os.path.join(SOC_ROOT, "reports", "incidents"),
    os.path.join(SOC_ROOT, "reports", "pdf"),
]

BUS_CHANNELS = [
    "discovery_events",
    "triage_alerts",
    "patch_manifests",
]


# ---------------------------------------------------------------------------
# Initialisation Logic
# ---------------------------------------------------------------------------
def bootstrap_soc() -> bool:
    """
    Create necessary subdirectories and validate the environment.
    Returns True if successful, False otherwise.
    """
    logger.info("Initializing RCA SOC environment …")

    try:
        # 1. Create report directories
        for path in REPORT_DIRS:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.debug(f"Created report directory: {path}")

        # 2. Create bus directories
        bus_root = os.path.join(SOC_ROOT, "bus")
        for channel in BUS_CHANNELS:
            channel_path = os.path.join(bus_root, channel)
            processed_path = os.path.join(channel_path, "processed")
            os.makedirs(processed_path, exist_ok=True)
            logger.debug(f"Created bus channel: {channel}")

        # 3. Validation: Requirements check
        # (Optional: we could check for scapy, pandas, etc. here)

        logger.info("RCA SOC bootstrap complete.")
        return True

    except Exception as exc:
        logger.error(f"Bootstrap failed: {exc}")
        return False


def get_soc_path(*args) -> str:
    """Return an absolute path relative to the soc/ directory."""
    return os.path.join(SOC_ROOT, *args)


if __name__ == "__main__":
    if bootstrap_soc():
        print("\n[SUCCESS] SOC environment is ready.")
    else:
        print("\n[FAILURE] SOC bootstrap failed. Check logs.")
        sys.exit(1)
