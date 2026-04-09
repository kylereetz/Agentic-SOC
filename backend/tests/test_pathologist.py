import pytest
from soc.agents.malware_pathologist import MalwarePathologistAgent

@pytest.mark.asyncio
async def test_pathologist_sandbox_parsing():
    """
    Simulate a Cuckoo/CAPE JSON trace to verify the Pathologist correctly
    infers the malware family and extracts MITRE ATT&CK techniques.
    """
    agent = MalwarePathologistAgent()
    
    # Mock Sandbox Trace Data (Typical Cuckoo JSON shape)
    # This simulates a Cobalt Strike beacon execution.
    mock_trace = {
        "file_name": "update_service.exe",
        "file_type": "PE32 executable (GUI) Intel 80386",
        "behavior": {
            "processes": [
                {
                    "process_name": "update_service.exe",
                    "api_calls": [
                        {"api": "CreateProcessInternalW", "args": {"ApplicationName": "svchost.exe"}},
                        {"api": "VirtualAllocEx", "args": {"AllocationType": "MEM_COMMIT | MEM_RESERVE"}},
                        {"api": "WriteProcessMemory", "args": {"Size": 4096}},
                        {"api": "CreateRemoteThread", "args": {"StartAddress": "0x7FF8..."}}
                    ]
                }
            ]
        },
        "network": {
            "http": [
                {
                    "method": "GET",
                    "uri": "/jquery-3.3.1.min.js",
                    "host": "192.0.2.140",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            ]
        }
    }
    
    report = await agent._analyze_sandbox_trace(mock_trace)
    
    # Verify the structured response
    assert report is not None
    assert isinstance(report.malware_family, str)
    assert len(report.mitre_tactics) > 0
    assert report.confidence_score >= 1 and report.confidence_score <= 100
    
    print(f"\n--- Pathologist Report ---")
    print(f"Family: {report.malware_family}")
    print(f"Confidence: {report.confidence_score}")
    print(f"MITRE: {report.mitre_tactics}")
    print(f"Intent: {report.intent_summary}")
    
    # Check for correct semantic extraction (Process Injection -> T1055)
    tactics_str = str(report.mitre_tactics)
    assert "T1055" in tactics_str or "process injection" in report.intent_summary.lower()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pathologist_sandbox_parsing())
