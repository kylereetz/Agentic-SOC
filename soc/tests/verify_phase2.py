import asyncio
import os
import json
import unittest
from datetime import datetime, timezone

# Ensure we can import from the project root
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from soc.agents.librarian import LibrarianAgent
from soc.agents.topology_mapper import TopologyMapper

class TestPhase2Components(unittest.IsolatedAsyncioTestCase):

    async def test_librarian_rag_logic(self):
        """Verify Librarian can index and search."""
        lib = LibrarianAgent()
        # Mock index
        lib.index = {}
        
        test_case = {
            "case_id": "CASE-999",
            "summary": "Brute force attack on SSH",
            "mitre_ttp": "T1110",
            "hypothesis": "External actor attempting password spraying",
            "reasoning_steps": ["Logon failures detected", "Source IP 8.8.8.8"]
        }
        
        # Manually trigger indexing logic (normally async via bus)
        content = f"{test_case['summary']} {test_case['hypothesis']}"
        embedding = await lib._generate_embedding(content)
        
        lib.index["CASE-999"] = {
            "summary": test_case["summary"],
            "hypothesis": test_case["hypothesis"],
            "embedding": embedding,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Test Search
        results = await lib.search("SSH login", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["case_id"], "CASE-999")
        self.assertGreater(results[0]["similarity"], 0.5)
        print(f"[SUCCESS] Librarian search verified: {results[0]['similarity']}")

    async def test_topology_mapper_logic(self):
        """Verify TopologyMapper builds the graph correctly."""
        mapper = TopologyMapper()
        mapper.nodes = {}
        mapper.edges = {}
        
        # Simulate host discovery
        mapper._add_node("10.0.0.5", "Host", "Host-A")
        
        # Simulate user logon
        mapper._add_node("kyle", "User", "kyle")
        mapper._add_edge("kyle", "10.0.0.5", "LOGGED_INTO")
        
        topology = mapper.get_topology()
        
        self.assertEqual(len(topology["nodes"]), 2)
        self.assertEqual(len(topology["edges"]), 1)
        self.assertEqual(topology["edges"][0]["source"], "kyle")
        self.assertEqual(topology["edges"][0]["target"], "10.0.0.5")
        print("[SUCCESS] Topology mapper graph logic verified.")

if __name__ == "__main__":
    unittest.main()
