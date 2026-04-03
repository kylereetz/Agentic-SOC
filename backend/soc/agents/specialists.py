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
        super().__init__(config_path, routing_topic="topic_ot")
        self.agent_name = "SENTINEL-OT"
        super().__init__(config_path, routing_topic="topic_ot")
        self.agent_name = "SENTINEL-OT"
        # [IQ] Dynamic Ethos Loading: Base class now automatically loads ethos_sentinel_ot.md
        self._reinit_model()

class NetworkAnalyst(InvestigatorAgent):
    """
    Expert in Network Traffic Analysis (NTA) and Lateral Movement.
    Focuses on beaconing patterns, C2 infrastructure, and pivoting.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path, routing_topic="topic_network")
        self.agent_name = "SENTINEL-NET"
        super().__init__(config_path, routing_topic="topic_network")
        self.agent_name = "SENTINEL-NET"
        # [IQ] Dynamic Ethos Loading: Base class now automatically loads ethos_sentinel_net.md
        self._reinit_model()

class IdentityAnalyst(InvestigatorAgent):
    """
    Expert in Active Directory, Privilege Escalation, and Credential Theft.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path, routing_topic="topic_identity")
        self.agent_name = "SENTINEL-ID"
        super().__init__(config_path, routing_topic="topic_identity")
        self.agent_name = "SENTINEL-ID"
        # [IQ] Dynamic Ethos Loading: Base class now automatically loads ethos_sentinel_id.md
        self._reinit_model()

class RemediationAnalyst(InvestigatorAgent):
    """
    Expert in Containment and Recovery.
    Translates forensic findings into actionable remediation steps.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path, routing_topic="topic_remediation")
        self.agent_name = "SENTINEL-FIX"
        super().__init__(config_path, routing_topic="topic_remediation")
        self.agent_name = "SENTINEL-FIX"
        # [IQ] Dynamic Ethos Loading: Base class now automatically loads ethos_sentinel_fix.md
        self._reinit_model()


class MalwarePathologist(InvestigatorAgent):
    """
    Expert in Static/Dynamic Binary Analysis and Sandbox execution.
    """
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        super().__init__(config_path, routing_topic="topic_malware")
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
        super().__init__(config_path, routing_topic="topic_network")
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
    

    # Malware / Lab
    if any(p in rule_name for p in ["malicious", "beacon", "injected", "malware", "lsass"]):
        return MalwarePathologist()

    # Default to Network or Generalist
    return NetworkAnalyst()

def get_topic_for_alert(alert: Dict[str, Any]) -> str:
    """
    Determine the appropriate EventBus topic queue for an alert based on metadata.
    """
    rule_name = alert.get("rule_name", "").lower()
    mitre_ttp = alert.get("mitre_ttp", "")
    
    # OT Protocols
    if any(p in rule_name for p in ["modbus", "profinet", "ethernetip", "plc"]) or mitre_ttp.startswith("T08"):
        return "topic_ot"
    
    # Identity / Creds
    if any(p in rule_name for p in ["credential", "mimikatz", "identity", "active directory", "account"]):
        return "topic_identity"
    

    # Malware / Lab
    if any(p in rule_name for p in ["malicious", "beacon", "injected", "malware", "lsass"]):
        return "topic_malware"

    # Default to Network or Generalist
    return "topic_network"
