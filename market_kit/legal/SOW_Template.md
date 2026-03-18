# Statement of Work (SOW) — Reetz Cyber Automation (RCA)

**Project Name**: NIST 800-171 Automated Compliance Audit
**Client**: [Client Name]
**Start Date**: [Date]
**Agreement**: Subject to the Master Service Agreement (MSA) dated [MSA Date].

## 1. Engagement Details & Site Scope
- **Client Primary Site**: [Site Address]
- **Target Subnets**: [e.g., 10.0.10.0/24, 192.168.1.0/24] 
- **Engagement Tier**: 
    - [ ] **Tier 1: Audit-Only** (Single Baseline + PDF Report)
    - [ ] **Tier 2: Scout + Audit** (Continuous monitoring + Quarterly reports)
    - [ ] **Tier 3: Full Agentic SOC** (All agents + Incident Response + 4hr SLA)

## 2. Project Scope & SOC Agents
The following services and assets will be deployed based on the selected Tier:

### 2.1 Core Audit (All Tiers)
- Full subnet discovery using **Sentinel Engine** and **Industrial Protocol Scanner**.
- Local hardening assessment of critical Windows/Linux hosts.
- Generation of a **Gap Analysis Report** mapped to NIST 800-171 Rev 3.

### 2.2 Continuous Monitoring (Tier 2 & 3)
- **Scout Agent**: Continuous asset inventory monitoring and drift detection.
- **Topology Mapper**: Real-time asset relationship visualization.
- **Narrator Agent**: Automated quarterly compliance status reports.

### 2.3 Active Response (Tier 3 Only)
- **Triage & Responder Agents**: Automated incident analysis and approved containment.
- **Patch Pilot**: Generation of remediation scripts for identified vulnerabilities.
- **SLA Commitment**: 4-hour notification for Critical/High incidents as per MSA §8.

## 3. Technical Prerequisites
Client agrees to provide the following within five (5) business days of Start Date:
- Network access (VPN or physical presence) to target subnets.
- Administrative credentials for representative host hardening checks.
- A designated technical point-of-contact for remediation approval.

## 4. Pricing & Retainer
- **One-Time Implementation/Audit Fee**: $[Amount]
- **Monthly SOC Retainer**: $[Amount]/month
- **Term**: [Duration, e.g., 12 Months]
- **Payment Terms**: Net 30 days from invoice.

## 5. Deliverables
- [ ] NIST 800-171 Compliance PDF (Auditor Agent)
- [ ] Remediation Action Plan (Patch Pilot Agent)
- [ ] Live Access to SOC Status API/Dashboard

---

**Approvals:**

RCA Project Manager: ____________________ Date: __________

Client Project Manager: ___________________ Date: __________
