# Agentic SOC GUI: Exhaustive Feature Report

This report provides a comprehensive breakdown of all features, tabs, and interactive elements across the **Aegis Agent** Dashboard (v1.0 MVP).

---

## 1. Global Navigation & Layout
*   **Sidebar (Primary Navigation)**:
    *   Collapsed/Expanded states.
    *   Direct navigation to: Investigations, Alert Queue, Agents, Threat Intel, Governance, Analytics, and Simulation Mode.
*   **Global Header**:
    *   **Operator Identity**: Displays Alias and Role (Admin/Guest).
    *   **Autonomy Indicator**: Real-time percentage of AI autonomy.
    *   **AI Copilot**: Floating interactive assistant toggle.
    *   **Global Exit**: Secure session termination.
*   **Bottom Dock**: Quick-access status bar for system-wide health (always visible).
*   **Command Palette (`Cmd+K`)**: Keyboard-driven navigation and action shortcut overlay.

---

## 2. Investigations ([InvestigationCanvas](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/InvestigationCanvas.jsx#188-297))
The primary workspace for deep forensic analysis.

*   **Attack Chain Tab**:
    *   **Interactive Graph**: Uses `ReactFlow` to visualize the intrusion lifecycle (Recon → Pivot → Credential → Persist → Exfil → C2).
    *   **Campaign Indicator**: Live status for active campaigns (e.g., "ALPHA-7 ACTIVE").
*   **CoT Explorer Tab (Chain-of-Thought)**:
    *   **Reasoning Steps**: Sequential log of agent actions, findings, and confidence scores.
    *   **MITRE Mapping**: Automatic tagging of steps with ATT&CK techniques (e.g., T1059.001).
    *   **Agent attribution**: Identifies which agent (Investigator, Malware Path., etc.) performed the action.
*   **HITL Queue Tab (Human-In-The-Loop)**:
    *   **Action Gating**: Interactive cards for actions requiring manual approval (VLAN Isolation, Process Kill, Account Disable).
    *   **Risk Assessment**: Contextual warnings about operational impact (e.g., "May disrupt 12 endpoints").
    *   **Admin Controls**: Approve/Reject buttons (Role-based access control enabled).

---

## 3. Alert Queue ([AlertQueue](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/AlertQueue.jsx#37-191))
High-fidelity alert management.

*   **Triage Controls**:
    *   **Global Search**: Filter by Title, Asset, or ID.
    *   **Severity Filters**: Critical, High, Medium, Low.
    *   **Source Filters**: EDR, SIEM, IDS, SOAR.
    *   **Temporal Filters**: 1h, 6h, 24h, 7d.
*   **Alert Table**:
    *   **Real-time Feed**: Color-coded alerts with pulse indicators for CRITICAL items.
    *   **Metadata**: Links alerts to Assets, Agents, and MITRE techniques.
*   **Alert Actions**:
    *   **Manual Assignment**: Assign a specific specialist agent.
    *   **Promotion**: Elevate an alert to a full Investigation Case.

---

## 4. Agents ([HiveHealth](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/HiveHealth.jsx#202-384))
The "Digital Hive Mind" management console.

*   **Health Dashboard**:
    *   **Global Kill Switch**: (Admin-only) Force-pause the `SENTINEL-RESPONDER` agent.
    *   **Health Metrics**: Real-time Avg Latency, HITL counts, and API Cost Rate ($/s).
*   **Agent Matrix**:
    *   **Pillar Filtering**: Filter the 24 agents by Core, Intel, Invest, Response, or Gov.
    *   **Agent Cards**: Displays status (Online/Idle/Pending), live CPU/Memory Load bars, and current micro-task (e.g., "Normalizing Palo Alto logs").
*   **Telemetry & Cost**:
    *   **Burn Chart**: Real-time area chart of LLM Token Burn vs. API Cost.
    *   **Autonomy Master Slider**: (Admin-only) Drag-and-drop adjustment of the system's autonomy level (Manual → Full-Auto).
*   **Orchestrator Event Stream**: Live WebSocket console showing raw agent-to-agent communication strings.

---

## 5. Threat Telemetry ([ThreatTelemetry](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/ThreatTelemetry.jsx#140-293))
Intelligence-led risk prioritization.

*   **Risk-Quantified Incident Queue**:
    *   **Loss Magnitude Ranking**: Incidents sorted by financial impact ($/hr).
    *   **Likelihood Analysis**: Percentage calculation of attack success.
    *   **Exposure Meter**: Global indicator of total business risk per hour.
*   **SENTINEL-MIRAGE DeceptionHits**:
    *   **Zero-False-Positive Alerts**: magenta-themed banners for honeytoken/honeypot interactions.
    *   **Immediate Isolation**: Bypass buttons to isolate source IPs instantly upon decoy hit.

---

## 6. Governance & Compliance ([GovernanceDashboard](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/GovernanceDashboard.jsx#157-288))
Strategic board-level reporting.

*   **Compliance Posture**:
    *   **Maturity Gauges**: Radial progress for NIST 800-171 and CMMC 2.0.
    *   **Control Family Breakdown**: Progress bars for all 14 NIST control families (AC, AU, IR, etc.).
*   **Auditor Feed**:
    *   **Continuous Compliance**: Rolling log of control passes/failures found by the Auditor agent.
*   **Executive Summary**:
    *   **NARRATOR-AI**: Human-readable summary of the week's security posture.
    *   **Board Actions**: Automated recommendations for resource allocation and isolation approvals.

---

## 7. Analytics ([AnalyticsDashboard](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/AnalyticsDashboard.jsx#58-168))
Operational performance metrics.

*   **KPI Scorecard**: Autonomy Ratio, FP Rate, Success Rate, and Mean-Time-To-Investigate.
*   **Trend Analysis**:
    *   **Autonomy Growth**: AI vs. Human action ratio over time.
    *   **FP Reduction**: Line chart tracking the "tuning" of the hive.
    *   **Agent Comparison**: Bar chart showing which specialist agents are most successful.

---

## 8. Simulation Mode ([SimulationMode](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/SimulationMode.jsx#15-117))
The cyber-range sandbox.

*   **Scenario Engine**: Select between APT-29, Ransomware, or Insider Threat scenarios.
*   **Run/Pause Controls**: Start/Stop the simulation to see how the hive responds.
*   **Efficiency Metrics**: Counts of AI actions taken per human intervention and projected automation savings.

---

## 9. Identity & Access ([LoginPage](file:///c:/Users/kyler/Documents/GitHub/Agentic%20SOC/dashboard/src/components/LoginPage.jsx#5-117))
*   **SENTINEL-GATEKEEPER Auth**: Secure entry point for operators.
*   **MFA Proxy Status**: Visual confirmation of encrypted tunnel establishment.
*   **Role Identification**: Categorizes access into Admin vs. Guest paths.
