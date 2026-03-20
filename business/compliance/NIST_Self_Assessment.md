# NIST 800-171 Self-Assessment (RCA Environment)

**Organization**: Reetz Cyber Automation LLC
**Assessment Date**: 2026-03-20
**Scope**: RCA Lab and Core Agentic Engine Infrastructure

## 1. Access Control (3.1)
- **3.1.1 Limit system access to authorized users**: Access to the RCA Lab environments is strictly controlled via Role-Based Access Control (RBAC). The SOC dashboard enforces authentication and tracks administrative logins.
- **3.1.2 Limit system access to the types of transactions and functions that authorized users are permitted to execute**: The RCA architecture implements least-privilege. Analyst roles cannot execute containment actions without Admin approval (via the Human Approval Gate endpoints).

## 2. Incident Response (3.6)
- **3.6.1 Establish an operational incident-handling capability for organizational systems**: RCA dogfoods its own Agentic SOC. The 24 AI agents continuously monitor the internal development and lab environments.
- **3.6.2 Track, document, and report incidents to designated officials**: All incidents and "triage alerts" are securely logged to the encrypted file-based event bus, creating a resilient chain of custody for subsequent review by the `SENTINEL-NARRATOR` and `LIBRARIAN` agents.

## 3. System and Information Integrity (3.14)
- **3.14.1 Identify, report, and correct information and system flaws in a timely manner**: Using the integrated `Patch Pilot` and `Responder` agents, the RCA lab continuously remediates newly discovered common vulnerabilities and exposures (CVEs).
- **3.14.6 Monitor organizational systems including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks**: Conducted continuously via `SENTINEL-SCOUT` passive sniffing and active vulnerability assessments.

## Conclusion
The RCA lab currently implements automated controls satisfying key elements of NIST 800-171. Our ongoing continuous monitoring ensures the platform remains aligned with DIB (Defense Industrial Base) security expectations.
