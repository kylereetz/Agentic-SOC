# Technical Brief: The Agentic SOC for Industrial Environments
**Reetz Cyber Automation — Special Report**

## Executive Summary
Traditional Security Operations Centers (SOCs) are built for the office, not the factory floor. They rely on high-bandwidth traffic mirroring, intrusive scanning, and expensive human analysts. For Wisconsin’s Small/Medium Manufacturers (SMMs), this model is both too expensive and too dangerous for legacy OT hardware. 

**Reetz Cyber Automation (RCA)** introduces the **Agentic SOC**: a decentralized, automated security layer that speaks "Shop Floor" and provides continuous NIST 800-171 compliance telemetry without the human overhead.

---

## 1. The Core Innovation: Autonomous Agents
Instead of a single, monolithic scanner, RCA deploys task-specific **Agents**. These are lightweight Python-based processes that communicate via a secure, local Event Bus.

- **Scout**: Performs continuous, low-impact asset discovery. It uses "Polite Probing" techniques to identify legacy PLCs without triggering safety stops.
- **Triage**: An AI-driven classifier that distinguishes between normal industrial noise (e.g., a Modbus write command from a SCADA host) and malicious activity.
- **Responder**: Drafts containment actions (e.g., Windows Firewall rules) instantly when a critical threat is detected, placing them in a "Human Approval Gate" for safety.
- **Auditor**: Automatically maps discovered network states directly to the SPRS (NIST 800-171) scoring system.

---

## 2. "Polite Discovery" for Legacy OT
The primary fear in industrial security is "The Ping of Death"—an intrusive network scan crashing an old machine. RCA’s **Sentinel Engine** solves this through:
1.  **Passive Sniffing First**: We listen to existing traffic to identify devices before ever sending a packet.
2.  **Context-Aware Probing**: We only query devices using their native industrial protocols (Modbus TCP, Ethernet/IP, S7) once they have been safely identified.
3.  **Air-Gapped Lab Testing**: Every RCA update is validated against our in-house collection of legacy hardware before deployment.

---

## 3. Automated NIST 800-171 Mapping
The "Mapper" component of the RCA Engine takes real-time telemetry and cross-references it with the **NIST 800-171 Revision 3** controls.
- Found an open RDP port? Mapper flags it against **Control 3.1.12** (Restrict remote access).
- New PLC detected? Mapper adds it to the **Control 3.4.1** (System Inventory).
- Result? A living, breathing compliance matrix that is ready for audit every single day.

---

## 4. Conclusion: Contract Insurance
For SMMs, cybersecurity isn't an IT expense—it's **contract insurance**. The RCA Agentic SOC ensures that you don't just *say* you are secure; you can *prove* it with automated, high-authority evidence.

**Contact RDA today for a First-Run Audit.**
*kyler@reetzcyber.com | reetzcyber.com*
