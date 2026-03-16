# Agentic SOC — Performance Audit Report

## 📊 Scorecard Summary

| Pillar | Agent | IQ | EQ | SQ | VQ | Overall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Ops** | [Scout](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/scout.py#143-288) | 6 | 7 | 5 | 8 | **6.5** |
| **Ops** | [Auditor](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/auditor.py#115-369) | 4 | 8 | 7 | 5 | **6.0** |
| **Ops** | [PatchPilot](file:///C:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/patch_pilot.py#253-438) | 5 | 9 | 7 | 6 | **6.8** |
| **Intel** | [Triage](file:///C:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/triage.py#211-299) | 5 | 8 | 7 | 9 | **7.3** |
| **Intel** | [Orchestrator](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#25-103) | 8 | 7 | 8 | 9 | **8.0** |
| **Intel** | [Investigator](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#328-628)| 9 | 7 | 8 | 9 | **8.3** |
| **Action**| [Forensics](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/forensics.py#43-118) | 4 | 9 | 8 | 8 | **7.3** |
| **Action**| [Responder](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/responder.py#36-171) | 6 | 9 | 8 | 7 | **7.5** |
| **Base** | [Manager](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#77-212) | 6 | 9 | 8 | 9 | **8.0** |

---

## 🔍 Critical Gaps & "Rails Risks"

### 1. The "Single Thread" Bottleneck (SQ Risk)
[ScoutAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/scout.py#143-288) uses a synchronous `while True` loop that blocks. In a scaled deployment, if a scan hangs, the entire service dies. 
**Action**: Move Scout to an async provider or a separate process handled by the Orchestrator.

### 2. The "Vacuum" Problem (IQ Risk)
Investigator agents are brilliant but "amnesiac." They don't remember if `192.168.1.105` was seen in a similar case last month.
**Action**: Implement a **LibrarianAgent** (RAG/Memory).

---

## 🏗️ New Agent Proposals (The Missing Pillars)

During the audit, I identified three functional areas where logic is either missing or "orphaned" in the wrong place:

### 1. `SENTINEL-LIBRARIAN` (Memory/RAG) 
- **Purpose**: Manage long-term case memory. 
- **Function**: Indexes every completed [CaseRecord](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#46-73) and provides a `query_past_incidents` tool to the Investigators.
- **Why**: Prevents reinventing the wheel on recurring alerts.

### 2. `SENTINEL-DISPATCH` (Communication)
- **Purpose**: Human-in-the-loop bridge.
- **Function**: Listens for `PENDING_APPROVAL` actions and notifies admins via Slack, Email, or Webhook.
- **Why**: Currently, a human must check the dashboard manually to see an action.

### 3. `SENTINEL-CORRELATOR` (Stateful Analysis)
- **Purpose**: Anti-noise and pattern detection.
- **Function**: Aggregates low-severity alerts over time (e.g., 50 "Failed Logins" in 10 mins) to produce a single `CRITICAL` alert.
- **Why**: Reduces alert fatigue for the Triage agent.

---

## 🛠️ Hardening Roadmap (Phase 6)
1. **Hardening**: Convert [ScoutAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/scout.py#143-288) to async-compatible polling.
2. **Expansion**: Build the `LibrarianAgent` to raise general IQ to 9+.
3. **Integration**: Wire the [Responder](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/responder.py#36-171) directly to the `DispatchAgent`.
