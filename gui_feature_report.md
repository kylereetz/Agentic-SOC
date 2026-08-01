# Agentic SOC GUI: Feature Breakdown Report

This report provides an exhaustive breakdown of all user interface components, views, and interactive controls across the **Branta Agent Dashboard** (v1.0 MVP).

The frontend is built with React, Vite, and Tailwind CSS, communicating with the backend API via REST and WebSocket event streams.

---

## 1. Global Navigation & Layout

* **Sidebar (Primary Navigation)**:
  * Collapsible/Expanded navigation states.
  * Direct workspace routing to Investigations, Alert Queue, Agents, Threat Intel, Governance, Analytics, and Simulation Mode.
* **Global Header Bar**:
  * **Operator Identity**: Displays active operator alias and access tier (Admin / Operator / Guest).
  * **Autonomy Indicator**: Real-time gauge of current autonomous action permissions.
  * **AI Copilot Toggle**: Floating interactive assistant drawer for query assistance.
  * **Session Controls**: Secure operator session termination.
* **System Dock**: Persistent bottom dock displaying global real-time event throughput and system health metrics.
* **Command Palette (`Cmd+K` / `Ctrl+K`)**: Keyboard-driven overlay for rapid search and action shortcuts.

---

## 2. Investigation Workspace ([InvestigationCanvas](./frontend/src/components/InvestigationCanvas.jsx))

The primary workspace for deep incident response, root cause analysis, and forensic timeline exploration.

* **Attack Chain Tab**:
  * **Interactive Intrusion Graph**: Renders the complete attack lifecycle using `ReactFlow` (Reconnaissance -> Lateral Movement -> Credential Access -> Persistence -> Exfiltration -> Command & Control).
  * **Campaign Indicator**: Real-time status badge for active threat campaigns.
* **Chain-of-Thought (CoT) Explorer Tab**:
  * **Reasoning Steps**: Chronological log of agent actions, findings, and confidence scores.
  * **MITRE ATT&CK Mapping**: Automatic tagging of reasoning steps with ATT&CK technique IDs (e.g., T1059.001).
  * **Agent Attribution**: Identifies specific agent attribution per reasoning step.
* **Human-in-the-Loop (HITL) Queue Tab**:
  * **Action Gating**: Interactive approval cards for high-risk containment actions (VLAN Isolation, Process Termination, Credential Rotation).
  * **Impact Assessment**: Contextual warning summaries detailing potential operational disruption before action approval.
  * **Role-Based Controls**: Authorize or reject pending agent requests with full audit logging.

---

## 3. High-Fidelity Alert Queue ([AlertQueue](./frontend/src/components/AlertQueue.jsx))

Centralized alert management and initial triage.

* **Triage Controls**:
  * **Global Search**: Filter alerts by Title, Target Asset, or Incident ID.
  * **Severity Filtering**: Filter by Critical, High, Medium, or Low severity tiers.
  * **Source Filtering**: Filter telemetry source (EDR, SIEM, IDS, Deception).
  * **Temporal Windows**: Quick filters for 1-hour, 6-hour, 24-hour, and 7-day windows.
* **Alert Feed**:
  * **Real-time Table**: Color-coded alert list with active pulse indicators for Critical priority items.
  * **Metadata Association**: Links alerts directly to related Assets, Agents, and MITRE ATT&CK codes.
* **Triage Actions**:
  * **Manual Assignment**: Reassign an alert to a specific specialist agent.
  * **Case Promotion**: Manually promote an alert into a full investigation case.

---

## 4. Digital Hive Mind Console ([HiveHealth](./frontend/src/components/HiveHealth.jsx))

Real-time monitoring and control panel for all 24 agents in the SOC fleet.

* **Health Dashboard**:
  * **Emergency Kill Switch**: Admin control to pause automated response agents.
  * **Performance Metrics**: Real-time execution latency, pending HITL queue depth, and LLM API cost rates.
