#!/bin/bash
# ==============================================================================
# OpenPLC Logic Engine Deployment Script
# 
# Purpose: Compiles and deploys OpenPLC v3 as a background daemon.
#          By default, this will bind to port 502 (Modbus TCP).
# OS Target: Dedicated Ubuntu 22.04 LTS VM (Proxmox)
# ==============================================================================

echo "[*] Starting OpenPLC Installation..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git build-essential pkg-config build-essential autoconf automake libtool cmake python3 python3-pip

echo "[*] Cloning OpenPLC Repository..."
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3

echo "[*] Running the installer for Linux... (This compiles C dependencies and takes some time)"
sudo ./install.sh linux

echo "============================================================================="
echo "[+] OPENPLC INSTALLATION COMPLETE!"
echo "Next Steps:"
echo "1. Start the OpenPLC runtime via the menu system or daemon."
echo "2. Open your browser and navigate to http://<THIS_VM_IP>:8080"
echo "3. Default login is 'openplc' / 'openplc'."
echo "4. Upload a simple ladder logic program and start the PLC runtime."
echo "5. Factory I/O (on Windows) will now be able to connect via Modbus TCP on port 502."
echo "============================================================================="
