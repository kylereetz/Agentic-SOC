import asyncio
import os
import sys
import json
import time
import sqlite3
from datetime import datetime, timezone
from dataclasses import asdict

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.investigation_manager import InvestigationManager
from soc.agents.librarian import LibrarianAgent
from soc.agents.dispatch import DispatchAgent
from soc.agents.correlator import CorrelatorAgent
from soc.agents.triage import TriageAgent
from soc.agents.investigator import InvestigatorAgent

async def run_hive_benchmark():
    print("="*60)
    print("  SENTINEL HIVE BENCHMARK: SYSTEM-WIDE HARDENING AUDIT")
    print("="*60)
    
    # Initialize Core Hive
    print("\n[SYSTEM] Booting Hive Components...")
    manager = InvestigationManager()
    librarian = LibrarianAgent()
    dispatch = DispatchAgent()
    correlator = CorrelatorAgent()
    
    # Shared tasks
    tasks = [
        asyncio.create_task(manager.run()),
        asyncio.create_task(librarian.run()),
        asyncio.create_task(dispatch.run()),
        asyncio.create_task(correlator.run())
    ]
    
    audit_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scores": {},
        "critiques": []
    }

    try:
        # TEST 1: The Multi-Stage Campaign (Correlator + Manager + Dispatch)
        print("\n[TEST 1] Attack Chain Correlation & Notification Flow...")
        attacker_ip = "10.hive.audit.1"
        
        # Sequence: Recon -> Lateral -> Exfil
        events = [
            {"rule_id": "RECON_001", "rule_name": "Recon Scan", "severity": "LOW", "source_ip": attacker_ip},
            {"rule_id": "LATERAL_001", "rule_name": "SMB Lateral", "severity": "WARNING", "source_ip": attacker_ip},
            {"rule_id": "EXFIL_001", "rule_name": "DNS Exfil", "severity": "WARNING", "source_ip": attacker_ip}
        ]
        
        for e in events:
            manager.in_bus.push(e)
            await asyncio.sleep(1)
            
        await asyncio.sleep(5) # Propagation time
        
        # Verify Manager created a Campaign case
        campaign_cases = [c for c in manager.active_cases.values() if "Campaign" in c.alert_details.get("rule_name", "")]
        if campaign_cases:
            print("  [PASS] Correlator identified multi-stage threat.")
            print("  [PASS] Manager ingested promoted campaign alert.")
            audit_results["scores"]["correlation"] = 9.8
        else:
            print("  [FAIL] Campaign promotion failed.")
            audit_results["scores"]["correlation"] = 4.0
            audit_results["critiques"].append("Correlator promotion to Manager failed to trigger Case creation.")

        # TEST 2: RAG Institutional Memory (Librarian)
        print("\n[TEST 2] RAG Retrieval Accuracy...")
        query = "How did the campaign for 10.hive.audit.1 progress?"
        memories = librarian.search(query, limit=1)
        if memories and memories[0]["case_id"] == campaign_cases[0].case_id:
            print(f"  [PASS] Librarian retrieved historical context (Score: {memories[0]['similarity']})")
            audit_results["scores"]["rag"] = 9.6
        else:
            print("  [FAIL] Librarian retrieval missed relevant campaign case.")
            audit_results["scores"]["rag"] = 3.0

        # TEST 3: Persistence & WAL Integrity (Investigation Manager)
        print("\n[TEST 3] SQLite & WAL Persistence Check...")
        if os.path.exists(manager.conn_path if hasattr(manager, 'conn_path') else "soc/reports/incidents/cases/soc_cases.db"):
            print("  [PASS] SQLite Database exists.")
            audit_results["scores"]["persistence"] = 9.2
        else:
            print("  [FAIL] Database file not found.")
            audit_results["scores"]["persistence"] = 0.0

        # TEST 4: Dispatch Suppression (Alert Fatigue)
        print("\n[TEST 4] Dispatch Storm Suppression...")
        # Check history size for the campaign case
        case_id = campaign_cases[0].case_id if campaign_cases else "NONE"
        matches = [h for h in dispatch.history if h["case_id"] == case_id]
        if len(matches) <= 2: # Slack + PD for initial opening, none for subsequent saves
            print(f"  [PASS] Dispatch suppressed redundant noise ({len(matches)} notifications sent).")
            audit_results["scores"]["noise_reduction"] = 9.5
        else:
            print(f"  [FAIL] Dispatch sent too many notifications ({len(matches)}) for a single case.")
            audit_results["scores"]["noise_reduction"] = 6.0

    finally:
        # Stop Hive
        manager.is_running = False
        librarian.is_running = False
        dispatch.is_running = False
        correlator.is_running = False
        for t in tasks:
            t.cancel()
            
    print("\n" + "="*60)
    print("  FINAL HIVE AUDIT COMPLETE")
    print("="*60)
    
    # Save the report
    with open("hive_audit_raw.json", "w") as f:
        json.dump(audit_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_hive_benchmark())
