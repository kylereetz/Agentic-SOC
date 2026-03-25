import logging
import os
import sys
import time
import json
import asyncio
import zipfile
from typing import Optional, List
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Main - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Reetz Cyber Automation (RCA) — Agentic SOC Orchestrator")
console = Console()

# =========================================================================
# Subcommand: bootstrap
# =========================================================================
@app.command()
def bootstrap():
    """Initialize the SOC environment (directories and configs)."""
    from soc.bootstrap import bootstrap_soc
    if bootstrap_soc():
        console.print("[bold green]Success:[/bold green] SOC environment is ready.")
    else:
        console.print("[bold red]Error:[/bold red] SOC bootstrap failed. Check logs.")
        raise typer.Exit(code=1)

# =========================================================================
# Subcommand: audit
# =========================================================================
@app.command()
def audit(
    audit_subnet: Optional[str] = typer.Option(None, help="Subnet to scan (e.g. 192.168.1.0/24)"),
    timeout: int = typer.Option(5, help="Timeout for network scans"),
    industrial: bool = typer.Option(False, help="Enable industrial protocol probing"),
    no_hardening: bool = typer.Option(False, help="Skip local OS hardening checks"),
    hardening_only: bool = typer.Option(False, help="Run ONLY local hardening checks")
):
    """Run a First-Run Audit (discovery + compliance + hardening)."""
    from engine.core.sentinel import SentinelEngine
    from engine.core.mapper import NISTMapper
    from engine.core.detector import run_local_hardening
    from engine.core.industrial import IndustrialScanner

    logger.info("=" * 60)
    logger.info("  Reetz Cyber Automation (RCA) — First-Run Audit")
    logger.info("=" * 60)

    if hardening_only:
        report = run_local_hardening()
        _print_hardening(report)
        return

    # Discovery
    sentinel = SentinelEngine()
    logger.info("Phase 1: Passive Sniffing (15s) …")
    sentinel.passive_sniffing(timeout=15)

    if audit_subnet:
        logger.info(f"Phase 2: ARP Sweep ({audit_subnet}) …")
        sentinel.active_arp_scan(target_subnet=audit_subnet, timeout=timeout)
        ips = list(sentinel.get_inventory().keys())
        if ips:
            logger.info("Phase 3: ICMP Sweep …")
            sentinel.icmp_sweep(ips, timeout=1)

    inventory = sentinel.get_inventory()
    logger.info(f"Discovery complete — {len(inventory)} assets.")

    # Industrial
    if industrial and inventory:
        logger.info("Phase 4: Industrial Protocol Probing …")
        scanner = IndustrialScanner(inter_probe_delay=0.5)
        for asset in scanner.scan_targets(list(inventory.keys())):
            if asset.ip_address in inventory:
                inventory[asset.ip_address]["ot_protocol"] = asset.protocol
                inventory[asset.ip_address]["ot_device_info"] = asset.device_info

    # Compliance matrix
    logger.info("Phase 5: Dual-baseline NIST compliance matrix …")
    mapper = NISTMapper()
    df = mapper.generate_compliance_matrix(inventory)
    if not df.empty:
        report_file = "rca_first_run_audit.csv"
        mapper.export_report(report_file)
        summary = mapper.summary()
        console.print("\n[bold cyan]NIST 800-171 Compliance Matrix Summary[/bold cyan]")
        for rev, counts in summary.items():
            console.print(f"  {rev}: {counts}")
        console.print(f"\n  Full report → {report_file}")

    # Hardening
    if not no_hardening:
        logger.info("Phase 6: Local OS Hardening …")
        report = run_local_hardening()
        _print_hardening(report)

def _print_hardening(report):
    """Pretty-print a hardening report."""
    console.print(f"\n[bold yellow]Hardening Report — {report.hostname} ({report.os_type})[/bold yellow]")
    for r in report.results:
        color = "green" if r.status == "PASS" else "red"
        console.print(f"  [{color}]{r.status:4s}[/{color}] {r.check_name} (NIST {r.nist_control})")
        console.print(f"         {r.detail}")

# =========================================================================
# Subcommand: report
# =========================================================================
@app.command()
def report(
    client: str = typer.Option("Client", help="Client name for the report"),
    auditor: str = typer.Option("RCA Automated Auditor", help="Auditor name for the report"),
    csv: Optional[str] = typer.Option(None, help="Path to compliance CSV"),
    output: Optional[str] = typer.Option(None, help="Output PDF path")
):
    """Generate a Gap Analysis PDF from compliance data."""
    from soc.cemetery.auditor import AuditorAgent
    auditor_obj = AuditorAgent(client_name=client, auditor_name=auditor)
    csv_path = csv or "rca_first_run_audit.csv"
    pdf = auditor_obj.generate_report(csv_path, output_path=output)
    console.print(f"[bold green]Success:[/bold green] PDF report generated → {pdf}")

