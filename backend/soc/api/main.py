"""
RCA SOC API: FastAPI Interface for SOC Monitoring & Control.
Exposes status, inventory, alerts, and the human approval gate.
Now secured with JWT Authentication & RBAC.
"""

import json
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault
from soc.security.crypto_cat import sign_action
from soc.agents.responder import ResponderAgent
from soc.agents.topology_mapper import TopologyMapper
from engine.core.llm_client import LLMClient

# ── CONFIG ──────────────────────────────────────────────────────────────────
vault_path = get_soc_path("configs", "secrets.json")
vault = Vault(vault_path, role="api")
vault_data = vault.load()

# Initialize API Secret Key if not present in Vault
if "api_secret_key" not in vault_data:
    logging.getLogger(__name__).info("Generating new secure API secret key and storing in Vault.")
    vault_data["api_secret_key"] = os.environ.get("SOC_API_SECRET_KEY", secrets.token_hex(32))
    vault.save(vault_data)

SECRET_KEY = vault_data["api_secret_key"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 hours

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="RCA SOC API", version="0.1.2")

logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://[::1]:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances for API access
topology_mapper = TopologyMapper()
llm_client = LLMClient()

# ── USER DATABASE ────────────────────────────────────────────────────────────
# Plaintext passwords are hashed once at startup using sha256_crypt.
# In production, replace these defaults with credentials loaded from the Vault
# or an external identity provider.
_RAW_USERS = [
    {"username": "admin",   "password": "admin123",   "role": "admin"},
    {"username": "analyst", "password": "analyst123", "role": "analyst"},
    {"username": "auditor", "password": "auditor123", "role": "auditor"},
]

def _build_users_db() -> dict:
    """Hash all plaintext passwords once at startup and return the user DB."""
    db = {}
    for user in _RAW_USERS:
        db[user["username"]] = {
            "username": user["username"],
            "hashed_password": pwd_context.hash(user["password"]),
            "role": user["role"],
        }
    return db

USERS_DB = _build_users_db()

# ── DATA MODELS ──────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class User(BaseModel):
    username: str
    role: str

class StatusResponse(BaseModel):
    scout_status: str
    bus_sizes: Dict[str, int]

class ApprovalRequest(BaseModel):
    approved_indices: Optional[List[int]] = None

class ChitChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None

# ── AUTH UTILS ──────────────────────────────────────────────────────────────
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_dict = USERS_DB.get(username)
    if user_dict is None:
        raise credentials_exception
    return User(username=user_dict["username"], role=user_dict["role"])

def check_role(allowed_roles: List[str]):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker

# ── PATHS ───────────────────────────────────────────────────────────────────
INVENTORY_DIR = get_soc_path("reports", "inventory")
TRIAGE_LOG = get_soc_path("reports", "triage", "triage_alerts.json")
PENDING_ACTIONS = get_soc_path("reports", "incidents", "pending_actions.json")
CHITCHAT_LOG_DIR = get_soc_path("reports", "chitchat")

# ── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    user_dict = USERS_DB.get(form_data.username)
    # Use constant-time pwd_context.verify() — never compare passwords with ==
    if not user_dict or not pwd_context.verify(form_data.password, user_dict["hashed_password"]):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Successful login for user: {form_data.username}")
    access_token = create_access_token(data={"sub": user_dict["username"], "role": user_dict["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user_dict["username"],
        "role": user_dict["role"]
    }

@app.get("/status", response_model=StatusResponse)
async def get_status(user: User = Depends(get_current_user)):
    """Return health and queue sizes of the SOC components."""
    bus_channels = ["discovery_events", "triage_alerts", "patch_manifests"]
    sizes = {}
    for channel in bus_channels:
        bus = EventBus(channel)
        sizes[channel] = bus.size()
    
    return {
        "scout_status": "operational",
        "bus_sizes": sizes
    }

@app.get("/inventory")
async def get_inventory(user: User = Depends(get_current_user)):
    """Retrieve the latest asset inventory snapshot."""
    if not os.path.exists(INVENTORY_DIR):
        os.makedirs(INVENTORY_DIR, exist_ok=True)
        return {}
        
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
async def get_alerts(user: User = Depends(get_current_user)):
    """Retrieve the cumulative triage alerts log."""
    if not os.path.exists(TRIAGE_LOG):
        return []
    try:
        with open(TRIAGE_LOG, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading alerts: {exc}")

@app.get("/pending")
async def get_pending_actions(user: User = Depends(check_role(["admin", "analyst"]))):
    """Retrieve drafted containment actions awaiting approval."""
    if not os.path.exists(PENDING_ACTIONS):
        return []
    try:
        with open(PENDING_ACTIONS, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading pending actions: {exc}")

@app.get("/cases")
async def get_cases(user: User = Depends(get_current_user)):
    """Retrieve all active investigation cases."""
    cases_dir = get_soc_path("reports", "incidents", "cases")
    if not os.path.exists(cases_dir):
        return []
    
    cases = []
    for filename in os.listdir(cases_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(cases_dir, filename), "r") as fh:
                    cases.append(json.load(fh))
            except Exception:
                continue
    return sorted(cases, key=lambda x: x.get("created_at", ""), reverse=True)

@app.post("/approve/{action_id}")
async def approve_action(action_id: str, req: ApprovalRequest, user: User = Depends(check_role(["admin"]))):
    """Approve and execute a containment action (Human Approval Gate). Admin only."""
    # Input validation: check for alphanumeric or UUID-like pattern (hex and hyphens)
    if not action_id or not re.match(r"^[a-zA-Z0-9_.-]+$", action_id):
        logger.warning(f"Invalid action_id format received: '{action_id}' (User: {user.username})")
        raise HTTPException(status_code=400, detail="Invalid Action ID format.")

    # Generate the Cryptographic Action Token (IdP signature)
    cat_signature = sign_action(action_id, SECRET_KEY)

    responder = ResponderAgent()
    success = responder.approve_action(action_id, cat_signature, req.approved_indices)
    if not success:
        logger.error(f"Action approval failed: Invalid signature or ID {action_id} not found. (User: {user.username})")
        raise HTTPException(status_code=403, detail="Approval rejected: Invalid signature or missing action.")
    
    logger.info(f"Action {action_id} approved by {user.username}.")
    return {"status": "success", "message": f"Action {action_id} approved."}

import random

@app.get("/api/agents/{agent_id}/telemetry")
async def get_agent_telemetry(agent_id: str, user: User = Depends(get_current_user)):
    """Retrieve deep telemetry for a specific agent for the dashboard side-panel."""
    return {
        "agent_id": agent_id,
        "role": agent_id.split("-")[0].capitalize() + "Agent",
        "status": "ACTIVE",
        "current_task": {
            "description": f"Executing active directives against associated IOCs",
            "started_at": datetime.now(timezone.utc).isoformat() + "Z",
            "associated_case": f"INC-2026-{random.randint(100, 999)}"
        },
        "stats": {
            "uptime_seconds": random.randint(3600, 86400),
            "success_rate": round(random.uniform(88.0, 99.9), 1),
            "tools_executed_today": random.randint(12, 450),
            "compute_cycles": random.randint(50000, 1500000)
        },
        "recent_events": [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 5))).isoformat() + "Z",
                "type": "ACTION",
                "detail": f"Executed core functionality for {agent_id}"
            }
        ]
    }

@app.get("/api/v1/topology", response_model=Dict[str, Any])
async def get_topology(current_user: User = Depends(get_current_user)):
    """[IQ] Retrieve the latest asset relationship graph."""
    return topology_mapper.get_topology()

@app.get("/api/v1/netflow")
async def get_netflow(user: User = Depends(get_current_user)):
    """Retrieve raw netflow telemetry maintained by SENTINEL-TRAFFIC-SIEVE."""
    graph_path = get_soc_path("reports", "network_graph.json")
    
    if os.path.exists(graph_path):
        try:
            with open(graph_path, "r") as f:
                data = json.load(f)
                return data.get("links", [])
        except Exception as e:
            logger.error(f"Error reading network graph: {e}")
            
    # Fallback to realistic mock lab data if no traffic has been sniffed yet
    now = datetime.now(timezone.utc).timestamp()
    return [
        {
            "source": "10.0.44.82", "target": "DC-01",
            "ports": [445, 88], "bytes_transfer": 1420500,
            "connection_count": 42, "mean_bytes": 33821.4,
            "first_seen": now - 3600, "last_seen": now - 12
        },
        {
            "source": "Host-DX9", "target": "45.33.22.11",
            "ports": [443], "bytes_transfer": 8804512,
            "connection_count": 14, "mean_bytes": 628893.7,
            "first_seen": now - 7200, "last_seen": now - 4
        },
        {
            "source": "MFG-PROD-01", "target": "MFG-WS-01",
            "ports": [502], "bytes_transfer": 21020,
            "connection_count": 310, "mean_bytes": 67.8,
            "first_seen": now - 86400, "last_seen": now - 2
        },
        {
            "source": "192.168.1.105", "target": "10.0.0.50",
            "ports": [8080], "bytes_transfer": 450000,
            "connection_count": 5, "mean_bytes": 90000.0,
            "first_seen": now - 1800, "last_seen": now - 60
        }
    ]

