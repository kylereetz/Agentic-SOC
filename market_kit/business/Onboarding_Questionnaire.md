# Client Onboarding Questionnaire — Reetz Cyber Automation (RCA)

**Goal**: Gather the technical and operational data required to configure the RCA Engine for your environment.

## 1. Network Infrastructure
- **Primary Subnet(s)**: (e.g., 192.168.1.0/24)
- **VLAN Structure**: Do you separate IT (Office) from OT (Shop Floor)?
- **Internet Exit Points**: How many gateways leave the building?

## 2. High-Value OT Assets
Please list the machines most critical to your production line:
| Machine Name | IP Address (if known) | Protocol (Modbus, S7, Ethernet/IP) |
|---|---|---|
| [CNC Mill 1] | | |
| [PLC Controller] | | |

## 3. Legacy Systems & Fragility
- Are there any machines running Windows XP or older?
- Have you experienced network crashes during previous IT scans/pings?

## 4. Compliance Goals
- **Target Deadline**: When do you expect a DoD audit?
- **Key Regulation**: NIST 800-171 Rev 2 or Revision 3?

## 5. Contact Information
- **Technical POC**:
- **Approving Executive**:

---
**Next Step**: Once returned, RCA will configure the `scout_config.json` for your first-run audit.
