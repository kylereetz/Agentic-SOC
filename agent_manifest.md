# Sentinel Agentic SOC: Agent Manifest

This manifest documents the architectural specifications, roles, and specialized operational capabilities for each agent in the **Sentinel Agentic SOC digital hive mind**.

All agents operate under a 4-Pillar strategic architecture plus a Core Orchestration layer, communicating asynchronously via encrypted event queues.

---

## Core Orchestration Layer (The Brain)

### 1. SYRINX-MANAGER ([InvestigationManager](./backend/soc/agents/orchestration/investigation_manager.py))
**Role**: The central case lifecycle manager and primary state engine.
* **Intelligence Quotient (IQ)**: Hypothesis Generator — auto-populates case hypotheses based on correlated findings.
* **Emotional Quotient (EQ)**: Write-Ahead Logging (WAL) for case persistence; SQLite/PostgreSQL transition for 10k+ event scalability.
* **Social Quotient (SQ)**: Asynchronous sync barriers to prevent vector RAG race conditions.
* **Cognitive Quotient (CQ)**: Crypto-Agile Service Mesh enforcement — mathematically mandates Quantum-Resistant X25519 ciphers for all mTLS service mesh connections.
* **Vigilance Quotient (VQ)**: Real-time WebSocket state updates for global investigation tracking.

### 2. SYRINX-ORCHESTRATOR ([Orchestrator](./backend/soc/agents/orchestration/orchestrator.py))
**Role**: High-level task dispatcher and multi-agent coordinator.
* **IQ**: Dynamic routing of incoming security alerts to the appropriate specialist agent.
* **EQ**: Maintains global state consistency across the agent hierarchy.
* **SQ**: Priority lane queuing — separates life-safety OT/ICS alerts from lower-priority IT hygiene tasks.
* **VQ**: Dispatch telemetry exposed to the operator dashboard for real-time agent load visibility.

---

## Operations Pillar (Surveillance & Ingestion)

### 3. GAGGLE-SCOUT ([ScoutAgent](./backend/soc/agents/operations/scout.py))
**Role**: Asset discovery and inventory management.
* **IQ**: Agentless discovery of IT/OT assets, proactive tracking of Shadow IT, unpatched legacy hardware, and default PLC credentials.
* **EQ**: Inventory diffing to detect unauthorized infrastructure changes and unpatched endpoints.
* **SQ**: Scheduled passive sweep cycles with configurable cadence; emits delta events on change detection.
* **VQ**: Live asset count and shadow IT posture summaries surfaced on the operator health panel.

### 4. GAGGLE-TOPOLOGY ([TopologyMapper](./backend/soc/agents/operations/topology_mapper.py))
**Role**: Asset relationship graph maintenance.
* **IQ**: Dynamic relationship graphing — tracks User -> Host, Host -> IP, and Host -> Service mappings.
* **EQ**: Continuous integration — synthesizes events from discovery, identity, and network telemetry buses.
* **VQ**: Renders asset relationship graphs in ReactFlow compatible format for investigation context.

### 5. GAGGLE-LOG-GUARDIAN ([LogGuardianAgent](./backend/soc/agents/operations/log_guardian.py))
**Role**: Deterministic log normalization with LLM fallback.
* **IQ**: 90% Deterministic Parsing — normalizes broken logs using Grok, Regex, and Wazuh decoders.
* **EQ**: Reasoning Fallback — routes unknown proprietary OT log formats to the 8B Reasoning Head to prevent syntactic hallucinations.
* **SQ**: Async pipeline ingestion — publishes normalized events without blocking upstream collectors.
* **VQ**: Schema conformance rate surfaced as a live data quality metric on the operator dashboard.

### 6. GAGGLE-TRAFFIC-SIEVE ([TrafficSieveAgent](./backend/soc/agents/operations/traffic_sieve.py))
**Role**: Netflow analysis and exfiltration detection.
* **IQ**: Netflow Correlation — identifies anomalous data egress patterns (bytes, flags, ports).
* **EQ**: Volume Thresholding — flags high-volume data transfers to unknown destination IPs.
* **SQ**: Sliding-window stream processing — continuously evaluates flow records without full dataset replay.
* **VQ**: Exfiltration event map rendered with directional egress overlays.

### 7. GAGGLE-WATCHDOG ([WatchdogAgent](./backend/soc/agents/operations/watchdog.py))
**Role**: System health and heartbeat monitoring.
* **IQ**: Self-Healing Hive — monitors fellow agents for reasoning lag, downtime, or abnormal token burn rates.
* **EQ**: Performance Telemetry — tracks token consumption and execution latency across the fleet.
* **SQ**: Heartbeat polling at configurable intervals; issues manager restart directives on missed beats.
* **VQ**: Live health grid color-coded by status with token burn-rate sparklines.

---

## Intelligence Pillar (Cognitive Investigation)

