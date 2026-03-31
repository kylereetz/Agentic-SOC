# RCA Home Lab Design Options (featuring the Powerhouse)

*Your personal PC drastically changes the game.* With 64GB of RAM and a 4080 Super (16GB VRAM), you now have enterprise-grade local AI inference capabilities. The 4080 Super will run `llama3-soc` or any 8B/70B-quantized LLM blazingly fast, fully satisfying the air-gapped requirement without breaking a sweat, while leaving plenty of memory for your day-to-day tasks.

## Hardware Arsenal
- **Personal PC (The Heavyweight)**: i7-10700kf (mid 5GHz), 64GB RAM, RTX 4080 Super.
- **Old Windows Machine**: Dedicated burner node.
- **Raspberry Pi 4**: Versatile ARM node.
- **Raspberry Pi Zero**: Lightweight edge node.
- **TP-Link TL-SG105E**: 5-port managed gigabit switch (VLAN & SPAN/Mirroring).
- **Archer TP-Link AC1200**: Air-gap gateway/router.

---

## Option 1: The "Dual-Brain" Architecture (Highly Recommended)
*This option keeps your personal PC safe from live malware/destruction testing, using it purely as the omniscient SOC Orchestrator while the older hardware acts as the physical "Victims."*

### Roles & Virtualization
* **Personal PC (The SOC Brain - VLAN 30)**:
  * Runs Docker Desktop / WSL2 (or VMware Workstation).
  * Hosts the `Ollama` inference engine natively using your 4080 Super. Your agents (`SENTINEL-GOVERNOR`, `SENTINEL-COMMUNICATOR`, etc.) will respond in milliseconds.
  * Plugs into the lab switch to passively mirror and analyze traffic without putting the PC in the direct line of fire of the lab malware.
* **Old Windows Machine (The IT Victim - VLAN 10)**:
  * Reprovisioned with Proxmox VE or Hyper-V Server.
  * Exclusively runs your Mock Active Directory and 3x simulated workstations. You can aggressively test malware, ransomware, and credential dumping here safely because it's a dedicated burner box.
* **Raspberry Pi 4 & Pi Zero (The OT Victim - VLAN 20)**: 
  * They run Modbus/TCP emulators (like OpenPLC) or small Python SCADA scripts. Plugged directly into the managed switch, providing raw, physical ethernet packets for your SOC to inspect for PLC jitter and anomalies.
* **Archer AC1200 Router**: 
  * Acts as the "air-gap" gateway. Connects the lab VLANs but drops all outbound WAN traffic. 

### Network Topology (TL-SG105E Switch)
* **Port 1 (Access)**: Connects to **Old Windows Machine** (VLAN 10).
* **Port 2 (Access)**: Connects to **Pi 4** (VLAN 20).
* **Port 3 (Access)**: Connects to **Pi Zero** (VLAN 20).
* **Port 4 (Uplink/Trunk)**: Connects to the AC1200 Router.
* **Port 5 (SPAN/Mirror)**: Connects to a secondary NIC (or USB-to-Ethernet) on your **Personal PC**, mirroring packets from Ports 1-3 straight into your RCA Scout container for real-time traffic analysis.

---

## Option 2: The "All-in-One Powerhouse" 
*Use the 64GB of RAM to host literally everything on your main PC, reserving the physical gear for physical attacking/sniffing.*

### Roles & Virtualization
* **Personal PC (The Mothership)**: 
  * Runs Hyper-V or VMware Workstation.
  * Hosts **VLAN 10** (IT Simulation VMs), **VLAN 20** (Simulated SCADA/HMI), and **VLAN 30** (Agentic SOC, Event Bus, Ollama on the 4080 Super).
  * Uses internal virtual switches to strictly segment the traffic. 
* **Old Windows Machine**:
  * Pwnbox. Install Kali Linux on it and plug it into the SG105E switch. Use this machine purely as the attacker to throw exploits at your personal PC's virtualized lab network.
* **Raspberry Pi 4 & Zero**:
  * Distributed network sensors. Use them to sniff physical segments or run Pi-hole/Suricata instances.

### Network Topology
* Keeps your main rig heavily virtualized, utilizing the physical switch to route your Kali Linux machine or Pi attacks into specific access ports mapped to your Personal PC's virtual switches.

---

## The Verdict
**Option 1** is the true "enterprise lab" experience. 

By offloading the vulnerable **Active Directory** and **Workstations** to the "Old Windows machine", you ensure that if a mock ransomware or worm escapes containment during testing, your personal rig and its files are never in the crosshairs. Furthermore, letting your 4080 Super rip through the LLM queues while passively sipping mirrored packets from Port 5 on the switch perfectly emulates how a physical **RCA Agent Appliance** would be deployed in a real-world factory.
