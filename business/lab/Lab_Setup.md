# RCA Lab: Air-Gapped OT Stress-Test Environment

To satisfy client concerns about "Legacy Machine Safety," all RCA agents must be stress-tested in this air-gapped environment before deployment.

## Hardware Stack
1.  **Industrial PLC Simulators**: 
    - 2x Raspberry Pi 4 running `OpenPLC` (Modbus/TCP emulator).
    - 1x Siemens S7-1200 (Legacy/Used) for PROFINET/EtherNetIP testing.
2.  **Legacy Endpoints**:
    - 1x Refurbished Dell OptiPlex running Windows 7 (Offline).
    - 1x Mini PC running Windows 10 (Target for Credential Guard testing).
    - 1x Raspberry Pi running Rocky Linux 9 (Target for PAM MFA testing).
3.  **Network Infrastructure**:
    - 1x Managed Layer 2 Switch (Netgear ProSafe) to test VLAN/Subnet isolation.
    - 1x Dedicated GL.iNet Travel Router (WiFi disabled) for DHCP/ARP testing.

## Stress-Test Protocols
- **Sentinel Load Test**: Run passive sniffing with 50+ synthetic nodes to ensure no memory leaks.
- **Industrial "Politeness" Check**: Monitor PLC scan times while `RCAIndustrial` probes are active. Scan time jitter must remain < 5ms.
- **Triage Validation**: Replay known-malicious PCAP files through the Triage agent to verify `CRITICAL` alert triggers.

## Security Controls (Applying NIST to the Lab)
- **3.10.1 (Physical Access)**: Lab hardware must be stored in a locked cabinet when not in use.
- **3.1.22 (Public Networks)**: This lab **must never** be connected to the public internet while RCA proprietary code is loaded. Data transfer should occur via encrypted USB only.
