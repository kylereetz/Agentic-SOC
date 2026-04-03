#!/bin/bash
# ==============================================================================
# Network Sensor (Zeek + Suricata + Wazuh Agent) Deployment Script
# 
# Purpose: Installs network security monitoring tools on a dedicated VM that
#          receives mirrored SPAN traffic from the Proxmox virtual switch.
# OS Target: Dedicated Ubuntu 22.04 LTS VM (Proxmox, attached to SPAN port)
# ==============================================================================

# Prompt for the SPAN interface name
read -p "Enter the name of the network interface receiving SPAN traffic (e.g., ens19): " SPAN_INTERFACE
read -p "Enter the IP address of your Wazuh Manager: " WAZUH_IP

echo "[*] Installing dependencies..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl wget jq net-tools software-properties-common

# ==================== SURICTA SETUP ====================
echo "[*] Installing Suricata (IDS/IPS)..."
sudo add-apt-repository ppa:oisf/suricata-stable -y
sudo apt-get update
sudo apt-get install suricata -y

# Configure Suricata to listen on the SPAN interface
sudo sed -i "s/interface: eth0/interface: ${SPAN_INTERFACE}/g" /etc/suricata/suricata.yaml

# Download Emerging Threats open ruleset
echo "[*] Updating Suricata Rules..."
sudo suricata-update
sudo systemctl enable suricata
sudo systemctl restart suricata

# ==================== ZEEK SETUP =======================
echo "[*] Installing Zeek (Network Metadata Generation)..."
echo 'deb http://download.opensuse.org/repositories/security:/zeek/xUbuntu_22.04/ /' | sudo tee /etc/apt/sources.list.d/security:zeek.list
curl -fsSL https://download.opensuse.org/repositories/security:zeek/xUbuntu_22.04/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/security_zeek.gpg > /dev/null
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install zeek -y

# Configure Zeek to listen on the SPAN interface
sudo sed -i "s/interface=eth0/interface=${SPAN_INTERFACE}/g" /opt/zeek/etc/node.cfg
sudo /opt/zeek/bin/zeekctl deploy

# ================== WAZUH AGENT SETUP ==================
echo "[*] Installing Wazuh Agent..."
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import && chmod 644 /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | tee -a /etc/apt/sources.list.d/wazuh.list
sudo apt-get update
WAZUH_MANAGER="${WAZUH_IP}" WAZUH_AGENT_GROUP="default" apt-get install wazuh-agent -y

# Configure Wazuh Agent to ingest Zeek and Suricata logs
echo "[*] Configuring Wazuh Agent Log Paths..."

cat <<EOF | sudo tee -a /var/ossec/etc/ossec.conf
  <!-- Ingest Suricata EVE JSON Logs -->
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>

  <!-- Ingest Zeek Modbus Logs -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/opt/zeek/logs/current/modbus.log</location>
  </localfile>
EOF

sudo systemctl daemon-reload
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent

echo "============================================================================="
echo "[+] SENSOR DEPLOYMENT COMPLETE!"
echo "- Suricata is listening on interface: ${SPAN_INTERFACE}"
echo "- Zeek is generating metadata logs."
echo "- Wazuh Agent is forwarding alerts to manager: ${WAZUH_IP}"
echo ""
echo "Verify traffic using: sudo tcpdump -i ${SPAN_INTERFACE}"
echo "============================================================================="
