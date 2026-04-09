# Sentinel Agentic SOC: Agent Manifest

## Core Orchestration

### 1. SYRINX-MANAGER ([InvestigationManager](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigation_manager.py#86-352))
**Role**: The "Brain" of the SOC. Orchestrates case lifecycles and agent assignments.
- **Intellegence Quotient (IQ)**: Hypothesis Generator — auto-populates case hypotheses based on findings.
- **Emotional Quotient (EQ)**: WAL (Write-Ahead-Log) for case persistence; SQLite/PostgreSQL transition for 10k+ scalability.
- **Social Quotient (SQ)**: Asynchronous Sync Barriers to prevent RAG race conditions.
- **Cognitive Quotient (CQ)**: Crypto-Agile Service Mesh enforcement — mathematically mandates Quantum-Resistant X25519 ciphers for all component mTLS connections.
- **Vigilance Quotient (VQ)**: Real-time WebSocket updates for global investigation state.

### 2. SYRINX-ORCHESTRATOR ([Orchestrator](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/orchestrator.py#25-165))
**Role**: High-level task dispatcher and multi-agent coordinator.
- **IQ**: Dynamic routing of alerts to the most relevant specialist.
- **EQ**: Global state consistency across the agent hierarchy.
- **SQ**: Priority lane queuing — separates life-safety OT alerts from lower-priority IT hygiene tasks.
- **VQ**: Dispatch telemetry exposed to the HiveHealth dashboard for real-time agent load visibility.

## Detection & Intelligence

### 3. QUILL-TRIAGE ([TriageAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/triage.py#302-436))
**Role**: IT Noise vs. OT Threat Classifier.
- **IQ**: Intel Scouter — boosts severity to CRITICAL for known campaign actors.
- **EQ**: Deterministic rule engine with auto-tuning/noise suppression.
- **SQ**: Subscription to `intel_bus` for real-time feedback ingestion.
- **VQ**: NIST 800-171/MITRE TTP mapping for every classified alert.

### 4. QUILL-CORRELATOR ([CorrelatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/correlator.py#70-177))
**Role**: Temporal state manager and campaign detector.
- **IQ**: Stateful Attack Chain detection (RECON -> LATERAL -> EXFIL).
- **EQ**: Rolling 48-hour temporal sliding window for entity tracking.
- **SQ**: Hash Linkage — connects distributed entity states via malicious file hashes.
- **VQ**: Correlation Strength scoring (0.0 - 1.0).

### 5. QUILL-LIBRARIAN ([LibrarianAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/librarian.py#35-154))
**Role**: Shared RAG (Retrieval-Augmented Generation) memory service.
- **IQ**: Semantic search across historical case data.
- **EQ**: Async Index Lock — prevents data corruption during simultaneous read/write.
- **SQ**: Priority polling (0.1s) for sub-second knowledge retrieval.
- **VQ**: Knowledge-Retained verification for every query.

### 6. QUILL-HUNTER ([HunterAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/hunter.py#36-148))
**Role**: Proactive Threat Hunter. Specialist in hypothesis-driven APT detection.
- **IQ**: Ingests new threat intel (e.g., CISA alerts) and automatically queries RAG memory for historical matches.
- **EQ**: Pattern Backtracking — Links current leads to past telemetry to find long-dwell threats.
- **SQ**: Deep integration with `QUILL-LIBRARIAN` for cross-case knowledge retrieval.
- **VQ**: Satisfies Level 3 CMMC "Advanced Threat Detection" enhanced controls.

### 7. GAGGLE-LOG-GUARDIAN ([LogGuardianAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/log_guardian.py#30-98))
**Role**: Deterministic log normalization with LLM Fallback.
- **IQ**: 90% Deterministic Parsing — normalizes broken logs using Grok, Regex, and Wazuh decoders.
- **EQ**: Reasoning Fallback — routes truly unknown proprietary OT formats to the 8B Reasoning Head to prevent syntactic hallucinations.
- **SQ**: Async pipeline ingestion — publishes normalized events to the `log_bus` without blocking upstream collectors.
- **VQ**: Schema conformance rate surfaced as a live data quality metric on the operator dashboard.

### 8. GAGGLE-TRAFFIC-SIEVE ([TrafficSieveAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/traffic_sieve.py#28-66))
**Role**: Netflow Analysis & Exfiltration Detection.
- **IQ**: Netflow Correlation — identifies anomalous data egress patterns (bytes/flags/ports).
- **EQ**: Volume Thresholding — flags high-volume transfers to unknown destination IPs.
- **SQ**: Sliding-window stream processing — continuously evaluates flow records without full dataset replay.
- **VQ**: Exfiltration event map rendered in the network topology view with directional egress overlays.

