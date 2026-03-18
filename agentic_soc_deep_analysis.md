# Agentic SOC: Technical Architecture & Competitive Analysis

## Executive Summary
**Sentinel Agentic SOC** is a next-generation security operations platform designed to solve the "Speed vs. Noise" dilemma in modern cybersecurity. Its primary mission is to transition the SOC from a human-heavy, reactive model to an autonomous, **"Digital Hive Mind"** capable of handling the entire incident lifecycle—from multi-protocol ingestion to forensic investigation and remediation.

Based on the [agent_manifest.md](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/agent_manifest.md), the system solves for high-fidelity detection by employing 24 specialized agents that collaborate using a multi-agent consensus model. It specifically addresses the needs of **IT/OT convergence**, providing deep visibility into industrial protocols (Modbus) while maintaining a strict NIST 800-171 and CMMC 2.0 compliance posture.

---

## Architectural Mapping (How the Pieces Fit Together)

The platform is organized into a 4-Pillar strategic framework, as detailed in [agentic_siem_ecosystem.md](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/agentic_siem_ecosystem.md).

### 1. Core Modules & Agents
*   **The Brain**: [SENTINEL-MANAGER](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py) ([InvestigationManager](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#87-365)) tracks the case lifecycle (TRIAGE -> SCOPING -> REMEDIATION -> CLOSED) and maintains long-term state in a **SQLite WAL**-backed database.
*   **The Heart**: [SENTINEL-ORCHESTRATOR](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py) ([OrchestratorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#25-165)) acts as a high-level dispatcher, selecting specialists via `get_specialist_for_alert` and managing async multi-agent execution.
*   **The Specialists**: A roster of 24 agents including [InvestigatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#392-721) (LLM-backed reasoning), `ForensicsAgent` (evidence collection), [TriageAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/triage.py#302-436) (noise reduction), and `MirageAgent` (deception/honeypots).

### 2. Data Flow & Orchestration
1.  **Ingestion**: [ScoutAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/scout.py) and [TrafficSieveAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/traffic_sieve.py) push raw telemetry to the [EventBus](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/bus/event_queue.py).
2.  **Triage**: [TriageAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/triage.py#302-436) applies a deterministic rule engine. It uses **"Intel Scouter"** to boost severity for known bad actors and **"Temporal Correlation"** to upgrade persistent warnings to CRITICAL attacks.
3.  **Active Investigation**: The [Orchestrator](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#25-165) dispatches specialists. The [InvestigatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#392-721) runs a **ReAct loop** (Reason → Act → Observe) via Gemini 1.5 Pro, accessing tools like [query_siem](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#146-157) and [collect_forensics](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#229-238).
4.  **Collective Memory**: Agents share findings via [SENTINEL-LIBRARIAN](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/librarian.py) (`LibrarianAgent`), a RAG service that allows specialists to "remember" historical case data.
5.  **Remediation**: [ResponderAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/responder.py) polls the `patch_manifests` channel. Actions are staged as `PENDING_APPROVAL`, requiring a human-in-the-loop to confirm containment via the [approve](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/main.py#425-434) CLI command in [main.py](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/main.py).

### 3. Communication Layer
The [EventBus](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/bus/event_queue.py) implementation is a standout architectural choice. It is a file-backed system that provides:
- **Encryption-at-Rest**: Using AES-256 (Fernet).
- **Message Integrity**: Cryptographic signing via HMAC-SHA256.
- **Asynchrony**: Python `asyncio` handles non-blocking polling across all agents.

---

## The "Top-Notch" Factor (Competitive Analysis)

### 1. Multi-Agent Consensus Logic
Unlike standard SOAR tools that follow linear playbooks, the [OrchestratorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#25-165) implements **Multi-Agent Consensus** ([orchestrator.py:78-85](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#L78-85)). For CRITICAL alerts, it runs multiple specialists in parallel (e.g., Malware Pathologist + Threat Hunter) to validate findings before recommending isolation.

### 2. ReAct reasoning & Autonomy Tracking
The [InvestigatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#392-721) doesn't just return a score; it publishes a full **Reasoning Chain** ([investigator.py:114-130](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#L114-130)).
- **Explainability**: Each step has a [reasoning](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#294-325) field for forensic transparency.
- **Drift Detection**: The [InvestigationManager](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#87-365) tracks **"Autonomy Drift"** ([investigation_manager.py:314-318](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#L314-318)), measuring the AI's deviation from established security guardrails.

### 3. IT/OT Convergence Expertise
The platform includes built-in specialist logic for industrial environments. [InvestigatorTools](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#139-329) includes [inspect_modbus_traffic](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#240-249), allowing the AI to reason about PLC function codes and emergency shutdown overrides—a rarity in traditional SOC tools.

### 4. High-Fidelity Infrastructure Resilience
The use of **SQLite WAL (Write-Ahead-Log)** and a separate [case_transactions.wal](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#45) ensures that even if the process crashes mid-investigation, no forensic evidence is lost.

---

## Gap Analysis (Path to Enterprise-Ready)

1.  **Distributed Communication**: The current [EventBus](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/bus/event_queue.py#42-192) is file-backed. While excellent for low-latency local execution, an enterprise SOC spanning multiple regions would require a transition to a distributed message broker like **NATS** or **Redis**.
2.  **Centralized Secrets Management**: Security keys (`SOC_BUS_KEY`) are managed via environment variables. An enterprise deployment should integrate with a **Secret Vault** (HashiCorp Vault or AWS Secrets Manager).
3.  **Granular Remediation Approval**: The current approval model is binary (Approve/Reject full ID). Implementing **Step-by-Step Remediation Approval** for complex multi-host containment plans would reduce operational risk.
4.  **Agent-on-Agent Auditing**: While [WatchdogAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/watchdog.py) monitors system health, adding a "Red Team" agent to intentionally inject false anomalies would allow the system to continuously audit its own detection accuracy.

---

> [!NOTE]
> This analysis is based on the **Maturity Hardening 10/10** phase of the repository. The inclusion of [final_hive_audit.py](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/final_hive_audit.py) demonstrates a high level of engineering maturity, treating the AI "hive" as a system that requires constant automated benchmarking.