# =========================================================================
# Subcommand: patch
# =========================================================================
@app.command()
def patch(
    alerts: Optional[str] = typer.Option(None, help="Path to triage alerts JSON"),
    include_hardening: bool = typer.Option(False, help="Also draft scripts for local hardening failures")
):
    """Draft remediation scripts from alerts or hardening findings."""
    from soc.agents.patch_pilot import PatchPilotAgent
    from engine.core.detector import run_local_hardening

    pilot = PatchPilotAgent()

    # Draft from triage alerts
    alerts_path = alerts or os.path.join("soc", "reports", "triage_alerts.json")
    if os.path.exists(alerts_path):
        pilot.draft_from_alerts(alerts_path)

    # Draft from local hardening failures
    if include_hardening:
        report_data = run_local_hardening()
        results = [
            {
                "check_name": r.check_name,
                "nist_control": r.nist_control,
                "os_target": r.os_target,
                "status": r.status,
                "detail": r.detail,
            }
            for r in report_data.results
        ]
        pilot.draft_from_hardening(results)

    manifest = pilot.write_manifest()
    pending = pilot.list_pending()
    console.print("\n[bold yellow]Patch Pilot — Drafted Scripts[/bold yellow]")
    for d in pending:
        console.print(f"  [{d.status}] {d.patch_id} — {d.title}")
        console.print(f"             {d.filepath}")
    console.print(f"\n  Manifest → {manifest}")
    console.print("[italic]Note: Scripts require human approval before execution.[/italic]")

