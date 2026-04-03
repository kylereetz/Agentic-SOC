#!/bin/bash
# ==============================================================================
# Wazuh SIEM All-in-One Deployment Script
# 
# Purpose: Deploys a self-contained Wazuh Manager, Indexer, and Dashboard.
# OS Target: Dedicated Ubuntu 22.04 LTS (Proxmox VM, Recommended 8GB RAM, 2 Cores)
# ==============================================================================

echo "[*] Starting Wazuh All-in-One Installation..."

# System Updates
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install curl apt-transport-https unzip wget libcap2-bin software-properties-common lsb-release gnupg2 -y

# Download Wazuh Installation Script
echo "[*] Downloading Wazuh Quickstart..."
curl -sO https://packages.wazuh.com/4.9/wazuh-install.sh

# Execute the Quickstart
# The '-a' flag runs the fully automated "All-in-One" installation.
echo "[*] Running Wazuh automated setup (This will take a few minutes)..."
sudo bash ./wazuh-install.sh -a

echo "============================================================================="
echo "[+] WAZUH INSTALLATION COMPLETE!"
echo "[!] Please save the passwords output above by the Wazuh script."
echo ""
echo "Next Steps:"
echo "1. Navigate to https://<THIS_VM_IP> in your browser."
echo "2. Log in with the 'admin' user and the generated password."
echo "3. Go to 'Add Agent' to securely onboard the OpenPLC, Factory I/O, and Sensor VMs."
echo "============================================================================="
