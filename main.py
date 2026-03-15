"""
RCA Main Orchestrator: Unified Entry Point.
Coordinates all RCA modules and agents via CLI subcommands.

Subcommands:
  audit    — Run a First-Run Audit (discovery + compliance + hardening)
  scout    — Start the Scout agent (scheduled inventory loop)
  report   — Generate a Gap Analysis PDF from latest compliance data
  triage   — Classify latest Scout events (IT noise vs. OT threats)
  patch    — Draft remediation scripts from alerts / hardening findings

Usage examples:
  python main.py audit --audit-subnet 192.168.1.0/24 --industrial
  python main.py scout
  python main.py report --client "Acme Manufacturing"
  python main.py triage
  python main.py patch

# Satisfies NIST 800-171 3.12.1 (Security Assessments)
"""

import argparse
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Main - %(message)s",
)
logger = logging.getLogger(__name__)


# =========================================================================
# Subcommand: audit
# =========================================================================
def cmd_audit(args):
    """Run a First-Run Audit (Phase 2 capability)."""
    from engine.core.sentinel import SentinelEngine
    from engine.core.mapper import NISTMapper
    from engine.core.detector import run_local_hardening
    from engine.core.industrial import IndustrialScanner

    logger.info("=" * 60)
    logger.info("  Reetz Cyber Automation (RCA) — First-Run Audit")
    logger.info("=" * 60)

    if args.hardening_only:
        report = run_local_hardening()
        _print_hardening(report)
        return

    # Discovery
    sentinel = SentinelEngine()

    logger.info("Phase 1: Passive Sniffing (15s) …")
    sentinel.passive_sniffing(timeout=15)

    if args.audit_subnet:
        logger.info(f"Phase 2: ARP Sweep ({args.audit_subnet}) …")
        sentinel.active_arp_scan(
            target_subnet=args.audit_subnet, timeout=args.timeout
        )
        ips = list(sentinel.get_inventory().keys())
        if ips:
            logger.info("Phase 3: ICMP Sweep …")
            sentinel.icmp_sweep(ips, timeout=1)

    inventory = sentinel.get_inventory()
    logger.info(f"Discovery complete — {len(inventory)} assets.")

    # Industrial
    if args.industrial and inventory:
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
        print(f"\n{'='*50}")
        print("  NIST 800-171 Compliance Matrix Summary")
        print(f"{'='*50}")
        for rev, counts in summary.items():
            print(f"  {rev}: {counts}")
        print(f"\n  Full report → {report_file}")

    # Hardening
    if not args.no_hardening:
        logger.info("Phase 6: Local OS Hardening …")
        report = run_local_hardening()
        _print_hardening(report)


def _print_hardening(report):
    """Pretty-print a hardening report."""
    print(f"\n{'='*50}")
    print(f"  Hardening Report — {report.hostname} ({report.os_type})")
    print(f"{'='*50}")
    for r in report.results:
        print(f"  [{r.status:4s}] {r.check_name} (NIST {r.nist_control})")
        print(f"         {r.detail}")


# =========================================================================
# Subcommand: scout
# =========================================================================
def cmd_scout(args):
    """Start the Scout agent (scheduled inventory loop)."""
    from soc.agents.scout import ScoutAgent

    agent = ScoutAgent(
        config_path=args.config
        if args.config
        else os.path.join("soc", "configs", "scout_config.json")
    )
    if args.once:
        agent.run_once()
    else:
        agent.start()


# =========================================================================
# Subcommand: report
# =========================================================================
def cmd_report(args):
    """Generate a Gap Analysis PDF."""
    from soc.agents.auditor import AuditorAgent

    auditor = AuditorAgent(
        client_name=args.client,
        auditor_name=args.auditor,
    )
    csv_path = args.csv or "rca_first_run_audit.csv"
    pdf = auditor.generate_report(csv_path, output_path=args.output)
    print(f"PDF report generated → {pdf}")


