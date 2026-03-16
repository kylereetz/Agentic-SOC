"""
RCA Patch Pilot: Remediation Script Drafter.
Consumes Triage alerts and Auditor gap data, then drafts targeted
PowerShell (Windows) or Bash (Rocky 9 / Linux) remediation scripts.

**CRITICAL SAFETY CONSTRAINT**: Scripts are NEVER auto-executed.
They are saved to `drafts/` with status PENDING_APPROVAL and require
explicit human approval before execution.

Each drafted script includes:
  - Header comment with vulnerability description and NIST control ref
  - Fix commands
  - Rollback section
  - Approval metadata

# Satisfies NIST 800-171 Rev 3:
# 3.4.3  - Track, review, approve, and log changes.
# 3.4.4  - Analyse the security impact of changes prior to implementation.
# 3.14.1 - Identify, report, and correct system flaws in a timely manner.
# 3.12.2 - Develop plans of action to correct deficiencies.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Patch Pilot - %(message)s",
)
logger = logging.getLogger(__name__)

_DRAFTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "drafts")
_REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class PatchDraft:
    """Represents a single drafted remediation script."""
    patch_id: str
    title: str
    target_os: str              # "windows" or "linux"
    nist_control: str
    finding_description: str
    script_content: str
    rollback_content: str
    target_host: str = "unknown"
    status: str = "PENDING_APPROVAL"
    filepath: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ---------------------------------------------------------------------------
# Script templates
# ---------------------------------------------------------------------------
_PS_TEMPLATE = '''# ===========================================================================
# RCA Patch Pilot — Remediation Script (PowerShell)
# ===========================================================================
# Patch ID   : {patch_id}
# Title      : {title}
# NIST Control: {nist_control}
# Finding    : {finding}
# Generated  : {timestamp}
# Status     : PENDING_APPROVAL — DO NOT EXECUTE WITHOUT HUMAN APPROVAL
# ===========================================================================

# ---- PRE-FLIGHT CHECK ----
Write-Host "[RCA_EVENT] {{ 'task': 'preflight', 'status': 'starting', 'title': '{title}' }}"
{idempotency_guard}

# ---- FIX ----
Write-Host "[RCA_EVENT] {{ 'task': 'fix', 'status': 'executing' }}"
{fix_commands}

# ---- VERIFICATION ----
Write-Host "[RCA_EVENT] {{ 'task': 'verify', 'status': 'executing' }}"
{verify_commands}

Write-Host "[RCA_EVENT] {{ 'task': 'complete', 'status': 'success' }}"
Write-Host "[RCA Patch Pilot] Remediation complete. Please verify manually."
'''

_PS_ROLLBACK_TEMPLATE = '''# ===========================================================================
# RCA Patch Pilot — ROLLBACK Script (PowerShell)
# ===========================================================================
# Patch ID   : {patch_id}
# Title      : ROLLBACK — {title}
# ===========================================================================

Write-Host "[RCA Patch Pilot] Rolling back: {title}"

{rollback_commands}

Write-Host "[RCA Patch Pilot] Rollback complete."
'''

_BASH_TEMPLATE = '''#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — Remediation Script (Bash)
# ===========================================================================
# Patch ID   : {patch_id}
# Title      : {title}
# NIST Control: {nist_control}
# Finding    : {finding}
# Generated  : {timestamp}
# Status     : PENDING_APPROVAL — DO NOT EXECUTE WITHOUT HUMAN APPROVAL
# ===========================================================================
set -euo pipefail

# ---- PRE-FLIGHT CHECK ----
echo "[RCA_EVENT] {{ \\"task\\": \\"preflight\\", \\"status\\": \\"starting\\", \\"title\\": \\"{title}\\" }}"
{idempotency_guard}

# ---- FIX ----
echo "[RCA_EVENT] {{ \\"task\\": \\"fix\\", \\"status\\": \\"executing\\" }}"
{fix_commands}

# ---- VERIFICATION ----
echo "[RCA_EVENT] {{ \\"task\\": \\"verify\\", \\"status\\": \\"executing\\" }}"
{verify_commands}

echo "[RCA_EVENT] {{ \\"task\\": \\"complete\\", \\"status\\": \\"success\\" }}"
echo "[RCA Patch Pilot] Remediation complete. Please verify manually."
'''

_BASH_ROLLBACK_TEMPLATE = '''#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — ROLLBACK Script (Bash)
# ===========================================================================
# Patch ID   : {patch_id}
# Title      : ROLLBACK — {title}
# ===========================================================================
set -euo pipefail

echo "[RCA_EVENT] {{ \\"task\\": \\"rollback\\", \\"status\\": \\"executing\\", \\"title\\": \\"{title}\\" }}"

{rollback_commands}

echo "[RCA_EVENT] {{ \\"task\\": \\"rollback\\", \\"status\\": \\"success\\" }}"
'''


# ---------------------------------------------------------------------------
# Known remediation library
# ---------------------------------------------------------------------------
# Maps (nist_control, finding_keyword) → remediation templates
REMEDIATION_LIBRARY: Dict[str, Dict[str, Any]] = {
    # --- Windows: Credential Guard / MFA ---
    "windows_mfa": {
        "title": "Enable Credential Guard",
        "nist_control": "3.5.3",
        "target_os": "windows",
        "guard_cmd": "if ((Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\\Microsoft\\Windows\\DeviceGuard).SecurityServicesRunning -contains 1) { Write-Host '[RCA_EVENT] { \"task\": \"preflight\", \"status\": \"skipped\", \"reason\": \"already_enabled\" }'; exit 0 }",
        "fix_commands": (
            "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard' "
            "-Name 'EnableVirtualizationBasedSecurity' -Value 1 -Type DWord\n"
            "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' "
            "-Name 'LsaCfgFlags' -Value 1 -Type DWord"
        ),
        "verify_commands": (
            "Get-CimInstance -ClassName Win32_DeviceGuard "
            "-Namespace root\\Microsoft\\Windows\\DeviceGuard "
            "| Select-Object SecurityServicesRunning"
        ),
        "rollback_commands": (
            "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard' "
            "-Name 'EnableVirtualizationBasedSecurity' -Value 0 -Type DWord\n"
            "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' "
            "-Name 'LsaCfgFlags' -Value 0 -Type DWord\n"
            "Write-Host 'Reboot required to fully disable Credential Guard.'"
        ),
    },
    # --- Windows: Guest Account ---
    "windows_guest": {
        "title": "Disable Guest Account",
        "nist_control": "3.1.1",
        "target_os": "windows",
        "guard_cmd": "if ((Get-LocalUser -Name 'Guest').Enabled -eq $false) { Write-Host '[RCA_EVENT] { \"task\": \"preflight\", \"status\": \"skipped\", \"reason\": \"already_disabled\" }'; exit 0 }",
        "fix_commands": "Disable-LocalUser -Name 'Guest'",
        "verify_commands": (
            "Get-LocalUser -Name 'Guest' | Select-Object Name, Enabled"
        ),
        "rollback_commands": "Enable-LocalUser -Name 'Guest'",
    },
    # --- Windows: SMB Encryption ---
    "windows_smb": {
        "title": "Enforce SMB Encryption",
        "nist_control": "3.13.8",
        "target_os": "windows",
        "fix_commands": "Set-SmbServerConfiguration -EncryptData $true -Force",
        "verify_commands": (
            "Get-SmbServerConfiguration | Select-Object EncryptData"
        ),
        "rollback_commands": "Set-SmbServerConfiguration -EncryptData $false -Force",
    },
    # --- Linux: PAM MFA ---
    "linux_mfa": {
        "title": "Configure PAM TOTP (Google Authenticator)",
        "nist_control": "3.5.3",
        "target_os": "linux",
        "variants": {
            "rocky": {
                "fix_commands": "dnf install -y google-authenticator\nsystemctl restart sshd",
                "guard_cmd": "if rpm -q google-authenticator; then echo 'already_installed'; exit 0; fi"
            },
            "ubuntu": {
                "fix_commands": "apt-get update && apt-get install -y libpam-google-authenticator\nsystemctl restart ssh",
                "guard_cmd": "if dpkg -l | grep -q google-authenticator; then echo 'already_installed'; exit 0; fi"
            }
        },
        "fix_commands": "dnf install -y google-authenticator", # Fallback
        "verify_commands": "grep 'pam_google_authenticator' /etc/pam.d/sshd",
        "rollback_commands": "sed -i '/pam_google_authenticator/d' /etc/pam.d/sshd",
    },
    # --- Rocky 9: Guest Account ---
    "linux_guest": {
        "title": "Lock Guest Account",
        "nist_control": "3.1.1",
        "target_os": "linux",
        "guard_cmd": "if ! grep -q 'guest:[!|*]' /etc/shadow; then echo '[RCA_EVENT] { \"task\": \"preflight\", \"status\": \"skipped\", \"reason\": \"already_locked\" }'; exit 0; fi",
        "fix_commands": (
            "# Lock the guest account if it exists\n"
            "id guest &>/dev/null && usermod -L guest || echo 'No guest account found.'"
        ),
        "verify_commands": "passwd -S guest 2>/dev/null || echo 'No guest user'",
        "rollback_commands": "usermod -U guest",
    },
    # --- Rocky 9: NFS Kerberos ---
    "linux_nfs": {
        "title": "Enforce Kerberos on NFS Exports",
        "nist_control": "3.13.8",
        "target_os": "linux",
        "fix_commands": (
            "# Replace insecure NFS exports with Kerberos-secured versions\n"
            "sed -i 's/sec=sys/sec=krb5p/g' /etc/exports\n"
            "exportfs -ra"
        ),
        "verify_commands": "cat /etc/exports | grep 'sec=krb5'",
        "rollback_commands": (
            "sed -i 's/sec=krb5p/sec=sys/g' /etc/exports\n"
            "exportfs -ra"
        ),
    },
}


# ---------------------------------------------------------------------------
# Patch Pilot Agent
# ---------------------------------------------------------------------------
class PatchPilotAgent:
    """
    Drafts remediation scripts based on Triage alerts and Detector findings.
    NEVER auto-executes — all scripts require human approval.

    # Satisfies NIST 800-171 3.4.3 and 3.14.1
    """

    def __init__(self):
        os.makedirs(_DRAFTS_DIR, exist_ok=True)
        self.drafts: List[PatchDraft] = []

    def draft_from_alerts(
        self, alerts_path: Optional[str] = None
    ) -> List[PatchDraft]:
        """
        Read triage alerts and generate remediation scripts for
        actionable findings.
        """
        if alerts_path is None:
            alerts_path = os.path.join(_REPORT_DIR, "triage_alerts.json")

        try:
            with open(alerts_path, "r") as fh:
                alerts = json.load(fh)
        except FileNotFoundError:
            logger.warning(f"No alerts file at {alerts_path}")
            return []

        for alert in alerts:
            if alert.get("severity") in ("WARNING", "CRITICAL"):
                self._draft_for_finding(alert)

        return self.drafts

    def draft_from_hardening(
        self, results: List[Dict[str, Any]]
    ) -> List[PatchDraft]:
        """
        Generate remediation scripts from RCADetector hardening results.
        Only drafts for findings with status 'Fail'.
        """
        for result in results:
            if result.get("status") == "Fail":
                self._draft_for_hardening_finding(result)
        return self.drafts

    def _draft_for_finding(self, alert: Dict[str, Any]) -> None:
        """Map an alert to a known remediation and draft the script."""
        nist = alert.get("nist_control", "")
        desc = alert.get("description", "").lower()

        # Try to match to a known remediation
        remediation_key = self._match_remediation(nist, desc)
        if remediation_key and remediation_key in REMEDIATION_LIBRARY:
            self._generate_script(
                REMEDIATION_LIBRARY[remediation_key],
                finding_description=alert.get("description", ""),
                target_host=alert.get("ip_address", "unknown")
            )

    def _draft_for_hardening_finding(
        self, result: Dict[str, Any]
    ) -> None:
        """Map a hardening check failure to a remediation."""
        nist = result.get("nist_control", "")
        check = result.get("check_name", "").lower()
        os_target = result.get("os_target", "").lower()

        key = None
        if "credential guard" in check or "mfa" in check:
            key = "windows_mfa" if "windows" in os_target else "linux_mfa"
        elif "guest" in check:
            key = "windows_guest" if "windows" in os_target else "linux_guest"
        elif "smb" in check or "encryption" in check:
            key = "windows_smb" if "windows" in os_target else "linux_nfs"

        if key and key in REMEDIATION_LIBRARY:
            self._generate_script(
                REMEDIATION_LIBRARY[key],
                finding_description=result.get("detail", ""),
                target_host=result.get("ip_address", "unknown")
            )

    def _match_remediation(
        self, nist_control: str, description: str
    ) -> Optional[str]:
        """Best-effort match of an alert to a remediation key."""
        for key, rem in REMEDIATION_LIBRARY.items():
            if rem["nist_control"] == nist_control:
                return key
        return None

    def _generate_script(
        self,
        remediation: Dict[str, Any],
        finding_description: str,
        target_host: str = "unknown",
    ) -> PatchDraft:
        """Create the actual script files and return a PatchDraft."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        patch_id = f"RCA-{ts}-{remediation['nist_control'].replace('.', '')}"
        title = remediation["title"]
        target_os = remediation["target_os"]

        # [IQ] Context-Aware Logic: Check for OS variants
        fix_cmds = remediation["fix_commands"]
        guard_cmd = remediation.get("guard_cmd", "")
        
        # Determine variant (simplified mockup)
        variant = "ubuntu" if "ubuntu" in finding_description.lower() else "rocky"
        if "variants" in remediation and variant in remediation["variants"]:
            fix_cmds = remediation["variants"][variant]["fix_commands"]
            guard_cmd = remediation["variants"][variant].get("guard_cmd", "")

        if target_os == "windows":
            ext = ".ps1"
            script = _PS_TEMPLATE.format(
                patch_id=patch_id,
                title=title,
                nist_control=remediation["nist_control"],
                finding=finding_description,
                timestamp=ts,
                idempotency_guard=guard_cmd,
                fix_commands=fix_cmds,
                verify_commands=remediation["verify_commands"],
            )
            rollback = _PS_ROLLBACK_TEMPLATE.format(
                patch_id=patch_id,
                title=title,
                rollback_commands=remediation["rollback_commands"],
            )
        else:
            ext = ".sh"
            script = _BASH_TEMPLATE.format(
                patch_id=patch_id,
                title=title,
                nist_control=remediation["nist_control"],
                finding=finding_description,
                timestamp=ts,
                idempotency_guard=guard_cmd,
                fix_commands=fix_cmds,
                verify_commands=remediation["verify_commands"],
            )
            rollback = _BASH_ROLLBACK_TEMPLATE.format(
                patch_id=patch_id,
                title=title,
                rollback_commands=remediation["rollback_commands"],
            )

        # Write fix script
        fix_path = os.path.join(_DRAFTS_DIR, f"{patch_id}_fix{ext}")
        with open(fix_path, "w", newline="\n") as fh:
            fh.write(script)

        # Write rollback script
        rb_path = os.path.join(_DRAFTS_DIR, f"{patch_id}_rollback{ext}")
        with open(rb_path, "w", newline="\n") as fh:
            fh.write(rollback)

        draft = PatchDraft(
            patch_id=patch_id,
            title=title,
            target_os=target_os,
            nist_control=remediation["nist_control"],
            finding_description=finding_description,
            script_content=script,
            rollback_content=rollback,
            target_host=target_host,
            filepath=fix_path,
        )
        self.drafts.append(draft)
        logger.info(
            f"[DRAFT] {patch_id} — {title} → {fix_path} "
            f"(STATUS: PENDING_APPROVAL)"
        )
        return draft

    def list_pending(self) -> List[PatchDraft]:
        """Return all drafts with PENDING_APPROVAL status."""
        return [d for d in self.drafts if d.status == "PENDING_APPROVAL"]

    def write_manifest(self) -> str:
        """
        [SQ] Write a JSON manifest of all drafts, grouped by host.
        """
        manifest_path = os.path.join(_DRAFTS_DIR, "manifest.json")
        
        # Group by host for parallel responder dispatch
        grouped_data: Dict[str, List[Dict[str, Any]]] = {}
        for d in self.drafts:
            if d.target_host not in grouped_data:
                grouped_data[d.target_host] = []
            grouped_data[d.target_host].append({
                "patch_id": d.patch_id,
                "title": d.title,
                "target_os": d.target_os,
                "nist_control": d.nist_control,
                "status": d.status,
                "filepath": d.filepath,
                "created_at": d.created_at,
            })

        with open(manifest_path, "w") as fh:
            json.dump(grouped_data, fh, indent=2)
        logger.info(f"Patch manifest (grouped) written → {manifest_path}")
        return manifest_path


if __name__ == "__main__":
    pilot = PatchPilotAgent()
    print("Patch Pilot loaded. Feed it alerts or hardening results to draft scripts.")
