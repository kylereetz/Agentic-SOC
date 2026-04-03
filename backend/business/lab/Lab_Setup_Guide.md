# RCA Lab Setup Guide: The "Dual-Brain" Architecture

## Overview
This guide provides step-by-step instructions to turn your existing hardware into the `Lab_Spec.md`-compliant Reetz Cyber Automation (RCA) testing environment. 

### Roles & Inventory
1. **Archer AC1200 (Router)**: The air-gapped gateway and management Access Point.
2. **TP-Link TL-SG105E (Switch)**: The core VLAN segmentation and packet-mirroring tap.
3. **Old Windows PC (Proxmox)**: The "Burner" node hosting the vulnerable IT Network (VLAN 10).
4. **Raspberry Pi 4 & Pi Zero**: The physical OT emulation devices (VLAN 20).
5. **Personal PC (10700kf, 4080 Super)**: The SOC Orchestrator and Agentic `llama3-soc` LLM node (VLAN 30).

---

## Phase 1: The Network Backbone
*We must establish the VLAN isolation and SPAN (Port Mirroring) first, so that your SOC has a funnel of data to inspect.*

### 1.1 Archer AC1200 Router (The Airgap AP)
Because you want an air-gapped environment, the router acts strictly as a local DHCP server and Wireless Access Point. 
1. Log into the AC1200 web interface.
2. Unplug the WAN/Internet port. It should not be connected to your home modem.
3. Configure the wireless settings: Broadcast a new SSID (e.g., `RCA-Lab-Airgap`). You will use your PC or laptop to connect to this WiFi for management.
4. Set the LAN IP address of the router to `10.0.30.1` (placing it in the Management VLAN 30 subnet).

### 1.2 TP-Link TL-SG105E Switch (VLANs & Mirroring)
This managed switch enforces the logical separation of your lab and provides the critical packet sniffing functionality.
1. Connect to the switch's web interface (default `192.168.0.1` or check your router).
2. Go to **VLAN** -> **802.1Q VLAN** and enable the feature. Set up the following:
   - **VLAN 10 (IT VLAN)**: Set **Port 2** as Untagged (PVID 10).
   - **VLAN 20 (OT VLAN)**: Set **Port 3** and **Port 4** as Untagged (PVID 20).
   - **VLAN 30 (SOC VLAN)**: Set **Port 5** as Untagged (PVID 30). Connect **Port 5** to a LAN port on the Archer AC1200.
3. Go to **Monitoring** -> **Port Mirroring**. 
   - **Mirroring Port (Destination)**: Select **Port 1** (This will plug into your Personal PC's Ethernet port).
   - **Mirrored Ports (Source)**: Select **Ports 2, 3, and 4** for both Ingress and Egress. 
   *(Now, any traffic inside the IT or OT VLANs gets copied and secretly blasted to your Personal PC on Port 1 for the RCA Scout to analyze).*

---

## Phase 2: The OT Edge (VLAN 20)
*Setting up the physical, destructible endpoints at the edge of the switch.*

### 2.1 Raspberry Pi 4 (Physical SCADA)
1. Flash **Raspberry Pi OS Lite (64-bit)** to an SD card.
2. Plug the Pi into **Port 3** on the SG105E switch.
3. Once booted and assigned an IP by the router, SSH in and install **OpenPLC** (or a simple Python Modbus server):
   ```bash
   git clone https://github.com/thiagoralves/OpenPLC_v3.git
   cd OpenPLC_v3
   ./install.sh linux
   ```
4. This Pi now acts as your primary simulated industrial controller.

### 2.2 Raspberry Pi Zero (Lightweight Edge)
1. Flash **Kali Linux** or **Raspberry Pi OS Lite** to the Zero.
2. Plug the Pi Zero into **Port 4** on the SG105E switch (via a USB-Ethernet adapter or directly if it's a newer model with a hat).
3. Use this device as a secondary sensor, or write a lightweight python script that periodically polls the Pi 4 over Modbus port 502 to simulate legitimate industrial chatter.

---

## Phase 3: The "Burner" IT Network (VLAN 10)
*This is the isolated playground where you will unleash worms, ransomware, and credential dumping algorithms.*

### 3.1 Provisioning the Old Windows PC
1. Download the **Proxmox VE** ISO and flash it to a USB drive using Rufus.
2. Boot your Old Windows PC from the USB and install Proxmox on the hard drive. 
3. Connect the Old PC's ethernet port to **Port 2** on the SG105E switch.
4. Access the Proxmox Web GUI (you can reach it via the AC1200 Wi-Fi if no strict ACLs are blocking inter-vlan).
5. Open Proxmox, navigate to **Network**, and ensure the default virtual bridge `vmbr0` is active.

### 3.2 Building the Victim Environment
Inside Proxmox, create the following VMs:
1. **Windows Server Core (Mock AD)**: Install the Active Directory Domain Services role. Create a dummy domain (`rca.local`).
2. **Windows 10/11 Workstations**: Create 1-2 thin Windows VMs. Join them to the `rca.local` domain. 
*Note: Because this machine is on Port 2, all active directory chatter, internal brute-forcing, and malware traffic will be mirrored to your 4080 Super rig for LLM inspection.*

---

## Phase 4: The Powerhouse SOC Orchestrator (VLAN 30)
*Your Personal PC will use its massive 64GB RAM and 4080 Super to digest the lab data in real-time.*

### 4.1 Physical Connection Setup
1. Connect your Personal PC via **Wi-Fi** to the `RCA-Lab-Airgap` network for general web management and API interaction.
2. Connect your Personal PC's **Ethernet Port** directly into **Port 1** of the SG105E switch. 
   *(Because Port 1 is the Mirror destination, it will receive a firehose of packets from the other devices without actually interacting back).*

### 4.2 SOC Tooling Setup
1. **Ollama & LLM**: Install [Ollama for Windows](https://ollama.com). Open PowerShell and run:
   ```bash
   ollama run llama3:8b-instruct
   ```
   *(Your 4080 Super will cache this 16GB model effortlessly, exposing the local API on `localhost:11434` for the Agentic SOC).*
2. **Promiscuous Interface Listener**: Ensure your RCA Scout Agent (or Wireshark) binds to the physical Ethernet adapter on your Personal PC in *Promiscuous Mode*. It will rip through the mirrored switch traffic looking for Modbus anomalies or SMB brute-forcing from your Old PC.
3. **Agentic Containers**: Run Docker Desktop (using WSL2 limits so it doesn't starve your local games/apps). Spin up the `business_intel` and `telemetry` event buses.

---

## Verification
1. Open Wireshark on your Personal PC and bind it to the Ethernet adapter.
2. Ping the Pi 4 from the virtual Windows VM on your Old PC.
3. You should see the ICMP packets show up in your Wireshark feed, proving the SG105E's **Port 5 SPAN** mirroring is perfectly shoveling the lab data into your 4080 Super rig!
