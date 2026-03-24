# RCA Deployment Guide: Factory Rollout
**Version**: 1.0
**Role**: On-Site Support Engineer

## 1. Initial Site Survey
Before deployment, verify the **Onboarding Questionnaire** is complete.
- Confirm physical access to the server room or IDF cabinet.
- Verify availability of a 110v power outlet and an Ethernet drop on the target OT/IT VLAN.

## 2. Hardware Preparation
Deploy RCA on a hardened **NUC** or **Industrial Gateway**.
- **OS**: Windows 11 Pro or Rocky Linux 9.
- **Python**: 3.10+ installed.
- **Environment**: Clone the `Agentic SOC` repo and run `.venv/Scripts/activate`.

## 3. Deployment Sequence

## 3. Deployment Sequence

### 3.1 Bootstraping & Offline Model Sync
Load the pre-trained local LLM models and RAG data from the encrypted USB drive:
```powershell
python main.py sync-models D:\RCA_Models
python main.py bootstrap
```

### 3.2 Network Siting & Air-Gap Verification
1. Physically connect the appliance's `eth1` interface to the OT switch's SPAN (Mirror) port.
2. Ensure the appliance has **NO outbound gateway route** to the internet.
3. Update `soc/configs/scout_config.json` with the local IP subnets to monitor passively.

### 3.3 Connectivity Check
Verify the API is reachable securely over the Local LAN for the human approval gate:
```powershell
python main.py start api
```
Then navigate to `https://<appliance-local-ip>:8443/status` from an administrative jump-box to confirm Agent health.

### 3.4 First-Run Audit
Kick off the initial discovery:
```powershell
python main.py audit --audit-subnet 192.168.1.0/24
```
Verify assets are appearing in `python main.py list inventory`.

## 4. Handover to Client
- Demonstrate the `main.py approve` command for containment actions.
- Provide the client with their first **Gap Analysis PDF**.
- Set the `Scout` agent to a recurring schedule (e.g., every 6 hours).

---
**Deployment Checked By**: ____________________ Date: __________