### 8. QUILL-TRIAGE ([TriageAgent](./backend/soc/agents/intelligence/triage.py))
**Role**: Alert severity classification and noise suppression.
* **IQ**: Intel Scouter — escalates severity to CRITICAL for known threat campaign actors.
* **EQ**: Deterministic rule engine with auto-tuning noise suppression.
* **SQ**: Real-time subscription to intelligence buses for feedback ingestion.
* **VQ**: Maps every classified alert to NIST 800-171 controls and MITRE ATT&CK techniques.

### 9. QUILL-CORRELATOR ([CorrelatorAgent](./backend/soc/agents/intelligence/correlator.py))
**Role**: Temporal state manager and campaign detector.
* **IQ**: Stateful Attack Chain detection (Reconnaissance -> Lateral Movement -> Exfiltration).
* **EQ**: Rolling 48-hour temporal sliding window for multi-entity tracking.
* **SQ**: Hash Linkage — connects distributed entity states via malicious file hashes.
* **VQ**: Correlation strength scoring from 0.0 to 1.0.

### 10. QUILL-LIBRARIAN ([LibrarianAgent](./backend/soc/agents/intelligence/librarian.py))
**Role**: Shared Retrieval-Augmented Generation (RAG) memory service.
* **IQ**: Semantic vector search across historical case data and threat intel.
* **EQ**: Async Index Locking — prevents vector index corruption during simultaneous read/write operations.
* **SQ**: Priority polling (0.1s) for sub-second knowledge retrieval.
* **VQ**: Knowledge retention verification for every search query.

### 11. QUILL-HUNTER ([HunterAgent](./backend/soc/agents/intelligence/hunter.py))
**Role**: Proactive hypothesis-driven threat hunter.
* **IQ**: Ingests new threat intelligence (e.g., CISA alerts) and queries vector memory for historical matches.
* **EQ**: Pattern Backtracking — links current suspicious leads to past telemetry to uncover long-dwell threats.
* **SQ**: Deep integration with `QUILL-LIBRARIAN` for cross-case knowledge retrieval.
* **VQ**: Satisfies Level 3 CMMC "Advanced Threat Detection" enhanced controls.

### 12. QUILL-ENDPOINT-ANALYST ([EndpointAnalystAgent](./backend/soc/agents/intelligence/endpoint_analyst.py))
**Role**: Endpoint execution forensics and process monitoring.
* **IQ**: Sysmon / EDR Parsing — detects obfuscated command lines, DLL injections, and suspicious process chains.
* **EQ**: Heuristic Fallback — uses strict Event ID matching if LLM parsing confidence drops below threshold.
* **SQ**: Direct Triage Escalation — bypasses general queues for high-confidence execution detections.

### 13. QUILL-INVESTIGATOR ([InvestigatorAgent](./backend/soc/agents/intelligence/investigator.py))
**Role**: Deep root cause analyst.
* **IQ**: Chain-of-Thought (CoT) reasoning for complex threat patterns.
* **EQ**: Tool-use validation — prevents LLM hallucination in forensic analysis steps.
* **SQ**: Evidence synthesis across multiple specialist finding logs.
* **VQ**: Explainability Modal integration for dashboard visualization.

### 14. QUILL-FORENSICS ([ForensicsAgent](./backend/soc/agents/intelligence/forensics.py))
**Role**: Forensic evidence collection and chain of custody preservation.
* **IQ**: Pattern Matching — flags known shellcode headers in raw memory dumps.
* **EQ**: Integrity Seals — SHA-256 hashing of all evidence at exact point of collection.
* **SQ**: Paged artifact collection to avoid out-of-memory errors on large data dumps.
* **VQ**: Forensic Timeline View — renders chronological sub-history for every case.

### 15. QUILL-MALWARE-PATHOLOGIST ([MalwarePathologistAgent](./backend/soc/agents/intelligence/malware_pathologist.py))
**Role**: Binary analysis and sandbox behavior tracking.
* **IQ**: Sandbox Behavioral Tracking — tracks process creation, registry modifications, and network beaconing.
* **EQ**: Signature Correlation — links binary behavior to known APT toolkit signatures.
* **SQ**: Async artifact hand-off — streams analysis results directly to investigation agents without blocking.
* **VQ**: Renders behavioral reports as structured pathology cards in the Case Detail view.

### 16. QUILL-GATEKEEPER ([GatekeeperAgent](./backend/soc/agents/intelligence/gatekeeper.py))
**Role**: Identity governance and Zero Trust specialist.
* **IQ**: Detects MFA fatigue, impossible travel, and credential compromise.
* **EQ**: Non-Human Identity (NHI) Governance — rotates agent API keys and monitors machine credentials.
* **SQ**: Subscribes to identity event buses for sub-second ingestion from SSO and PAM telemetry feeds.
* **VQ**: Identity risk heatmaps surfaced per user/role with live Zero Trust posture scoring.

