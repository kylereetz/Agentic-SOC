# Master Service Agreement (MSA) — Reetz Cyber Automation (RCA)

This Master Service Agreement ("Agreement") is between **Reetz Cyber Automation LLC** ("Company") and the **Client** identified in the applicable Statement of Work (SOW).

## 1. Services
Company shall provide automated NIST 800-171 compliance telemetry and OT security monitoring services as defined in the SOW ("Services"). Services are delivered via the "RCA Engine" and specialized "SOC Agents" deployed locally on Client's network.

## 2. Shared Responsibility Model
Client acknowledges that cybersecurity is a shared responsibility.
- **Company Responsibility**: Ensuring the RCA engine correctly identifies assets and maps discovered configurations against the NIST 800-171 baseline as specified by the DOD/NIST guidance.
- **Client Responsibility**: Maintaining physical security of hardware, managing user credentials, implementing the remediation scripts drafted by the RCA Patch Pilot agent, and notifying Company of any major OT network changes not covered by current SOW.

## 3. Intellectual Property (IP)
All software, agents, algorithms, and methodologies used to provide the Services—including but not limited to the RCA Engine (Sentinel, Mapper, Industrial) and SOC Agents (Scout, Triage, Responder, Auditor)—are the sole and exclusive property of **Reetz Cyber Automation LLC**. Client is granted a non-exclusive, non-transferable license to use the generated Reports and Patch Scripts for internal compliance purposes during the term of this Agreement.

## 4. Confidentiality
Both parties agree to protect "Confidential Information" with the same degree of care they use for their own sensitive data.
- **Client Confidential Information**: Network maps, asset inventories, vulnerability scan results, and production schedules.
- **Company Confidential Information**: Proprietary scanning logic, agent source code, and pricing structures.
- **Exception**: Company may use anonymized, aggregated telemetry data for the purpose of improving the RCA Engine's threat detection capabilities.

## 5. Limitation of Liability
> [!IMPORTANT]
> To the maximum extent permitted by law, Company's total liability for any claims arising out of this Agreement shall not exceed the total fees paid by Client to Company in the six (6) months preceding the incident. Company is not liable for manufacturing downtime caused by OT protocol discovery, legacy hardware failures, or the execution of remediation scripts by Client personnel.

## 6. Data Handling & Security
Company is committed to maintaining the highest standard of data privacy and security, as continuous monitoring requires access to sensitive network telemetry.
- **Encryption**: All network scan data, asset inventories, and alert logs are encrypted at rest using AES-256 (via Fernet) and in transit via TLS 1.3 or higher. Cryptographic keys are managed within dedicated secure vaults and are never exposed in application source code.
- **Event Bus Integrity**: Inter-agent communication occurs over a proprietary secure, file-based event bus. Messages are cryptographically signed (HMAC-SHA256) to ensure integrity, prevent unauthorized tampering, and maintain a robust, court-admissible Chain of Custody.
- **Data Residency & Minimization**: Client data will remain within authorized geographical boundaries as mandated by the SOW. Raw telemetry is processed in-memory where possible. Persistent logs are strictly minimized, and temporary files are systematically purged following analysis in accordance with minimum necessity principles.
- **Compliance Alignment**: Data handling practices strictly follow the guidelines prescribed by NIST 800-171 and CMMC 2.0 level requirements, ensuring robust access control, continuous auditing, and logical separation of client environments.

## 7. Statement of Work (SOW) Framework
Specific scopes of work, resource allocations, engagement tiers, and customized deliverables shall be governed by a separate Statement of Work (SOW), which shall be incorporated into this Agreement as an Exhibit.
- **SLA Variations**: Specific response time exceptions, maintenance window overrides, or priority routing requirements will be explicitly detailed in the SOW.
- **Resource Limits & LLM Constraints**: The SOW specifies compute resource constraints, including absolute limits on RCA Agent LLM token usage ("Tokens per Client"). Upon reaching 95% of allocated tokens, Company will notify Client. Excess usage required for active incident remediation may result in overage charges or temporary telemetry throttling, subject to Client's predefined approval matrix.
- **Conflict Resolution**: In the event of a conflict between the terms of this MSA and any corresponding SOW, the terms of the SOW shall prevail exclusively for that specific engagement.

## 8. Incident Notification SLA
Company acknowledges that timely response is critical for effective incident containment and commits to the following Service Level Agreements (SLAs) for notification:
- **Critical Severity**: Active indicators of compromise (IoC), unauthorized lateral movement, or critical network breaches. **SLA: 1 Hour (24/7/365)**.
- **High Severity**: Identified vulnerabilities with known, active exploits in the wild affecting core production infrastructure. **SLA: 4 Hours**.
- **Medium/Low Severity**: Configuration anomalies, unauthorized software installations, or non-critical vulnerabilities. Included in weekly aggregated Reports.
- **RCA Engine Uptime Guarantee**: The underlying RCA orchestrator and agentic infrastructure will maintain a 99.9% uptime SLA. Scheduled maintenance windows will be communicated at least 48 hours in advance.
- **Notification Method**: Alerts will be delivered via the agreed-upon primary communication channel (e.g., Client Dashboard, secure email, or automated SMS/pager integration) as defined in the SOW.

## 9. No Guarantee of Compliance
The Services are intended to assist Client in meeting NIST 800-171 and CMMC requirements. However, Company does not guarantee that Client will pass any official audit or be declared "compliant" by a third-party assessor (C3PAO).

## 10. Data Retention & Privacy
Upon termination of this Agreement, Company shall delete all Client-specific raw scan data within ninety (90) days. Summarized compliance reports generated during the term may be retained for legal record-keeping for up to seven (7) years.

## 11. Termination
Either party may terminate this agreement with thirty (30) days written notice. In the event of material breach, termination may be immediate.

---

**Signatures:**

RCA Representative: ____________________ Date: __________

Client Representative: ___________________ Date: __________
