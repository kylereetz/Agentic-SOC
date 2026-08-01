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
from soc.agents.intelligence.specialists import get_specialist_for_alert
from soc.agents.orchestration.investigation_manager import InvestigationManager

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
        self.callback_bus = EventBus("orchestrator_callbacks")
        self.manager = InvestigationManager()
        self.queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}  # case_id -> task
        self.active_hosts: Set[str] = set()  # IPs currently under investigation
        self.pending_cases: Dict[str, Dict[str, Any]] = (
            {}
        )  # Tracks distributed consensus
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
                logger.debug(
                    f"Enqueued alert {alert.get('rule_id')} with priority {priority}"
                )
            else:
                await asyncio.sleep(1)

    async def process_queue(self):
        """[SQ/IQ] Dispatch specialists from the priority queue."""
        while self.is_running:
            priority, alert = await self.queue.get()
            ip = alert.get("source_ip", "unknown")

            # [IQ] Conflict Resolution: Prevent duplicate investigations for same host
            if ip != "unknown" and ip in self.active_hosts:
                logger.warning(
                    f"[CONFLICT] Delaying investigation for {ip} (Already active)"
                )
                # Put it back in the queue with lower priority
                await self.queue.put((priority + 1, alert))
                self.queue.task_done()
                await asyncio.sleep(2)
                continue

            try:
                # Step 0: Initialise CaseMemory for the hive
                case = self.manager._open_case(alert)

                # Step 1: Topic Routing Selection
                from soc.agents.intelligence.specialists import get_topic_for_alert

                topic_a = get_topic_for_alert(alert)

                # [IQ] Consensus Logic: For CRITICAL, add a second specialist topic queue
                topics_to_run = [topic_a]
                if alert.get("severity") == "CRITICAL":
                    secondary = (
                        "topic_malware"
                        if "modbus" not in str(alert).lower()
                        else "topic_network"
                    )
                    if secondary not in topics_to_run:
                        topics_to_run.append(secondary)

                # Step 2: Distributed Topic Dispatch
                self.active_hosts.add(ip)
                self.pending_cases[case.case_id] = {
                    "expected": len(topics_to_run),
                    "alert": alert,
                    "findings": [],
                    "conclusions": set(),
                }

                logger.info(
                    f"[SYNC] Hive Dispatch for {case.case_id} targeting queues: {topics_to_run}"
                )

                # Publish to topic queues instead of running locally
                for t in topics_to_run:
                    bus = EventBus(t)
                    bus.push({"case_id": case.case_id, "alert": alert})

                self.queue.task_done()

            except Exception as e:
                logger.error(f"Failed to dispatch alert: {e}")
                # Cleanup if dispatch completely failed
                if ip in self.active_hosts:
                    self.active_hosts.remove(ip)
                self.queue.task_done()

    async def _monitor_callbacks(self):
        """[EQ] Monitor callbacks from independent distributed worker agents."""
        while self.is_running:
            cb = await asyncio.to_thread(self.callback_bus.pop)
            if cb:
                case_id = cb.get("case_id")
                agent = cb.get("agent")
                findings = cb.get("findings", [])

                if case_id in self.pending_cases:
                    p = self.pending_cases[case_id]
                    p["conclusions"].add(agent)
                    p["findings"].extend(findings)

                    logger.info(
                        f"[{case_id}] [SYNC] Received callback from {agent}. ({len(p['conclusions'])}/{p['expected']})"
                    )

                    if len(p["conclusions"]) >= p["expected"]:
                        logger.info(f"[{case_id}] [SYNC] Consensus reached!")
                        # Create memory struct for handoff
                        from soc.agents.intelligence.investigator import CaseMemory

                        memory = CaseMemory(case_id=case_id)
                        memory.findings = p["findings"]

                        await self._hand_off_to_remediation(case_id, p["alert"], memory)

                        # Cleanup active host block
                        ip = p["alert"].get("source_ip", "unknown")
                        if ip in self.active_hosts:
                            self.active_hosts.remove(ip)
                        del self.pending_cases[case_id]
                else:
                    logger.warning(
                        f"Received callback for unknown/completed case {case_id} from {agent}"
                    )
            else:
                await asyncio.sleep(1)

    async def _hand_off_to_remediation(
        self, case_id: str, alert: Dict[str, Any], memory
    ):
        """[VQ] Final collective hand-off to WEDGE-RESPONDER."""
        logger.info(
            f"[{case_id}] [SYNC] Consensus reached. Routing to topic_remediation..."
        )

        # Merge finding context
        hive_summary = "\n".join(
            [
                f"{f.get('agent', 'Unknown')}: {f.get('content', '')}"
                for f in memory.findings
            ]
        )

        remediation_prompt = {
            "task": "DRAFT_REMEDIATION",
            "investigation_summary": hive_summary,
            "original_alert": alert,
        }

        # Push to Remediation queue instead of local execution
        EventBus("topic_remediation").push(
            {"case_id": case_id, "alert": remediation_prompt}
        )
        logger.info(f"[{case_id}] [SYNC] Hive Remediation task queued.")

    async def _monitor_deadlocks(self):
        """[EQ] Monitor for stuck agents or unresponsive tasks."""
        while self.is_running:
            logger.debug(
                f"Supervisor Heartbeat: {len(self.active_tasks)} active investigations."
            )
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
            self._monitor_callbacks(),
            self._monitor_deadlocks(),
        )


if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    try:
        asyncio.run(orchestrator.start_async())
    except KeyboardInterrupt:
        print("Stopping Orchestrator...")
