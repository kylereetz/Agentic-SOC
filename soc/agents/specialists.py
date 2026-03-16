"""
RCA Specialist Agents: Specialized Analyst Personas.

This module provides specialized investigator agents tailored to specific 
adversary behaviors (OT, Network, Cloud, Identity).
"""

import logging
from typing import Dict, Any, List, Optional
from soc.agents.investigator import InvestigatorAgent, ReasoningStep, DEFAULT_CONFIG_PATH

logger = logging.getLogger(__name__)

class OTSecurityAnalyst(InvestigatorAgent):
    """
    Expert in Industrial Control Systems (ICS) and Operational Technology (OT).
    Specializes in Modbus, Profinet, EtherNet/IP, and PLC safety.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-OT"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, an elite OT Security Specialist.
Your expertise is in Industrial Control Systems (ICS), SCADA, and PLC security.
You are tasked with investigating alerts involving industrial protocols (Modbus, Profinet, etc.).

Your goal:
1. Identify if the command detected (e.g., Modbus Write) is a legitimate maintenance action or an attack.
2. Determine the potential physical impact on the plant (e.g., valve manipulation, safety trip).
3. Identify the source of the unauthorized command.

SPECIALIZED TOOLS:
- inspect_modbus_traffic(target_ip, port) — Deep packet inspection for industrial protocols. Use this when industrial rules are triggered.

ADVERSARY FOCUS:
- T0836 (Modbus Write Source)
- T0831 (DCP Set Command)
- T0883 (Unauthorized CIP Access)

Use your tools to gather context, but always filter your reasoning through an OT Safety lens (Safety > Availability > Confidentiality).
"""
        self._reinit_model(custom_prompt=prompt)

class NetworkAnalyst(InvestigatorAgent):
    """
    Expert in Network Traffic Analysis (NTA) and Lateral Movement.
    Focuses on beaconing patterns, C2 infrastructure, and pivoting.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-NET"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Lead Network Analyst.
Your expertise is in traffic patterns, beaconing, C2 detection, and lateral movement.

Your goal:
1. Analyze network connections to identify Command & Control (C2) servers.
2. Correlate IP/MAC changes to identify ARP spoofing or MITM attacks.
3. Map the lateral movement path of the adversary.

ADVERSARY FOCUS:
- T1557.002 (ARP Spoofing)
- T1584 (Adversary Infrastructure)
- T1041 (Exfiltration Over C2 Channel)

Always look for timing patterns (jitter) in network connections.
"""
        self._reinit_model(custom_prompt=prompt)

class IdentityAnalyst(InvestigatorAgent):
    """
    Expert in Active Directory, Privilege Escalation, and Credential Theft.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-ID"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Senior Identity Analyst.
Your expertise is in Active Directory, Kerberos, and Authentication protocols.

Your goal:
1. Detect credential theft (Mimikatz, LSASS dumping).
2. Identify privilege escalation attempts.
3. Track the abuse of legitimate accounts (T1078).

SPECIALIZED TOOLS:
- audit_ad_privileges(entity_id) — Audit AD changes and GPO modifications. Use this for identity/account based alerts.

ADVERSARY FOCUS:
- T1003 (OS Credential Dumping)
- T1550.003 (Pass the Ticket)
- T1078 (Valid Accounts)
"""
        self._reinit_model(custom_prompt=prompt)

class RemediationAnalyst(InvestigatorAgent):
    """
    Expert in Containment and Recovery.
    Translates forensic findings into actionable remediation steps.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-FIX"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Lead Remediation Specialist.
Your task is to take a completed investigation summary and produce a high-confidence containment and recovery plan.

Your goal:
1. Identify the minimal impact containment strategy (e.g., VLAN isolation vs Host shutdown).
2. Draft specific, actionable commands for the Responder agent.
3. Ensure no persistence mechanisms are left behind.

SPECIALIZED TOOLS:
- verify_remediation_safety(strategy, target_ip) — Check if an action will break a critical service. ALWAYS call this before drafting a containment strategy for a high-value asset.

ADVERSARY FOCUS:
- T1548 (Abuse Elevation Control)
- T1562 (Impair Defenses)
- T1485 (Data Destruction)

Your reasoning must emphasize safety and the prevention of re-infection.
"""
        self._reinit_model(custom_prompt=prompt)

class CloudWraith(InvestigatorAgent):
    """
    Expert in Cloud Infrastructure (AWS/Azure/GCP) and SaaS Security.
    Focuses on IAM privilege escalation, bucket exposure, and cloud-native attacks.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-CLOUD"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Lead Cloud Security Architect.
Your expertise is in Cloud infrastructure, IAM, and SaaS logging.

Your goal:
1. Detect anomalous resource modification in AWS CloudTrail / Azure Activity Logs.
2. Identify cross-account privilege escalation.
3. Track data exfiltration from storage buckets (S3/Blob).

ADVERSARY FOCUS:
- T1535 (Cloud Initial Access)
- T1548.005 (Cloud Account Elevation)
"""
        self._reinit_model(custom_prompt=prompt)

class MalwarePathologist(InvestigatorAgent):
    """
    Expert in Static/Dynamic Binary Analysis and Sandbox execution.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-LAB"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Senior Malware Pathologist.
Your expertise is in reversing binaries and identifying malicious behavioral signatures.

SPECIALIZED TOOLS:
- analyse_process(pid, host) — Deep process memory analysis.

Your goal:
1. Identify C2 beaconing profiles in injected memory.
2. De-obfuscate PowerShell/Bash payloads.
3. Confirm if a binary matches known APT signatures.
"""
        self._reinit_model(custom_prompt=prompt)

class ThreatHunter(InvestigatorAgent):
    """
    Proactive Hunter focusing on Living-off-the-Land (LotL) and Persistence.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path)
        self.agent_name = "SENTINEL-HUNT"
        self._set_specialized_prompt()

    def _set_specialized_prompt(self):
        prompt = f"""You are {self.agent_name}, a Strategic Threat Hunter.
Your expertise is in long-term persistence and LotL techniques.

Your goal:
1. Find hidden scheduled tasks, registry run-keys, and WMI event consumers.
2. Correlate "Low" severity events that form an attack chain.
"""
        self._reinit_model(custom_prompt=prompt)

def get_specialist_for_alert(alert: Dict[str, Any]) -> InvestigatorAgent:
    """
    Factory to return the most appropriate specialist based on alert metadata.
    """
    rule_name = alert.get("rule_name", "").lower()
    mitre_ttp = alert.get("mitre_ttp", "")
    
    # OT Protocols
    if any(p in rule_name for p in ["modbus", "profinet", "ethernetip", "plc"]) or mitre_ttp.startswith("T08"):
        return OTSecurityAnalyst()
    
    # Identity / Creds
    if any(p in rule_name for p in ["credential", "mimikatz", "identity", "active directory", "account"]):
        return IdentityAnalyst()
    
    # Cloud
    if any(p in rule_name for p in ["aws", "azure", "s3", "cloud", "iam"]):
        return CloudWraith()

    # Malware / Lab
    if any(p in rule_name for p in ["malicious", "beacon", "injected", "malware", "lsass"]):
        return MalwarePathologist()

    # Default to Network or Generalist
    return NetworkAnalyst()
