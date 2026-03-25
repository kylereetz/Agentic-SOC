"""
Verification script: exercises the ForensicsAgent across all four quality dimensions —
IQ (pattern detection), EQ (SHA-256 integrity seals), SQ (paged storage), and VQ (chain-of-custody timeline).
"""
import os
import sys
import json
import hashlib

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.forensics import ForensicsAgent, FORENSICS_ROOT

def test_forensics_harden_detailed():
    print("Initializing Refined ForensicsAgent...")
    agent = ForensicsAgent()
    
    case_id = "INC-HARDEN-REFINE-01"
    target_ip = "192.168.1.105"
    
    print(f"\nTesting IQ: Pattern Matching...")
    evidence = agent.collect_evidence(case_id, target_ip, "MEMORY")
    if evidence["iq_analysis"]["pattern_detection"]:
        print(f"SUCCESS: Patterns detected: {[p['header'] for p in evidence['iq_analysis']['pattern_detection']]}")
    else:
        print("FAILURE: No patterns detected in synthetic memory dump.")

    print(f"\nTesting EQ: Integrity Seals...")
    full_data = "".join(evidence["data_pages"])
    actual_hash = hashlib.sha256(full_data.encode()).hexdigest()
    if evidence["eq_integrity"]["hash"] == actual_hash:
        print(f"SUCCESS: Integrity seal verified [{actual_hash[:8]}]")
    else:
        print("FAILURE: Seal mismatch.")

    print(f"\nTesting SQ: Paged Collection...")
    if evidence["sq_optimization"]["storage_mode"] in ["SINGLE_PAGE", "PAGED"]:
        print(f"SUCCESS: Storage mode: {evidence['sq_optimization']['storage_mode']} ({evidence['sq_optimization']['page_count']} pages)")
    else:
        print("FAILURE: Invalid storage mode.")

    print(f"\nTesting VQ: Evidence Timeline (CoC)...")
    coc_path = os.path.join(FORENSICS_ROOT, "chain_of_custody.json")
    with open(coc_path, "r") as f:
        coc = json.load(f)
    if any(e["evidence_id"] == evidence["evidence_id"] for e in coc["events"]):
        print("SUCCESS: Evidence Timeline entry found.")
    else:
        print("FAILURE: CoC entry missing.")

    print("\nRefined Verification complete.")

if __name__ == "__main__":
    test_forensics_harden_detailed()
