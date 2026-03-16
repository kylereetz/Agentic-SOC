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

### 3.1 Bootstraping
Initialize the local environment:
```powershell
python main.py bootstrap
```

### 3.2 Configuration
Update `soc/configs/scout_config.json` with the client's subnet ranges obtained during onboarding.

### 3.3 Connectivity Check
Verify the API is reachable locally for the human approval gate:
```powershell
python main.py start api
```
Then navigate to `http://localhost:8000/status` to confirm agent health.

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