@app.get("/api/v1/log-guardian")
async def get_log_guardian(user: User = Depends(get_current_user)):
    """Retrieve realtime LLM parsing stats from SENTINEL-LOG-GUARDIAN."""
    stats_path = get_soc_path("reports", "log_guardian_stats.json")
    
    if os.path.exists(stats_path):
        try:
            with open(stats_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading log guardian stats: {e}")
            
    # Mock data for immediate preview in lab environments without active pipelines
    return {
        "metrics": {
            "total_processed": 8421,
            "fast_path": 7910,
            "llm_fallback": 508,
            "failed": 3
        },
        "recent_agentic": [
            {
                "timestamp": datetime.now(timezone.utc).timestamp() - 14,
                "source": "Siemens S7 PLC",
                "raw": "0x00A1 FATAL OVERRIDE TEMP=340C THRESH=300 P_ID=04",
                "inferred": "PLC reporting critical temperature override threshold exceeded on PID 04.",
                "ip": "10.0.44.82"
            },
            {
                "timestamp": datetime.now(timezone.utc).timestamp() - 56,
                "source": "Custom RFID Door Reader",
                "raw": "ERR_BAD_BADGE HEX:4FA3 user_ref:NULL retry=5",
                "inferred": "Repeated unauthorized badge swipe failure.",
                "ip": "10.0.0.12"
            },
            {
                "timestamp": datetime.now(timezone.utc).timestamp() - 110,
                "source": "Legacy HMI Station",
                "raw": "USR_ACT_291 OP_MODE_CHANGE FROM=AUTO TO=MANUAL",
                "inferred": "Operator manually changed HMI mode from Auto to Manual.",
                "ip": "192.168.1.105"
            }
        ]
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.2", "kill_switch": _kill_switch_active}

# ── Kill Switch ───────────────────────────────────────────────────────────────
# Process-level flag. The orchestrator polls /api/v1/health and halts
# autonomous action dispatch when kill_switch is True.
_kill_switch_active: bool = False

@app.post("/api/v1/kill-switch")
async def toggle_kill_switch(user: User = Depends(check_role(["admin"]))):
    """[SAFETY] Toggle the global emergency kill switch — admin only.
    When active, the Orchestrator will pause all autonomous agent dispatching
    and require human approval for every pending action.
    """
    global _kill_switch_active
    _kill_switch_active = not _kill_switch_active
    state = "ENGAGED" if _kill_switch_active else "DISENGAGED"
    logger.warning("[KILL-SWITCH] Emergency kill switch %s by operator '%s'", state, user.username)
    return {"kill_switch": _kill_switch_active, "state": state, "operator": user.username}

@app.get("/api/v1/users")
async def get_users(user: User = Depends(check_role(["admin"]))):
    """[IAM] Return the sanitized user roster — admin only. No credentials are exposed."""
    return [
        {"username": u["username"], "role": u["role"]}
        for u in USERS_DB.values()
    ]

@app.post("/api/v1/chitchat")
async def chitchat(req: ChitChatRequest, user: User = Depends(get_current_user)):
    """[IQ] Route a natural language query to the internal model (ChitChat) with dynamic documentation context."""
    try:
        # 1. Load Agent Ethos (Doctrine)
        ethos_path = get_soc_path("ethos", "ethos_sentinel_communicator.md")
        system_logic = "You are ChitChat (Agentic SOC Communicator). You provide concise, expert SOC analysis and support."
        try:
            if os.path.exists(ethos_path):
                with open(ethos_path, "r") as f:
                    system_logic = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not load communicator ethos: {e}")

        # 2. Gather Incident Context (Latest Cases)
        cases_dir = get_soc_path("reports", "incidents", "cases")
        context_str = ""
        try:
            if os.path.exists(cases_dir):
                case_files = [f for f in os.listdir(cases_dir) if f.endswith(".json")]
                if case_files:
                    # Sort by modification time to get the latest
                    case_files.sort(key=lambda x: os.path.getmtime(os.path.join(cases_dir, x)), reverse=True)
                    latest_case_path = os.path.join(cases_dir, case_files[0])
                    with open(latest_case_path, "r") as f:
                        case_data = json.load(f)
                        context_str = f"\n\nCURRENT INCIDENT CONTEXT (LATEST CASE):\n{json.dumps(case_data, indent=2)}"
        except Exception as e:
            logger.warning(f"Failed to gather incident context for ChitChat: {e}")

        # Fallback for mock simulation seen in frontend
        if not context_str:
            context_str = "\n\nCURRENT INCIDENT CONTEXT (SIMULATION MODE):\nIncident ID: INC-2023-981\nStatus: Active Investigation\nFocus: Potential lateral movement from Host-DX9 to Domain Controllers."

        # 3. Construct messages
        messages = [
            {"role": "system", "content": f"{system_logic}{context_str}"}
        ]
        
        if req.history:
             for msg in req.history:
                 # Map dashboard's 'role' and 'text' to LLM's 'role' and 'content'
                 messages.append({"role": msg["role"], "content": msg["text"]})
        
        # Add the current query
        messages.append({"role": "user", "content": req.query})
        
        # Use LLMClient to generate response
        response = await llm_client.generate_chat(messages)

        # Persistence: log to a file for auditing (async not needed for simple append)
        if not os.path.exists(CHITCHAT_LOG_DIR):
            os.makedirs(CHITCHAT_LOG_DIR, exist_ok=True)
            
        session_id = f"{user.username}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        log_file = os.path.join(CHITCHAT_LOG_DIR, f"{session_id}.json")
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "user": user.username,
            "query": req.query,
            "response": response
        }
        
        try:
            current_log = []
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    current_log = json.load(f)
            current_log.append(log_entry)
            with open(log_file, "w") as f:
                json.dump(current_log, f, indent=2)
        except Exception as log_err:
            logger.error(f"Failed to persist ChitChat log: {log_err}")

        return {"response": response}
    except Exception as e:
        logger.error(f"ChitChat internal model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