### 9. QUILL-ENDPOINT-ANALYST ([EndpointAnalystAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/endpoint_analyst.py))
**Role**: Endpoint Execution & Memory Forensics Monitoring.
- **IQ**: Sysmon / EDR Parsing — Detects obfuscated command lines, DLL injections, and suspicious process chains.
- **EQ**: Heuristic Fallback — Uses strict EID matching if LLM parsing confidence is low.
- **SQ**: Direct Triage Escalation — Bypasses discovery queues for high-confidence execution detections.

## Investigation & Engineering

### 10. QUILL-INVESTIGATOR ([InvestigatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/investigator.py#390-708))
**Role**: Deep analyst providing LLM-driven root cause analysis.
- **IQ**: Chain-of-Thought (CoT) reasoning for complex threat patterns.
- **EQ**: Tool-use validation (prevents LLM hallucination in forensic steps).
- **SQ**: Evidence synthesis across multiple specialist finding logs.
- **VQ**: Explainability Modal integration for dashboard visualization.

### 11. QUILL-FORENSICS ([ForensicsAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/forensics.py#46-211))
**Role**: Evidence collection and integrity preserving.
- **IQ**: Pattern Matching — flags known shellcode headers in raw memory dumps.
- **EQ**: Integrity Seals — SHA-256 hashing of all evidence at point of collection.
- **SQ**: Paged artifact collection to avoid OOM on large data dumps.
- **VQ**: Forensic Timeline view — chronological sub-history for every case.

### 12. QUILL-MALWARE-PATHOLOGIST ([MalwarePathologistAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/malware_pathologist.py#28-44))
**Role**: Advanced Binary Analysis.
- **IQ**: Sandbox Behavioral Tracking — process creation, registry modification, and network beaconing.
- **EQ**: Signature Correlation — links malware behavior to known APT group toolkits.
- **SQ**: Async artifact hand-off — streams analysis results directly to `QUILL-FORENSICS` and `QUILL-INVESTIGATOR` without blocking.
- **VQ**: Behavioral report rendered as a structured pathology card in the Case Detail view.


## Response & Operations

### 14. WEDGE-RESPONDER ([ResponderAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/responder.py#38-258))
**Role**: Automated containment and active defense.
- **IQ**: Risk Scoring Logic — blocks actions exceeding the asset's criticality threshold.
- **EQ**: Dead-Man Switch — auto-reverts isolation if heartbeat with Manager is lost.
- **SQ**: Non-blocking dispatch via Celery task queue integration.
- **VQ**: Autonomy Gauge — live drift animation on every successful action.

### 15. WEDGE-PATCHADVISOR ([PatchAdvisor](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/backend/soc/agents/patch_advisor.py))
**Role**: Advisory vulnerability remediation scripting via 8B Reasoning Head.
- **IQ**: Context-aware script generation with dependency mapping—strictly bounded as an Advisor.
- **EQ**: Enforces the "Rule of Zero" safety protocol; never executes roots/SYSTEM commands autonomously.
- **SQ**: Interfaces with `triage_alerts` to draft bash/PowerShell mitigation scripts for human review.
- **VQ**: Patch status timeline displayed per asset alongside pending human validations.

### 16. QUILL-GATEKEEPER ([GatekeeperAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/gatekeeper.py#49-160))
**Role**: Identity & Zero Trust Specialist. Guardian of machine and human IDs.
- **IQ**: Detects MFA fatigue, impossible travel, and lateral movement via compromised credentials.
- **EQ**: NHI (Non-Human Identity) Governance — rotates agent API keys.
- **SQ**: Subscribes to `identity_bus` for sub-second event ingestion from SSO and PAM telemetry feeds.
- **VQ**: Identity risk heatmap surfaced per user/role with live Zero Trust posture scoring.

### 17. QUILL-VANGUARD ([VanguardAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/vanguard.py#34-150))
**Role**: Supply Chain & Vendor Risk Specialist.
- **IQ**: Ingests SBOMs to instantly flag zero-day impacts on nested libraries (e.g., Log4Shell).
- **EQ**: Monitors external comms for BEC patterns and vendor impersonation.
- **SQ**: Async SBOM diff pipeline — continuously reconciles current SBOM snapshots against new CVE feeds.
- **VQ**: Vendor risk scorecard rendered in the governance pane with dependency graph drill-down.