# =========================================================================
# Subcommand: start
# =========================================================================
@app.command()
def start(
    agent: str = typer.Argument(..., help="Agent to start: scout, triage, responder, governor, communicator, or api")
):
    """Start a specific SOC agent or the API layer."""
    if agent == "scout":
        from soc.agents.scout import ScoutAgent
        config_path = os.path.join("soc", "configs", "scout_config.json")
        agent_obj = ScoutAgent(config_path=config_path)
        asyncio.run(agent_obj.start())
    
    elif agent == "triage":
        from soc.agents.triage import TriageAgent
        agent_obj = TriageAgent()
        logger.info("Triage agent starting in polling loop...")
        while True:
            count = agent_obj.run_cycle()
            if count > 0:
                logger.info(f"Cycle complete: {count} alerts generated.")
            time.sleep(10)
            
    elif agent == "responder":
        from soc.agents.responder import ResponderAgent
        agent_obj = ResponderAgent()
        logger.info("Responder agent starting in polling loop...")
        while True:
            count = agent_obj.run_cycle()
            if count > 0:
                logger.info(f"Cycle complete: {count} new actions drafted.")
            time.sleep(10)
            
    elif agent == "api":
        import uvicorn
        logger.info("Starting SOC API at http://127.0.0.1:8000")
        uvicorn.run("soc.api.main:app", host="0.0.0.0", port=8000, reload=True)
        
    elif agent == "orchestrate":
        from soc.agents.orchestrator import OrchestratorAgent
        orchestrator = OrchestratorAgent()
        asyncio.run(orchestrator.start_async())

    elif agent == "correlator":
        from soc.agents.correlator import CorrelatorAgent
        agent_obj = CorrelatorAgent()
        asyncio.run(agent_obj.run())

    elif agent == "vanguard":
        from soc.agents.vanguard import VanguardAgent
        agent_obj = VanguardAgent()
        asyncio.run(agent_obj.run())

    elif agent == "watchdog":
        from soc.agents.watchdog import WatchdogAgent
        agent_obj = WatchdogAgent()
        asyncio.run(agent_obj.run())

    elif agent == "log-guardian":
        from soc.agents.log_guardian import LogGuardianAgent
        agent_obj = LogGuardianAgent()
        asyncio.run(agent_obj.run())

    elif agent == "cloud-wraith":
        from soc.agents.cloud_wraith import CloudWraithAgent
        agent_obj = CloudWraithAgent()
        asyncio.run(agent_obj.run())

    elif agent == "mirage":
        from soc.agents.mirage import MirageAgent
        agent_obj = MirageAgent()
        asyncio.run(agent_obj.run())

    elif agent == "hunter":
        from soc.agents.hunter import HunterAgent
        agent_obj = HunterAgent()
        asyncio.run(agent_obj.run())

    elif agent == "red-team":
        from soc.agents.red_team import RedTeamAgent
        agent_obj = RedTeamAgent()
        asyncio.run(agent_obj.run())

    elif agent == "traffic-sieve":
        from soc.agents.traffic_sieve import TrafficSieveAgent
        agent_obj = TrafficSieveAgent()
        asyncio.run(agent_obj.run())

    elif agent == "gatekeeper":
        from soc.agents.gatekeeper import GatekeeperAgent
        agent_obj = GatekeeperAgent()
        asyncio.run(agent_obj.run())

    elif agent == "dispatch":
        from soc.cemetery.dispatch import DispatchAgent
        agent_obj = DispatchAgent()
        asyncio.run(agent_obj.run())

    elif agent == "narrator":
        from soc.cemetery.narrator import NarratorAgent
        agent_obj = NarratorAgent()
        asyncio.run(agent_obj.run())

    elif agent == "risk-quantifier":
        from soc.cemetery.risk_quantifier import RiskQuantifierAgent
        agent_obj = RiskQuantifierAgent()
        asyncio.run(agent_obj.run())

    elif agent == "policy-architect":
        from soc.cemetery.policy_architect import PolicyArchitectAgent
        agent_obj = PolicyArchitectAgent()
        asyncio.run(agent_obj.run())

    elif agent == "governor":
        from soc.agents.governor import GovernorAgent
        agent_obj = GovernorAgent()
        asyncio.run(agent_obj.run())

    elif agent == "communicator":
        from soc.agents.communicator import CommunicatorAgent
        agent_obj = CommunicatorAgent()
        asyncio.run(agent_obj.run())

    elif agent == "librarian":
        from soc.agents.librarian import LibrarianAgent
        agent_obj = LibrarianAgent()
        asyncio.run(agent_obj.run())

    elif agent == "malware-pathologist":
        from soc.agents.malware_pathologist import MalwarePathologistAgent
        agent_obj = MalwarePathologistAgent()
        asyncio.run(agent_obj.run())
        
    # --- Distributed Workflow Entrypoints ---
    elif agent == "specialist-ot":
        from soc.agents.specialists import OTSecurityAnalyst
        worker = OTSecurityAnalyst()
        worker.start()
        
    elif agent == "specialist-net":
        from soc.agents.specialists import NetworkBehaviorAnalyst
        worker = NetworkBehaviorAnalyst()
        worker.start()
        
    elif agent == "specialist-id":
        from soc.agents.specialists import IdentityAccessAnalyst
        worker = IdentityAccessAnalyst()
        worker.start()
        
    elif agent == "specialist-fix":
        from soc.agents.specialists import RemediationAnalyst
        worker = RemediationAnalyst()
        worker.start()
        
    elif agent == "specialist-cloud":
        from soc.agents.specialists import CloudWraith
        worker = CloudWraith()
        worker.start()

    elif agent == "specialist-lab":
        from soc.agents.specialists import MalwarePathologist
        worker = MalwarePathologist()
        worker.start()

    elif agent == "specialist-hunt":
        from soc.agents.specialists import ThreatHunter
        worker = ThreatHunter()
        worker.start()
        
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown agent '{agent}'")
        raise typer.Exit(code=1)

# =========================================================================
# Subcommand: list
# =========================================================================
@app.command(name="list")
def list_resources(
    resource: str = typer.Argument(..., help="Resource to list: inventory, alerts, or pending")
):
    """Pretty-print SOC state (inventory, alerts, pending actions)."""
    from soc.api.main import get_inventory, get_alerts, get_pending_actions
    import asyncio

    async def _fetch():
        if resource == "inventory":
            data = await get_inventory()
            table = Table(title="SOC Asset Inventory")
            table.add_column("IP", style="cyan")
            table.add_column("MAC", style="magenta")
            table.add_column("Method")
            table.add_column("OT Info")
            
            # Handle empty inventory
            if not data:
                console.print(table)
                console.print("[dim]Inventory is empty.[/dim]")
                return

            if isinstance(data, dict):
                for ip, details in data.items():
                    table.add_row(ip, details.get("mac_address", ""), details.get("discovery_method", ""), details.get("ot_protocol", "N/A"))
            console.print(table)
            
        elif resource == "alerts":
            data = await get_alerts()
            table = Table(title="Triage Alerts")
            table.add_column("Severity", style="bold")
            table.add_column("IP", style="cyan")
            table.add_column("Rule")
            table.add_column("Description")
            
            if not data:
                console.print(table)
                console.print("[dim]No alerts in triage log.[/dim]")
                return

            for a in data:
                color = "red" if a["severity"] == "CRITICAL" else "yellow" if a["severity"] == "WARNING" else "white"
                table.add_row(f"[{color}]{a['severity']}[/{color}]", a["source_ip"], a["rule_name"], a["description"])
            console.print(table)
            
        elif resource == "pending":
            data = await get_pending_actions()
            table = Table(title="Pending Containment Actions")
            table.add_column("ID", style="dim")
            table.add_column("Target", style="cyan")
            table.add_column("Strategy", style="bold yellow")
            table.add_column("Status")
            
            if not data:
                console.print(table)
                console.print("[dim]No pending actions awaiting approval.[/dim]")
                return

            for act in data:
                table.add_row(act["id"], act["target_ip"], act["strategy"], act["status"])
            console.print(table)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown resource '{resource}'")

    asyncio.run(_fetch())

