import os
import sys

from soc.agents.triage import TriageEngine, TriageAlert

def test_triage_spoofing_prevention():
    engine = TriageEngine()
    
    # Inject a test rule that hits CRITICAL natively
    engine.rules = [
        {
            "id": "RULE-TEST-01",
            "name": "Simulated Critical Event",
            "severity": "CRITICAL",
            "classification": "malicious",
            "description": "Simulative rule",
            "pattern": {
                "event_type": "vuln_exploit"
            }
        }
    ]

    print("\n--- Test 1: Spoofed UDP Packet (Connectionless) ---")
    spoofed_event = {
        "event_type": "vuln_exploit",
        "protocol": "UDP",
        "ip": "10.0.0.50",
        "mac": "AA:BB:CC:DD:EE:FF"
    }
    
    alert1 = engine.classify_event(spoofed_event)
    print(f"Severity returned: {alert1.severity}")
    if alert1.severity == "WARNING":
        print("[SUCCESS] Corroboration mandate successfully capped spoofed UDP alert to WARNING.")
    else:
        print(f"[FAILURE] Spoofed event was not capped: {alert1.severity}")
        sys.exit(1)

    print("\n--- Test 2: Validated TCP Packet (Handshake Complete) ---")
    validated_tcp_event = {
        "event_type": "vuln_exploit",
        "protocol": "TCP",
        "flags": "ACK, PSH",
        "ip": "10.0.0.50",
        "mac": "AA:BB:CC:DD:EE:FF"
    }
    
    alert2 = engine.classify_event(validated_tcp_event)
    print(f"Severity returned: {alert2.severity}")
    if alert2.severity == "CRITICAL":
        print("[SUCCESS] State/Telemetry mechanism permitted verified TCP connection to remain CRITICAL.")
    else:
        print(f"[FAILURE] Validated event was erroneously capped: {alert2.severity}")
        sys.exit(1)

    print("\n--- Test 3: EDR Correlated Event (Host Telemetry) ---")
    edr_event = {
        "event_type": "vuln_exploit",
        "protocol": "UDP", # Even if UDP, EDR verifies it
        "edr_correlated": True,
        "ip": "10.0.0.50"
    }
    
    alert3 = engine.classify_event(edr_event)
    print(f"Severity returned: {alert3.severity}")
    if alert3.severity == "CRITICAL":
        print("[SUCCESS] State/Telemetry mechanism permitted EDR correlated alert to remain CRITICAL.")
    else:
        print(f"[FAILURE] Correlated event was erroneously capped: {alert3.severity}")
        sys.exit(1)


if __name__ == "__main__":
    test_triage_spoofing_prevention()