# =========================================================================
# Subcommand: triage
# =========================================================================
def cmd_triage(args):
    """Classify the latest Scout events."""
    from soc.agents.triage import TriageAgent

    agent = TriageAgent(
        rules_path=args.rules
        if args.rules
        else os.path.join("soc", "configs", "triage_rules.json")
    )
    events_path = args.events or os.path.join(
        "soc", "reports", "inventory", "latest_events.json"
    )
    alerts = agent.process_event_file(events_path)
    summary = agent.summary(alerts)
    print(f"\n{'='*50}")
    print("  Triage Summary")
    print(f"{'='*50}")
    for sev, count in summary.items():
        print(f"  {sev}: {count}")
    print(f"  Total alerts: {len(alerts)}")


# =========================================================================
# Subcommand: patch
# =========================================================================
def cmd_patch(args):
    """Draft remediation scripts from alerts or hardening findings."""
    from soc.agents.patch_pilot import PatchPilotAgent
    from engine.core.detector import run_local_hardening

    pilot = PatchPilotAgent()

    # Draft from triage alerts
    alerts_path = args.alerts or os.path.join("soc", "reports", "triage_alerts.json")
    if os.path.exists(alerts_path):
        pilot.draft_from_alerts(alerts_path)

    # Draft from local hardening failures
    if args.include_hardening:
        report = run_local_hardening()
        results = [
            {
                "check_name": r.check_name,
                "nist_control": r.nist_control,
                "os_target": r.os_target,
                "status": r.status,
                "detail": r.detail,
            }
            for r in report.results
        ]
        pilot.draft_from_hardening(results)

    manifest = pilot.write_manifest()
    pending = pilot.list_pending()
    print(f"\n{'='*50}")
    print("  Patch Pilot — Drafted Scripts")
    print(f"{'='*50}")
    for d in pending:
        print(f"  [{d.status}] {d.patch_id} — {d.title}")
        print(f"             {d.filepath}")
    print(f"\n  Manifest → {manifest}")
    print("  ⚠ Scripts require human approval before execution.")


# =========================================================================
# Argument parser
# =========================================================================
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reetz Cyber Automation (RCA) — Agentic SOC Engine"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # audit
    p_audit = sub.add_parser("audit", help="Run a First-Run Audit")
    p_audit.add_argument("--audit-subnet", type=str)
    p_audit.add_argument("--timeout", type=int, default=5)
    p_audit.add_argument("--industrial", action="store_true")
    p_audit.add_argument("--no-hardening", action="store_true")
    p_audit.add_argument("--hardening-only", action="store_true")
    p_audit.set_defaults(func=cmd_audit)

    # scout
    p_scout = sub.add_parser("scout", help="Start the Scout agent")
    p_scout.add_argument("--config", type=str, help="Path to scout config JSON")
    p_scout.add_argument("--once", action="store_true", help="Run one cycle only")
    p_scout.set_defaults(func=cmd_scout)

    # report
    p_report = sub.add_parser("report", help="Generate Gap Analysis PDF")
    p_report.add_argument("--client", type=str, default="Client")
    p_report.add_argument("--auditor", type=str, default="RCA Automated Auditor")
    p_report.add_argument("--csv", type=str, help="Path to compliance CSV")
    p_report.add_argument("--output", type=str, help="Output PDF path")
    p_report.set_defaults(func=cmd_report)

    # triage
    p_triage = sub.add_parser("triage", help="Classify Scout events")
    p_triage.add_argument("--rules", type=str, help="Path to triage rules JSON")
    p_triage.add_argument("--events", type=str, help="Path to events JSON")
    p_triage.set_defaults(func=cmd_triage)

    # patch
    p_patch = sub.add_parser("patch", help="Draft remediation scripts")
    p_patch.add_argument("--alerts", type=str, help="Path to triage alerts JSON")
    p_patch.add_argument(
        "--include-hardening",
        action="store_true",
        help="Also draft scripts for local hardening failures",
    )
    p_patch.set_defaults(func=cmd_patch)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    start = time.time()
    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as exc:
        logger.error(f"Command failed: {exc}")
    finally:
        logger.info(f"Total execution time: {time.time() - start:.2f}s")