# =========================================================================
# Subcommand: usage
# =========================================================================
@app.command()
def usage():
    """Generate a 30-day activity summary for billing and site health."""
    from soc.api.main import get_inventory, get_alerts, get_pending_actions
    from soc.bus.event_queue import EventBus
    
    async def _gather():
        inv = await get_inventory()
        alerts = await get_alerts()
        pending = await get_pending_actions()
        
        # In a real app, we'd also check archived_actions.json
        archive_path = os.path.join("soc", "reports", "incidents", "archived_actions.json")
        archived_count = 0
        if os.path.exists(archive_path):
            with open(archive_path, "r") as f:
                archived_count = len(json.load(f))

        # --- BILLING HOOK: Calculate token telemetry ---
        total_tokens = 0
        bus = EventBus("business_intel")
        
        def _parse_event(filepath):
            try:
                with open(filepath, "r") as fh:
                    storage_obj = json.load(fh)
                if storage_obj.get("secure"):
                    if not bus.cipher:
                        return None
                    decrypted_json = bus.cipher.decrypt(storage_obj["payload"].encode())
                    return json.loads(decrypted_json)
                else:
                    return storage_obj["payload"]
            except Exception:
                return None

        # Scan active and processed queues for billing telemetry
        for directory in [bus.channel_dir, bus.processed_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.startswith("event_") and filename.endswith(".json"):
                        path = os.path.join(directory, filename)
                        payload = _parse_event(path)
                        if payload and "total_tokens" in payload:
                            total_tokens += payload["total_tokens"]

        # Estimate cost (e.g. blended rate of $0.01 per 1000 tokens)
        cost_estimate = (total_tokens / 1000.0) * 0.01

        table = Table(title="RCA Site Usage Report (Monthly Summary)")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("Total Assets Managed", str(len(inv)))
        table.add_row("Security Alerts Triaged", str(len(alerts)))
        table.add_row("Actions Awaiting Approval", str(len(pending)))
        table.add_row("Total Remediations Executed", str(archived_count))
        table.add_row("LLM Tokens (Tokens per Client)", f"{total_tokens:,}")
        table.add_row("Estimated Token Cost", f"${cost_estimate:.2f}")
        
        console.print(table)
        console.print("[dim italic]Report generated for billing period ending today.[/dim italic]")

    asyncio.run(_gather())

# =========================================================================
# Subcommand: backup
# =========================================================================
@app.command()
def backup(output: str = typer.Option("rca_backup.zip", help="Output zip filename")):
    """Archive all SOC reports and bus history for disaster recovery."""
    soc_dir = "soc"
    if not os.path.exists(soc_dir):
        console.print("[bold red]Error:[/bold red] SOC directory not found.")
        return

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(soc_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.join(soc_dir, "..")))

    console.print(f"[bold green]Success:[/bold green] SOC backup created → {output}")

# =========================================================================
# Subcommand: approve
# =========================================================================
@app.command()
def approve(action_id: str = typer.Argument(..., help="ID of the action to approve")):
    """Approve a pending containment action by its ID (requires Vault secret)."""
    from soc.agents.responder import ResponderAgent
    from soc.security.vault import Vault
    from soc.bootstrap import get_soc_path
    from soc.security.crypto_cat import sign_action
    
    vault = Vault(get_soc_path("configs", "secrets.json"), role="admin")
    admin_secret = vault.load().get("api_secret_key", "")
    
    cat_signature = sign_action(action_id, admin_secret)
    responder = ResponderAgent()
    
    if responder.approve_action(action_id, cat_signature):
        console.print(f"[bold green]Success:[/bold green] Action {action_id} APPROVED via CAT signature and archived.")
    else:
        console.print(f"[bold red]Error:[/bold red] Action approval REJECTED. Invalid CAT or action not found.")

if __name__ == "__main__":
    app()