### 18. QUILL-MIRAGE ([MirageAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/mirage.py#36-103))
**Role**: Deception & Decoy Operations Specialist.
- **IQ**: Deploys and monitors lightweight honeypots (PLCs, CAD shares) and "canary" credentials.
- **EQ**: Silent Sentry — bypasses queues for sub-second deception hit escalation.
- **SQ**: Out-of-band event channel — publishes deception hits directly to `SYRINX-MANAGER` without traversing the primary alert bus.
- **VQ**: Active decoy map overlaid on the network topology view with hit-count and attacker dwell-time annotations.

### 19. GAGGLE-SCOUT ([ScoutAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/scout.py#162-335))
**Role**: Asset discovery and inventory management.
- **IQ**: Agentless discovery of OT/ICS assets, proactive tracking of shadow IT, unpatched legacy systems, and identifying default PLC credentials.
- **EQ**: Inventory diffing to detect unauthorized changes (Shadow IT) and legacy, unpatched endpoints.
- **SQ**: Scheduled passive sweep cycles with configurable cadence; emits delta events to `discovery_bus` on change detection.
- **VQ**: Live asset count, shadow IT posture summary, and new-asset alerts rendered on the HiveHealth panel.

### 20. GAGGLE-TOPOLOGY ([TopologyMapper](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/topology_mapper.py))
**Role**: The Asset Relationship Graph.
- **IQ**: Dynamic Graphing — tracks User -> Host, Host -> IP, and Host -> Service mappings.
- **EQ**: Continuous Integration — synthesizes events from discovery, identity, and network telemetry buses.
- **VQ**: Visualizes relationships in a ReactFlow compatible format to aid investigation context.

## Business & Governance

### 21. FLYWAY-GOVERNOR ([GovernorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/governor.py))
**Role**: Unified Governance & Tuning.
- **IQ**: Compliance Cross-Mapping — maps detections directly to NIST 800-171/CMMC 2.0 domains.
- **EQ**: Triage Feedback Loop — parses success/failure ratios to autonomously tune upstream triage algorithms.
- **SQ**: Policy arbitration queue — serializes competing rule updates to prevent configuration race conditions.
- **VQ**: Compliance posture scorecard with per-domain control coverage visualized across NIST 800-171 and CMMC 2.0.

### 22. FLYWAY-COMMUNICATOR ([CommunicatorAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/communicator.py))
**Role**: Tri-Factor Unified Reporting.
- **IQ**: Single-Pass Synthesis — calculates financial downtime, creates executives summaries, and pushes analyst pages inside a single LLM execution to minimize API bloat.
- **EQ**: Alert Fatigue Filter — silently caches identical outcome hashes to throttle outbound duplicate paging storms.
- **SQ**: Async multi-channel dispatch — concurrently pushes to email, Slack, and webhook endpoints without sequential blocking.
- **VQ**: Outbound report log with delivery status, recipient acknowledgment, and dedup suppression count surfaced in the governance pane.

### 23. GAGGLE-WATCHDOG ([WatchdogAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/watchdog.py#24-60))
**Role**: Heartbeat-Monitor & System Health.
- **IQ**: Self-Healing Hive — monitors other agents for hallucinations, lag, or downtime.
- **EQ**: Performance Telemetry — tracks token usage and latency across the fleet.
- **SQ**: Heartbeat polling at configurable intervals; triggers `SYRINX-MANAGER` restart directives on missed beats.
- **VQ**: Live agent health grid on HiveHealth — color-coded by status with token budget burn-rate sparklines.

### 24. FLYWAY-HISTORIAN ([HistorianAgent](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/historian.py))
**Role**: The Long-Term Dormancy Tracker (Rare Event Model).
- **IQ**: Automatically extracts multi-entity formats (IP, User) from incoming telemetry.
- **EQ**: Eliminates temporal noise by ignoring active entities; specifically hunts "threshold of silence" awakenings.
- **SQ**: Ultra-lightweight WAL SQLite persistence for long-dwell entity state (30+ days).
- **VQ**: Case History & Temporal Intelligence view — renders entity dormancy timelines with re-activation event markers.

### 25. FLYWAY-STRATEGIST ([FictitiousPlaySolver](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/soc/agents/game_theory_solver.py))
**Role**: Defensive Resource Allocator (Game Theory Solver).
- **IQ**: Fictitious Play algorithm — calculates MSNE probabilities for Zero-Sum games.
- **EQ**: Efficient Solver — provides optimized defender strategies without Scipy or heavy dependencies.
- **SQ**: Resource Optimization — calculates optimal defensive asset allocation under scarcity.
- **VQ**: Mapping to CMMC Level 3 "Advanced Risk Assessment".
