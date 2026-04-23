import os
import json
import uuid
from datetime import datetime, timezone
from soc.bus.event_queue import EventBus
from soc.agents.orchestration.investigation_manager import InvestigationManager
from soc.agents.intelligence.investigator import InvestigatorAgent
from soc.bootstrap import get_soc_path

def test_alert_to_case_lifecycle():
    """
    Integration Test: Alert -> Case -> Reasoning -> Promotion
    """
    manager = InvestigationManager()
    triage_bus = EventBus("triage_alerts")
    reasoning_bus = EventBus("investigation_reasoning")
    
    # 1. Clear queues (pop everything)
    while triage_bus.pop(): pass
    while reasoning_bus.pop(): pass
    
    # 2. Push a Critical Alert
    test_alert = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rule_id": "RULE_INTEGRATION_TEST",
        "rule_name": "Integration Test Alert",
        "severity": "CRITICAL",
        "source_ip": "10.0.0.5",
        "description": "Integration Test Description",
        "mitre_ttp": "T1614",
        "nist_control": "3.1.1"
    }
    triage_bus.push(test_alert)
    
    # 3. Run Manager to open Case
    count = manager.run_cycle()
    assert count >= 1
    
    # Get the newly opened case
    case_id = None
    for cid, case in manager.active_cases.items():
        if case.source_ip == "10.0.0.5":
            case_id = cid
            break
    
    assert case_id is not None
    assert manager.active_cases[case_id].status == "TRIAGE"
    
    # 4. Push a Reasoning Step for this Case
    test_step = {
        "investigation_id": case_id,
        "type": "THOUGHT",
        "content": "Running integration test thought step.",
        "agent": "TEST-AGENT",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    reasoning_bus.push(test_step)
    
    # 5. Run Manager to Sync reasoning and promote
    manager.run_cycle()
    
    # 6. Verify Promotion and Linking
    updated_case = manager.active_cases[case_id]
    assert updated_case.status == "SCOPING"
    assert any("integration test thought step" in r for r in updated_case.reasoning_steps)
    
    print(f"Integration Test Passed: {case_id} promoted to SCOPING.")

if __name__ == "__main__":
    test_alert_to_case_lifecycle()
