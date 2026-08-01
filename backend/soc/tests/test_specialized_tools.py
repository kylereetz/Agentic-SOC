"""
Integration test for Specialized Analyst Tooling.
Verifies that specialized agents (OT, ID, FIX) can use their unique tools.
"""

import unittest
from datetime import datetime
from soc.agents.intelligence.specialists import (
    OTSecurityAnalyst,
    IdentityAnalyst,
    RemediationAnalyst,
)
from soc.agents.intelligence.investigator import ReasoningStep


class TestSpecializedTools(unittest.TestCase):

    def test_ot_analyst_modbus_tool(self):
        """Verify the OT analyst knows about and can call Modbus inspection."""
        agent = OTSecurityAnalyst()
        alert = {
            "rule_name": "Unauthorized Modbus Write",
            "source_ip": "10.0.40.50",
            "mitre_ttp": "T0836",
        }
        # We simulate the _investigate loop result or directly call the tool dispatch
        # To keep it fast, we test the tool dispatch capability
        result = agent.tools.dispatch(
            "inspect_modbus_traffic", {"target_ip": "10.0.40.50"}
        )
        self.assertIn("Modbus Inspection", result)
        self.assertIn("Function Code 5", result)

    def test_id_analyst_ad_tool(self):
        """Verify the Identity analyst can call AD privilege audit."""
        agent = IdentityAnalyst()
        result = agent.tools.dispatch(
            "audit_ad_privileges", {"entity_id": "KR\\bad_actor"}
        )
        self.assertIn("AD Privilege Audit", result)
        self.assertIn("Domain Admins", result)

    def test_remediation_safety_tool(self):
        """Verify the Remediation analyst can check for critical service disruption."""
        agent = RemediationAnalyst()

        # Test a critical IP
        critical_result = agent.tools.dispatch(
            "verify_remediation_safety",
            {"strategy": "ISOLATE", "target_ip": "192.168.1.10"},
        )
        self.assertIn("SAFETY WARNING", critical_result)

        # Test a non-critical IP
        safe_result = agent.tools.dispatch(
            "verify_remediation_safety",
            {"strategy": "ISOLATE", "target_ip": "192.168.1.105"},
        )
        self.assertIn("Safety check PASSED", safe_result)


if __name__ == "__main__":
    unittest.main()
