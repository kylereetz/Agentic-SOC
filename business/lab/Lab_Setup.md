# Standard Operating Procedure (SOP): RCA Lab Operations
**Version**: 1.0
**Owner**: Kyler Reetz

## 1. Purpose
To ensure that all Reetz Cyber Automation (RCA) agents are stress-tested in a controlled, air-gapped industrial environment before being deployed to client production networks.

## 2. Hardware Inventory Management
- **Quarterly Audit**: Every 90 days, verify all lab hardware (PLCs, Mini PCs, Managed Switches) are functional.
- **Firmware Lock**: Once a "Safety Baseline" is established for a legacy PLC simulator, do not update its firmware unless a specific vulnerability requires testing.
- **Physical Security**: All lab assets must be stored in the designated locked cabinet. Access is restricted to RCA authorized personnel.

## 3. Agent Staging Process (Pre-Deployment)
Before any new version of an RCA Agent (Scout, Triage, Responder) is delivered to a client site, it MUST undergo the following staging:

### 3.1 Load Testing
- Deploy the agent to the Lab Gateway.
- Simulate 100+ synthetic industrial nodes (Modbus/IP).
- **Pass Criteria**: Agent RAM usage stable < 200MB over 24 hours.

### 3.2 Safety ("Polite Discovery") Test
- Connect a Siemens S7-1200 or OpenPLC simulator.
- Enable `RCAIndustrial` protocol scanning.
- **Pass Criteria**: PLC scan cycle jitter remains < 5ms. No "Safety Stop" or diagnostic errors triggered on the PLC.

### 3.3 Triage Accuracy Test
- Replay a PCAP of a known RDP brute-force or Modbus write attack.
- **Pass Criteria**: Triage agent correctly flags as `CRITICAL` within 30 seconds.

## 4. Air-Gap Integrity
- **NO INTERNET**: The lab network switch must never have an uplink to a public network.
- **Data Transfer**: Code updates and scan reports must move via encrypted, single-use USB drives that are formatted after each transfer.

---
**Approved By**: ____________________ (Kyler Reetz) Date: __________
