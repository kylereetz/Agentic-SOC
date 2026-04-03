"""
Telemetry Utility: Tracks operational metrics like local inference load.
Pushes events to the 'business_intel' bus for SENTINEL-NARRATOR.
"""

import json
from datetime import datetime, timezone
from soc.bus.event_queue import EventBus

business_bus = EventBus("business_intel")

def track_compute_usage(agent_name: str, model: str, prompt_cycles: int, completion_cycles: int, case_id: str = "SYSTEM"):
    """
    Push a compute load event to the business intelligence bus.
    """
    total = prompt_cycles + completion_cycles
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent_name,
        "model": model,
        "prompt_cycles": prompt_cycles,
        "completion_cycles": completion_cycles,
        "total_cycles": total,
        "case_id": case_id
    }
    business_bus.push(event)

def track_business_loss(incident_id: str, loss_estimate: float, criticality: str, summary: str):
    """
    Push an estimated fiscal impact event.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incident_id": incident_id,
        "loss_estimate": loss_estimate,
        "criticality": criticality,
        "summary": summary,
        "type": "fiscal_impact"
    }
    business_bus.push(event)
