# Master Service Agreement (MSA) — Reetz Cyber Automation (RCA)

**DRAFT FOR REVIEW — NOT A LEGAL DOCUMENT UNTIL SIGNED**

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

## 6. No Guarantee of Compliance
The Services are intended to assist Client in meeting NIST 800-171 and CMMC requirements. However, Company does not guarantee that Client will pass any official audit or be declared "compliant" by a third-party assessor (C3PAO).

## 7. Data Retention & Privacy
Upon termination of this Agreement, Company shall delete all Client-specific raw scan data within ninety (90) days. Summarized compliance reports generated during the term may be retained for legal record-keeping for up to seven (7) years.

## 8. Termination
Either party may terminate this agreement with thirty (30) days written notice. In the event of material breach, termination may be immediate.

---

**Signatures:**

RCA Representative: ____________________ Date: __________

Client Representative: ___________________ Date: __________
