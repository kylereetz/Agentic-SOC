# Agentic SOC Dashboard: Simulated Features Audit

Following an inspection of the React frontend source code (`dashboard/src/components`), the following components and views contain simulated data, mock functions, or UI-only representations that do not yet perfectly mirror the active Python backend. They use hardcoded arrays or `setInterval` ticking functions to simulate real-time API integrations.

---

## 1. Investigation Canvas & Incident Management
- **`InvestigationCanvas.jsx`**: Uses a hardcoded `INCIDENTS` array ("INC-2023-981", "INC-2023-992") to populate the active incident list instead of querying the `/cases` API endpoint.
- **`EntityGraph.jsx`**: Periodically polls `fetchTopology()` using a `setInterval` but visualizes static sample entities alongside the live topology.
- **`HypothesisPanel.jsx`**: Uses `setInterval` to simulate the "AI reasoning" typewriter effect and populates the panel with a hardcoded `HYPOTHESES` array.

## 2. Agent Monitoring & Hive Health
- **`HiveHealth.jsx`**: Relies on hardcoded arrays like `FLEET_METRICS` and `AGENT_CAPABILITIES`. Uses `setInterval` to simulate active agent heartbeat ticks on the GUI.
- **`AgentFleetMonitor.jsx`**: "Simulate tool count ticking for active agents" artificially increments the tools used counter.
- **`AgentDetailDrawer.jsx`**: Uses a mock `setInterval(fetchTelemetry, 5000)` to simulate Server-Sent Events (SSE) and live log streaming for individual agents.

## 3. Threat Telemetry (Intel)
- **`ThreatTelemetry.jsx`**: Heavily backed by a `// ── Mock Data ──` block. The `INTEL_FEEDS`, standard `THREAT_ACTOR_PROFILES` (e.g. APT-29, Lazarus), and global coordinate map markers are statically hardcoded rather than ingested from external MISP or STIX feeds.

## 4. Analytics & Governance
- **`AnalyticsDashboard.jsx`**: All charts (Recharts) are populated with static constants: `AUTONOMY_DATA`, `FP_DATA`, `AGENT_PERF`, `DURATION_DATA`, and `PIE_DATA`.
- **`GovernanceDashboard.jsx`**: The compliance heatmaps and tables run off hardcoded `COMPLIANCE_SCORES`, `NIST_CONTROLS`, and `RECENT_AUDITS` arrays instead of dynamic Python NIST output.

## 5. Adversary Simulation & Scenarios
- **`SimulationMode.jsx` / `CyberRange.jsx`**: These components represent an entirely simulated "cyber range". They use `setInterval` to push fake "live attack events" from `SIMULATION_SCENARIOS` to the UI to demonstrate agent response capabilities without requiring real network attacks.
- **`BlastRadiusSimulator.jsx`**: A purely frontend tool that graphs static nodes to demonstrate how a compromise might spread—no real mathematical blast-radius calculation is being performed on the backend topology.

## 6. Audit & Discovery Launchpad
- **`AuditDiscoveryLaunchpad.jsx`**: Even though the SOC has a real `Scout` agent, this dashboard component uses `setInterval` to push "mock inventory updates" to the screen incrementally, rather than streaming the true NMAP/ARP discovery results via a WebSocket.

---
**Note:** These mocked datasets perfectly demonstrate the *vision* of the Agentic SOC. Replacing them with true backend FastAPI `/api/v1/...` integrations is the final step to bridging the complete end-to-end autonomous architecture.
