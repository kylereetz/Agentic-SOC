# The Agentic SIEM Ecosystem: An Exhaustive Map

In a top-tier Agentic SIEM, the "Orchestrator" doesn't just manage one or two agents; it coordinates a **digital hive mind**. Each agent is a narrow specialist with its own LLM prompt engineering, local tools (CLI, API, Sandbox), and stateful memory.

Below is the exhaustive list of specialized agents categorized by our 4-Pillar strategic framework, plus the Core Orchestration layer.

---

## 0. The Orchestration Layer (The Brain)
*These core agents manage the entire investigation lifecycle and task dispatch.*

| Agent Name | Specialization | Key Capability |
| :--- | :--- | :--- |
| **SENTINEL-MANAGER** | Case Lifecycle | Orchestrates case lifecycles, Zero-Trust Crypto-Agility, and agent assignments via a SQLite/WAL engine. |
| **SENTINEL-ORCHESTRATOR** | Task Dispatcher | High-level dispatcher and multi-agent coordinator for specialized tasking. |

---

## 1. The Operations Pillar (Surveillance & Ingestion)
*These agents ensure high-fidelity data flow and immediate visibility.*

| Agent Name | Specialization | Key Capability |
| :--- | :--- | :--- |
| **SENTINEL-SCOUT** | Asset Discovery | Performs agentless discovery, diffing, and Post-Quantum Cryptography (PQC) Vulnerability Tracking for IT/OT assets. |
| **SENTINEL-TOPOLOGY** | Network Mapping | Maintains an active relationship graph mapping Users to Hosts to Services. |
| **SENTINEL-LOG-GUARDIAN** | Normalization | Fixes "broken" logs from legacy systems using NLP-guided schemas. |
| **SENTINEL-TRAFFIC-SIEVE** | Netflow Analysis | Identifies anomalous data exfiltration patterns in netflow/PCAPs. |
| **SENTINEL-WATCHDOG** | System Health | Monitors the hive for "hallucinations," performance lag, or downtime. |

---

## 2. The Intelligence Pillar (Cognitive Investigation)
*These agents perform deep analysis to separate noise from threats.*

| Agent Name | Specialization | Key Capability |
| :--- | :--- | :--- |
| **SENTINEL-TRIAGE** | Alert Classifier | Noise vs. Threat classifier using deterministic rules and MITRE mapping. |
| **SENTINEL-CORRELATOR** | Temporal Linking | Links distributed entity states across 48-hour windows to detect campaigns. |
| **SENTINEL-LIBRARIAN** | Institutional Memory | Shared RAG service for semantic search across historical case data. |
| **SENTINEL-HUNTER** | Proactive Search | Hypothesis-driven search for "living-off-the-land" (LotL) and APT patterns. |
| **SENTINEL-ENDPOINT-ANALYST** | Execution Forensics | Sysmon / EDR parsing to detect obfuscated command lines and suspicious processes. |
| **SENTINEL-INVESTIGATOR** | Deep Analysis | LLM-driven root cause analysis using Chain-of-Thought reasoning. |
| **SENTINEL-FORENSICS** | Evidence Isolation | Collects and signs (SHA-256) forensic artifacts (RAM, PCAP, Disk). |
| **SENTINEL-MALWARE-PATHOLOGIST** | Malware Analysis | Static and dynamic analysis of binaries in a high-fidelity sandbox. |
| **SENTINEL-GATEKEEPER** | Identity & Access | Detects MFA fatigue, impossible travel, and NHI (Non-Human Identity) risk. |
| **SENTINEL-VANGUARD** | Supply Chain Risk | Ingests SBOMs to instantly flag zero-day impacts on nested libraries. |
| **SENTINEL-MIRAGE** | Deception Operations | Deploys and monitors lightweight honeypots (PLCs, CAD shares) and canaries. |
| **SENTINEL-RED** | Adversary Simulation | Injects synthetic OT/Network threats to continuously audit SOC true-positive detection efficacy. |

---

## 3. The Action Pillar (Response & Remediation)
*These agents take the fight to the adversary and repair the environment.*

| Agent Name | Specialization | Key Capability |
| :--- | :--- | :--- |
| **SENTINEL-PATCHPILOT** | Vulnerability Patching | Drafts context-aware fix scripts for vulnerabilities and hardening failures. |
| **SENTINEL-RESPONDER** | Automated Containment | Performs process kills and network isolation with a built-in dead-man's switch. |

---

## 4. The Business Pillar (Governance & Strategy)
*These agents translate technical data into business value.*

| Agent Name | Specialization | Key Capability |
| :--- | :--- | :--- |
| **SENTINEL-GOVERNOR** | Unified Governance & Tuning | Compliance cross-mapping (NIST/CMMC) and autonomous triage algorithm tuning. |
| **SENTINEL-COMMUNICATOR** | Tri-Factor Reporting | Single-pass synthesis of financial impact, executive reports, and paging dispatch with fatigue filtering. |
| **SENTINEL-HISTORIAN** | Long-Term Tracking | Eliminates temporal noise by ignoring active entities to hunt long-dwell awakenings via WAL. |

---

> [!IMPORTANT]
> **Scaling the Hive**: A true "Score 9.0" Orchestrator doesn't treat these agents as static scripts. It uses **Multi-Agent Consensus**—where *SENTINEL-MALWARE-PATHOLOGIST* and *SENTINEL-GATEKEEPER* must both agree before *SENTINEL-RESPONDER* is allowed to isolate a high-value CEO laptop.