### 17. QUILL-VANGUARD ([VanguardAgent](./backend/soc/agents/intelligence/vanguard.py))
**Role**: Supply chain and vendor risk specialist.
* **IQ**: Ingests Software Bill of Materials (SBOMs) to instantly evaluate zero-day impacts on nested libraries.
* **EQ**: Monitors external communications for BEC patterns and vendor impersonation.
* **SQ**: Async SBOM diff pipeline — continuously reconciles current SBOM snapshots against new CVE feeds.
* **VQ**: Vendor risk scorecards rendered in the governance pane with dependency graph drill-downs.

### 18. QUILL-MIRAGE ([MirageAgent](./backend/soc/agents/intelligence/mirage.py))
**Role**: Deception operations and decoy management.
* **IQ**: Deploys and monitors lightweight honeypots (PLCs, CAD shares) and canary credentials.
* **EQ**: Silent Sentry — bypasses standard queues for sub-second deception hit escalation.
* **SQ**: Out-of-band event channel — publishes deception hits directly to `SYRINX-MANAGER`.
* **VQ**: Active decoy maps overlaid on network topology views with attacker dwell-time annotations.

---

## Action Pillar (Response & Remediation)

### 19. WEDGE-RESPONDER ([ResponderAgent](./backend/soc/agents/action/responder.py))
**Role**: Automated containment and active defense.
* **IQ**: Risk Scoring Logic — blocks containment actions that exceed asset criticality thresholds.
* **EQ**: Dead-Man Switch — auto-reverts host isolation if heartbeat with the manager is lost.
* **SQ**: Non-blocking dispatch via Celery task queue integration.
* **VQ**: Autonomy gauge with live drift tracking on every successful action.

### 20. WEDGE-PATCHADVISOR ([PatchAdvisor](./backend/soc/agents/action/patch_advisor.py))
**Role**: Advisory vulnerability remediation scripting.
* **IQ**: Context-aware script generation with dependency mapping — strictly bounded as an Advisor.
* **EQ**: Enforces the "Rule of Zero" safety protocol; **never** executes root or SYSTEM commands autonomously.
* **SQ**: Interfaces with triage queues to draft Bash and PowerShell mitigation scripts for human review.
* **VQ**: Patch status timeline displayed per asset alongside pending human validation gates.

---

## Business Pillar (Governance & Strategy)

### 21. FLYWAY-GOVERNOR ([GovernorAgent](./backend/soc/agents/business/governor.py))
**Role**: Unified governance and compliance cross-mapping.
* **IQ**: Compliance Cross-Mapping — maps detections directly to NIST 800-171 and CMMC 2.0 control domains.
* **EQ**: Triage Feedback Loop — parses success/failure ratios to autonomously tune upstream triage algorithms.
* **SQ**: Policy arbitration queue — serializes competing rule updates to prevent configuration race conditions.
* **VQ**: Compliance posture scorecards with per-domain control coverage visualized across NIST 800-171 and CMMC 2.0.

### 22. FLYWAY-COMMUNICATOR ([CommunicatorAgent](./backend/soc/agents/business/communicator.py))
**Role**: Unified executive and operational reporting.
* **IQ**: Single-Pass Synthesis — calculates financial downtime, generates executive summaries, and formats paging alerts in a single LLM pass.
* **EQ**: Alert Fatigue Filter — silently caches identical outcome hashes to throttle duplicate paging storms.
* **SQ**: Async multi-channel dispatch — concurrently pushes to email, Slack, and webhook endpoints without sequential blocking.
* **VQ**: Outbound report logs with delivery status, recipient acknowledgment, and suppression counts.

### 23. FLYWAY-HISTORIAN ([HistorianAgent](./backend/soc/agents/business/historian.py))
**Role**: Long-term dormancy and rare event tracking.
* **IQ**: Automatically extracts multi-entity formats (IP, User) from incoming telemetry.
* **EQ**: Eliminates temporal noise by ignoring active entities, specifically hunting "threshold of silence" awakenings.
* **SQ**: Ultra-lightweight WAL SQLite persistence for long-dwell entity state (30+ days).
* **VQ**: Case History & Temporal Intelligence view — renders entity dormancy timelines with re-activation markers.

### 24. FLYWAY-STRATEGIST ([FictitiousPlaySolver](./backend/soc/agents/business/game_theory_solver.py))
**Role**: Defensive resource allocation solver.
* **IQ**: Fictitious Play algorithm — calculates Mixed-Strategy Nash Equilibrium (MSNE) probabilities for zero-sum games.
* **EQ**: Efficient Solver — provides optimized defender strategies without heavy scientific dependencies.
* **SQ**: Resource Optimization — calculates optimal defensive asset allocation under scarcity bounds.
* **VQ**: Maps directly to CMMC Level 3 "Advanced Risk Assessment" requirements.
