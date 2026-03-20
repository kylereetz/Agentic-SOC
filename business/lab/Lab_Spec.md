# RCA Lab & Testing Specification
**Version**: 1.1

## Overview
The Reetz Cyber Automation (RCA) internal lab network ensures all SOC agents and the core orchestrator engine are tested against realistic, air-gapped industrial IT/OT environments prior to external release.

## Network Topology
- **VLAN 10 (IT Simulation)**:
  - Mock Active Directory server (Windows Server Core).
  - 3x simulated workstation endpoints for testing brute-force anomalies and malware propagation logic.
- **VLAN 20 (OT Emulation)**:
  - 2x Siemens S7-1200 or OpenPLC simulated endpoints mapped for Modbus/TCP testing.
  - Physical or emulated SCADA HMI for validating `SENTINEL-TRAFFIC-SIEVE` behavior alongside safe discovery scanning without PLC jitter.
- **VLAN 30 (RCA Staging)**:
  - Host server for RCA Docker containers.
  - Hosts the underlying file-based secure event bus and API interface.

## Hardware Specification
- **Host hypervisor**: Minisforum or similar dedicated Mini PC with minimum 32GB RAM / 8 physical cores.
- **Switching**: Managed switch capable of SPAN/Port Mirroring to permit passive sniffing tests by the RCA Scout agent.
- **Storage**: Minimum 1TB NVMe for rapid persistence of `business_intel` and `telemetry` event buses during load tests.

## Security Constraints
- All VLANs lack inbound/outbound external gateway access (Air-Gapped).
- Agent execution models are hosted either locally (via Ollama) or proxied through a singular dedicated secure management VPN interface with strictly defined TLS endpoints.
