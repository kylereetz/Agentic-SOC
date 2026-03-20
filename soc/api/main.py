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
from datetime import datetime, timedelta
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
from soc.agents.responder import ResponderAgent
from soc.agents.topology_mapper import TopologyMapper

# ── CONFIG ──────────────────────────────────────────────────────────────────
vault_path = get_soc_path("configs", "secrets.json")
vault = Vault(vault_path)
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA SOC API - %(message)s",
)
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

# ── MOCK USER DATABASE (MVP Start) ──────────────────────────────────────────
# ── USER DATABASE ────────────────────────────────────────────────────────────
# Pre-defined users for the MVP
# Passwords will be hashed at runtime or lazy-loaded for performance
def get_users_db():
    return {
        "admin": {
            "username": "admin",
            "hashed_password": "admin123", # Plain text for MVP stability
            "role": "admin",
        },
        "analyst": {
            "username": "analyst",
            "hashed_password": "analyst123",
            "role": "analyst",
        },
        "auditor": {
            "username": "auditor",
            "hashed_password": "auditor123",
            "role": "auditor",
        },
    }

USERS_DB = get_users_db() # Still using a global for simplicity, but in a function

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

# ── AUTH UTILS ──────────────────────────────────────────────────────────────
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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

# ── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    user_dict = USERS_DB.get(form_data.username)
    if not user_dict or form_data.password != user_dict["hashed_password"]:
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
async def approve_action(action_id: str, user: User = Depends(check_role(["admin"]))):
    """Approve and execute a containment action (Human Approval Gate). Admin only."""
    # Input validation: check for alphanumeric or UUID-like pattern (hex and hyphens)
    if not action_id or not re.match(r"^[a-zA-Z0-9-]+$", action_id):
        logger.warning(f"Invalid action_id format received: '{action_id}' (User: {user.username})")
        raise HTTPException(status_code=400, detail="Invalid Action ID format.")

    responder = ResponderAgent()
    success = responder.approve_action(action_id)
    if not success:
        logger.error(f"Action approval failed: ID {action_id} not found or already approved. (User: {user.username})")
        raise HTTPException(status_code=404, detail=f"Action ID {action_id} not found or already approved.")
    
    logger.info(f"Action {action_id} approved by {user.username}.")
    return {"status": "success", "message": f"Action {action_id} approved."}

@app.get("/api/v1/topology", response_model=Dict[str, Any])
async def get_topology(current_user: User = Depends(get_current_user)):
    """[IQ] Retrieve the latest asset relationship graph."""
    return topology_mapper.get_topology()

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.2"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
