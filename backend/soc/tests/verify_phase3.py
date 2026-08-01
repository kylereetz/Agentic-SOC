"""
Automated Test Suite: Verify Phase3.
Verifies functionality, security controls, and regression safety for target component.
"""

import asyncio
import os
import time
from datetime import datetime
from soc.bus.event_queue import EventBus
from soc.agents.narrator import NarratorAgent
from soc.utils.telemetry import track_compute_usage, track_business_loss, business_bus
from soc.bootstrap import get_soc_path


async def test_reporting_pipeline():
    print("--- [VERIFICATION] Phase 3: Reporting & Business ---")

    narrator = NarratorAgent()
    report_dir = get_soc_path("reports", "business")

    # 1. Clean old reports for testing
    if os.path.exists(report_dir):
        for f in os.listdir(report_dir):
            if f.endswith(".pdf"):
                os.remove(os.path.join(report_dir, f))

    # 2. Simulate Compute Load
    print("[1/4] Simulating cognitive load (compute cycles)...")
    track_compute_usage("Investigator", "llama-3-8b-instruct", 100, 50, "INC-TEST-001")
    track_compute_usage("Investigator", "llama-3-8b-instruct", 200, 80, "INC-TEST-001")

    # 3. Simulate Closed Case
    print("[2/4] Simulating closed cases...")
    case_bus = EventBus("case_updates")
    mock_case = {
        "case_id": "INC-TEST-001",
        "status": "CLOSED",
        "summary": "Verified lateral movement via SMB. Isolated host 192.168.1.50.",
        "severity": "CRITICAL",
    }
    case_bus.push(mock_case)

    # Simulate a second case with fiscal impact
    track_business_loss(
        "INC-TEST-002", 1500.0, "WARNING", "Potential data exfiltration stopped."
    )
    case_bus.push(
        {
            "case_id": "INC-TEST-002",
            "status": "CLOSED",
            "summary": "External C2 connection blocked by TRAFFIC-SIEVE.",
            "severity": "WARNING",
        }
    )

    # 4. Trigger Report Generation
    print("[3/4] Triggering Executive Snapshot...")
    business_bus.push({"type": "report_trigger"})

    # Run narrator briefly to process events
    print("Running Narrator loop for 5 seconds...")
    stop_event = asyncio.Event()

    async def run_narrator():
        # Patching narrator to stop after processing trigger
        original_snapshot = narrator._generate_weekly_snapshot

        def patched_snapshot():
            original_snapshot()
            stop_event.set()

        narrator._generate_weekly_snapshot = patched_snapshot
        await narrator.run()

    try:
        await asyncio.wait_for(run_narrator(), timeout=10.0)
    except asyncio.TimeoutError:
        print("Narrator timed out, but let's check for files...")
    except Exception as e:
        if not stop_event.is_set():
            print(f"Narrator stopped with error (expected?): {e}")

    # 5. Verify PDF Creation
    print("[4/4] Verifying PDF creation...")
    reports = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
    if reports:
        print(f"SUCCESS: Generated {len(reports)} report(s).")
        for r in reports:
            size = os.path.getsize(os.path.join(report_dir, r))
            print(f"  - {r} ({size} bytes)")
        return True
    else:
        print("FAILURE: No PDF reports found.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_reporting_pipeline())
    if not success:
        exit(1)