* **Agent Fleet Matrix**:
  * **Pillar Filter**: Filter agents across Core, Operations, Intelligence, Action, and Business pillars.
  * **Agent Status Cards**: Live operational status (Online / Processing / Idle), resource utilization bars, and current active task description.
* **Telemetry & Cost Analytics**:
  * **Token Burn Chart**: Real-time area graph tracking LLM token burn versus cost over time.
  * **Autonomy Slider**: Dynamic control slider adjusting systemic autonomy limits (Manual -> Semi-Autonomous -> Full Autonomy).
* **Event Console**: Live WebSocket terminal streaming raw inter-agent communication logs.

---

## 5. Intelligence & Threat Telemetry ([ThreatTelemetry](./frontend/src/components/ThreatTelemetry.jsx))

Risk-quantified incident prioritization and deception monitoring.

* **Risk-Quantified Incident Queue**:
  * **Loss Magnitude Ranking**: Incidents prioritized by estimated financial exposure rate ($/hr).
  * **Likelihood Analysis**: Calculated probability score of threat progression.
  * **Exposure Gauge**: Aggregate business financial risk indicator per hour.
* **Deception Operations (`QUILL-MIRAGE`)**:
  * **Zero-False-Positive Alerts**: High-visibility alert banners for honeypot or canary credential interactions.
  * **Rapid Isolation**: One-click host isolation buttons upon verified deception triggers.

---

## 6. Governance & Compliance Panel ([GovernanceDashboard](./frontend/src/components/GovernanceDashboard.jsx))

Strategic compliance posture tracking and executive reporting.

* **Compliance Posture**:
  * **Maturity Gauges**: Radial progress tracking for NIST SP 800-171 and CMMC 2.0 readiness.
  * **Control Family Breakdown**: Detailed progress bars across all 14 NIST control families (Access Control, Audit & Accountability, Incident Response, etc.).
* **Auditor Log**:
  * **Continuous Compliance Stream**: Rolling audit log of automated control evaluations performed by `FLYWAY-GOVERNOR`.
* **Executive Summaries**:
  * **AI Narrative Summaries**: Human-readable weekly security posture summaries.
  * **Board Action Recommendations**: Strategic recommendations for resource allocation and risk mitigation.

---

## 7. Operational Analytics ([AnalyticsDashboard](./frontend/src/components/AnalyticsDashboard.jsx))

Performance analytics and system efficiency metrics.

* **KPI Scorecard**: Real-time tracking of Autonomy Ratio, False Positive Rate, Mitigation Success Rate, and Mean-Time-To-Investigate (MTTI).
* **Trend Analysis**:
  * **Autonomy Growth**: Line chart comparing automated AI actions versus manual human interventions over time.
  * **False Positive Reduction**: Visualization of triage accuracy improvement over time.
  * **Agent Efficiency**: Comparative analysis showing resolution rates per agent.

---

## 8. Cyber Range Simulation Mode ([SimulationMode](./frontend/src/components/SimulationMode.jsx))

Interactive sandbox for testing SOC agent responses against simulated attack vectors.

* **Scenario Engine**: Select pre-configured attack scenarios (APT-29 Spearphishing, Ransomware Egress, Insider Threat Credential Abuse).
* **Simulation Controls**: Play, pause, or reset attack simulations to observe multi-agent response flows in real time.
* **Efficiency Benchmarking**: Tracks automated actions taken per human intervention and calculates projected time saved.

---

## 9. Identity & Access Control ([LoginPage](./frontend/src/components/LoginPage.jsx))

* **Gatekeeper Authentication**: Operator authentication portal managed by `QUILL-GATEKEEPER`.
* **Tunnel Verification**: Visual confirmation of encrypted mTLS proxy tunnels.
* **Role-Based Access Control (RBAC)**: Enforces permission boundaries between Admin, Operator, and Auditor access tiers.
