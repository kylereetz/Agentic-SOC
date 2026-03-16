"""
RCA SOC API: FastAPI Interface for SOC Monitoring & Control.
Exposes status, inventory, alerts, and the human approval gate.
"""

import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.agents.responder import ResponderAgent

app = FastAPI(title="RCA SOC API", version="0.1.0")

# Paths
INVENTORY_DIR = get_soc_path("reports", "inventory")
TRIAGE_LOG = get_soc_path("reports", "triage", "triage_alerts.json")
PENDING_ACTIONS = get_soc_path("reports", "incidents", "pending_actions.json")

# Data Models
class StatusResponse(BaseModel):
    scout_status: str
    bus_sizes: Dict[str, int]

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Return health and queue sizes of the SOC components."""
    bus_channels = ["discovery_events", "triage_alerts", "patch_manifests"]
    sizes = {}
    for channel in bus_channels:
        bus = EventBus(channel)
        sizes[channel] = bus.size()
    
    return {
        "scout_status": "operational", # Placeholder for real heartbeat check
        "bus_sizes": sizes
    }

@app.get("/inventory")
async def get_inventory():
    """Retrieve the latest asset inventory snapshot."""
    files = sorted([
        f for f in os.listdir(INVENTORY_DIR)
        if f.startswith("inventory_") and f.endswith(".json")
    ])
    
    if not files:
        return {}
        
    latest_file = os.path.join(INVENTORY_DIR, files[-1])
    try:
        with open(latest_file, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading inventory: {exc}")

@app.get("/alerts")
async def get_alerts():
    """Retrieve the cumulative triage alerts log."""
    if not os.path.exists(TRIAGE_LOG):
        return []
    try:
        with open(TRIAGE_LOG, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading alerts: {exc}")

@app.get("/pending")
async def get_pending_actions():
    """Retrieve drafted containment actions awaiting approval."""
    if not os.path.exists(PENDING_ACTIONS):
        return []
    try:
        with open(PENDING_ACTIONS, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading pending actions: {exc}")

@app.post("/approve/{action_id}")
async def approve_action(action_id: str):
    """Approve and execute a containment action (Human Approval Gate)."""
    responder = ResponderAgent()
    success = responder.approve_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Action ID {action_id} not found or already approved.")
    
    return {"status": "success", "message": f"Action {action_id} approved."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
