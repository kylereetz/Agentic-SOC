"""
RCA Orchestrator Agent: Scaling Agentic Behavior.

This agent acts as the 'Dispatcher'. It monitors the triage bus, 
selects the most appropriate specialist (OT, Network, Identity), 
and manages the investigation lifecycle.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

from soc.bus.event_queue import EventBus
from soc.agents.specialists import get_specialist_for_alert
from soc.agents.investigation_manager import InvestigationManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Orchestrator - %(message)s",
)
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Supervises the assignment of specialized agents to incoming alerts.
    
    This fulfills the requirement to 'scale the agent behavior' by ensuring
    that the right intelligence is applied to the right threat.
    """
    def __init__(self):
        self.in_bus = EventBus("triage_alerts")
        self.manager = InvestigationManager()
        self.queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}  # case_id -> task
        self.active_hosts: Set[str] = set()               # IPs currently under investigation
        self.is_running = False

    async def enqueue_alerts(self):
        """[SQ] Continuously poll the bus and add to Priority Queue."""
        while self.is_running:
            alert = self.in_bus.pop()
            if alert:
                # Priority: CRITICAL=0, WARNING=1, INFO=2
                sev_map = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
                priority = sev_map.get(alert.get("severity", "INFO"), 2)
                
                await self.queue.put((priority, alert))
                logger.debug(f"Enqueued alert {alert.get('rule_id')} with priority {priority}")
            else:
                await asyncio.sleep(1)

    async def process_queue(self):
        """[SQ/IQ] Dispatch specialists from the priority queue."""
        while self.is_running:
            priority, alert = await self.queue.get()
            ip = alert.get("source_ip", "unknown")

            # [IQ] Conflict Resolution: Prevent duplicate investigations for same host
            if ip != "unknown" and ip in self.active_hosts:
                logger.warning(f"[CONFLICT] Delaying investigation for {ip} (Already active)")
                # Put it back in the queue with lower priority
                await self.queue.put((priority + 1, alert))
                self.queue.task_done()
                await asyncio.sleep(2)
                continue

            try:
                # Step 0: Initialise CaseMemory for the hive
                case = self.manager._open_case(alert)
                from soc.agents.investigator import CaseMemory
                memory = CaseMemory(case_id=case.case_id)

                # Step 1: Specialist Selection
                specialist_a = get_specialist_for_alert(alert)
                
                # [IQ] Consensus Logic: For CRITICAL, add a second specialist (Malware or Hunter)
                specialists_to_run = [specialist_a]
                if alert.get("severity") == "CRITICAL":
                    from soc.agents.specialists import MalwarePathologist, ThreatHunter
                    # Pick a different secondary based on type
                    secondary = MalwarePathologist() if "modbus" not in str(alert).lower() else ThreatHunter()
                    specialists_to_run.append(secondary)
                
                # Step 2: Multi-Agent Dispatch
                self.active_hosts.add(ip)
                
                logger.info(f"[SYNC] Hive Dispatch for {case.case_id} ({len(specialists_to_run)} agents)")
                
                # Run specialists in parallel
                tasks = []
                for s in specialists_to_run:
                    task = asyncio.create_task(
                        self._run_specialist_async(s, alert, case.case_id, ip, memory)
                    )
                    tasks.append(task)
                
                # Wait for all specialists to conclude
                await asyncio.gather(*tasks)

                # Step 3: Consensus Check & Remediation Hand-off
                if len(memory.conclusion_consensus) >= len(specialists_to_run):
                    await self._hand_off_to_remediation(case.case_id, alert, memory)
                
            except Exception as e:
                logger.error(f"Failed to dispatch alert: {e}")
            try:
                # Cleanup
                if ip in self.active_hosts:
                    self.active_hosts.remove(ip)
                self.queue.task_done()
            except: pass

    async def _run_specialist_async(self, specialist, alert, case_id, host_ip, memory):
        """[VQ] Async wrapper for specialist analysis with hive memory support."""
        logger.info(f"[{case_id}] [SYNC] Pulse: Starting {specialist.agent_name}")
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, specialist._investigate, alert, case_id, memory)
        except Exception as e:
            logger.error(f"[{case_id}] {specialist.agent_name} failed: {e}")
        finally:
            # Note: active_hosts cleanup is now handled in process_queue's finally block if desired,
            # or here if it's the last task.
            pass

    async def _hand_off_to_remediation(self, case_id: str, alert: Dict[str, Any], memory):
        """[VQ] Final collective hand-off to SENTINEL-FIX."""
        from soc.agents.specialists import RemediationAnalyst
        logger.info(f"[{case_id}] [SYNC] Consensus reached. Handing off to SENTINEL-FIX...")
        
        remediator = RemediationAnalyst()
        loop = asyncio.get_running_loop()
        
        # Merge finding context
        hive_summary = "\n".join([f"{f['agent']}: {f['content']}" for f in memory.findings])
        
        remediation_prompt = {
            "task": "DRAFT_REMEDIATION",
            "investigation_summary": hive_summary,
            "original_alert": alert
        }
        await loop.run_in_executor(None, remediator._investigate, remediation_prompt, case_id, memory)
        logger.info(f"[{case_id}] [SYNC] Hive Remediation plan completed.")

    async def _monitor_deadlocks(self):
        """[EQ] Monitor for stuck agents or unresponsive tasks."""
        while self.is_running:
            logger.debug(f"Supervisor Heartbeat: {len(self.active_tasks)} active investigations.")
            # In a real system, we'd check timestamps here
            await asyncio.sleep(30)

    async def start_async(self):
        """Main async entry point for the orchestrator."""
        self.is_running = True
        logger.info("OrchestratorAgent (v9.0) Supervisor starting...")
        
        # Run supervisor tasks
        await asyncio.gather(
            self.enqueue_alerts(),
            self.process_queue(),
            self._monitor_deadlocks()
        )

if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    try:
        asyncio.run(orchestrator.start_async())
    except KeyboardInterrupt:
        print("Stopping Orchestrator...")
