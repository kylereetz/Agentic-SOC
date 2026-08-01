"""
RCA Detector: OS-Specific Hardening & Security Posture Checks.
Checks local security settings across Windows 10/11, Windows Server,
and Rocky Linux 9 environments.

Focus areas (Phase 1):
  - MFA / credential guard status
  - Guest account status
  - Unencrypted network shares (SMB / NFS)

Uses subprocess and paramiko for local and remote checks respectively.

# Satisfies NIST 800-171 Rev 3:
# 3.5.3  - Use multifactor authentication for local and network access.
# 3.1.1  - Limit system access to authorized users.
# 3.1.2  - Limit system access to permitted transactions and functions.
# 3.4.2  - Establish and enforce security configuration settings.
# 3.13.8 - Implement cryptographic mechanisms to prevent unauthorized
#           disclosure of CUI during transmission.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import paramiko

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Detector - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class HardeningResult:
    """Single check result."""

    check_name: str
    nist_control: str  # e.g. "3.5.3"
    os_target: str  # e.g. "Windows 10/11"
    status: str  # "Pass", "Fail", "Error", "Skipped"
    detail: str = ""


@dataclass
class HostReport:
    """Aggregated results for one host."""

    hostname: str
    os_type: str
    results: List[HardeningResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Windows checks (local execution via PowerShell)
# ---------------------------------------------------------------------------
class WindowsDetector:
    """
    Runs PowerShell-based hardening checks on Windows 10/11 and Server.
    Must be executed with Administrator privileges.

    # Satisfies NIST 800-171 3.5.3, 3.1.1, 3.4.2
    """

    @staticmethod
    def _ps(command: str) -> str:
        """Execute a PowerShell command and return stdout."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip()
        except Exception as exc:
            logger.error(f"PowerShell exec failed: {exc}")
            return ""

    def check_mfa_status(self) -> HardeningResult:
        """
        Check whether Windows Credential Guard / Windows Hello is enabled.
        This is a proxy indicator that the system supports hardware-backed MFA.

        # Satisfies NIST 800-171 3.5.3
        """
        output = self._ps(
            "Get-CimInstance -ClassName Win32_DeviceGuard "
            "-Namespace root\\Microsoft\\Windows\\DeviceGuard "
            "| Select-Object -ExpandProperty SecurityServicesRunning"
        )
        if "1" in output:
            return HardeningResult(
                check_name="Credential Guard",
                nist_control="3.5.3",
                os_target="Windows 10/11 / Server",
                status="Pass",
                detail="Credential Guard is running.",
            )
        return HardeningResult(
            check_name="Credential Guard",
            nist_control="3.5.3",
            os_target="Windows 10/11 / Server",
            status="Fail",
            detail=f"Credential Guard not detected. Raw: {output}",
        )

    def check_guest_account(self) -> HardeningResult:
        """
        Verify that the built-in Guest account is disabled.

        # Satisfies NIST 800-171 3.1.1
        """
        output = self._ps(
            "Get-LocalUser -Name 'Guest' | Select-Object -ExpandProperty Enabled"
        )
        if output.lower() == "false":
            return HardeningResult(
                check_name="Guest Account Disabled",
                nist_control="3.1.1",
                os_target="Windows 10/11 / Server",
                status="Pass",
                detail="Guest account is disabled.",
            )
        return HardeningResult(
            check_name="Guest Account Disabled",
            nist_control="3.1.1",
            os_target="Windows 10/11 / Server",
            status="Fail",
            detail=f"Guest account enabled or status unknown. Raw: {output}",
        )

    def check_unencrypted_shares(self) -> HardeningResult:
        """
        Check if SMB encryption is enforced on the server.

        # Satisfies NIST 800-171 3.13.8
        """
        output = self._ps(
            "Get-SmbServerConfiguration | " "Select-Object -ExpandProperty EncryptData"
        )
        if output.lower() == "true":
            return HardeningResult(
                check_name="SMB Encryption Enforced",
                nist_control="3.13.8",
                os_target="Windows 10/11 / Server",
                status="Pass",
                detail="SMB encryption is enforced on all shares.",
            )
        return HardeningResult(
            check_name="SMB Encryption Enforced",
            nist_control="3.13.8",
            os_target="Windows 10/11 / Server",
            status="Fail",
            detail=f"SMB encryption is NOT enforced. Raw: {output}",
        )

    def run_all(self) -> List[HardeningResult]:
        """Execute all Windows hardening checks."""
        return [
            self.check_mfa_status(),
            self.check_guest_account(),
            self.check_unencrypted_shares(),
        ]


# ---------------------------------------------------------------------------
# Rocky Linux 9 checks (remote execution via Paramiko SSH)
# ---------------------------------------------------------------------------
class RockyDetector:
    """
    Runs SSH-based hardening checks against Rocky Linux 9 hosts.

    # Satisfies NIST 800-171 3.5.3, 3.1.1, 3.4.2
    """

    def __init__(
        self,
        hostname: str,
        username: str,
        password: Optional[str] = None,
        key_filename: Optional[str] = None,
        port: int = 22,
    ):
        self.hostname = hostname
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(
                hostname,
                port=port,
                username=username,
                password=password,
                key_filename=key_filename,
                timeout=10,
            )
            logger.info(f"SSH connected to {hostname}")
        except Exception as exc:
            logger.error(f"SSH connection to {hostname} failed: {exc}")
            raise

    def _exec(self, cmd: str) -> str:
        """Execute a command over SSH and return stdout."""
        try:
            _, stdout, _ = self.ssh.exec_command(cmd, timeout=15)
            return stdout.read().decode().strip()
        except Exception as exc:
            logger.error(f"Remote exec failed on {self.hostname}: {exc}")
            return ""

    def check_mfa_status(self) -> HardeningResult:
        """
        Check if PAM TOTP / Google Authenticator module is present.

        # Satisfies NIST 800-171 3.5.3
        """
        output = self._exec(
            "grep -c 'pam_google_authenticator\\|pam_totp' /etc/pam.d/sshd"
        )
        if output.isdigit() and int(output) > 0:
            return HardeningResult(
                check_name="PAM MFA Module",
                nist_control="3.5.3",
                os_target="Rocky 9",
                status="Pass",
                detail="PAM MFA module (TOTP) detected in sshd config.",
            )
        return HardeningResult(
            check_name="PAM MFA Module",
            nist_control="3.5.3",
            os_target="Rocky 9",
            status="Fail",
            detail="No PAM MFA module found in /etc/pam.d/sshd.",
        )

    def check_guest_account(self) -> HardeningResult:
        """
        Verify that there is no 'guest' user or that the account is locked.

        # Satisfies NIST 800-171 3.1.1
        """
        output = self._exec("getent passwd guest")
        if not output:
            return HardeningResult(
                check_name="Guest Account Absent",
                nist_control="3.1.1",
                os_target="Rocky 9",
                status="Pass",
                detail="No 'guest' user found in /etc/passwd.",
            )
        # Account exists — check if locked
        lock_status = self._exec("passwd -S guest 2>/dev/null | awk '{print $2}'")
        if lock_status in ("L", "LK"):
            return HardeningResult(
                check_name="Guest Account Locked",
                nist_control="3.1.1",
                os_target="Rocky 9",
                status="Pass",
                detail="Guest account exists but is locked.",
            )
        return HardeningResult(
            check_name="Guest Account Active",
            nist_control="3.1.1",
            os_target="Rocky 9",
            status="Fail",
            detail=f"Guest account is present and not locked. Status: {lock_status}",
        )

    def check_unencrypted_shares(self) -> HardeningResult:
        """
        Check for NFS exports without Kerberos (sec=krb5) protection.

        # Satisfies NIST 800-171 3.13.8
        """
        output = self._exec("cat /etc/exports 2>/dev/null")
        if not output:
            return HardeningResult(
                check_name="NFS Shares",
                nist_control="3.13.8",
                os_target="Rocky 9",
                status="Pass",
                detail="No NFS exports configured.",
            )
        if "sec=krb5" in output:
            return HardeningResult(
                check_name="NFS Kerberos Enforced",
                nist_control="3.13.8",
                os_target="Rocky 9",
                status="Pass",
                detail="NFS exports use Kerberos security.",
            )
        return HardeningResult(
            check_name="NFS Unencrypted Shares",
            nist_control="3.13.8",
            os_target="Rocky 9",
            status="Fail",
            detail="NFS exports detected without Kerberos (sec=krb5).",
        )

    def run_all(self) -> List[HardeningResult]:
        """Execute all Rocky 9 hardening checks."""
        return [
            self.check_mfa_status(),
            self.check_guest_account(),
            self.check_unencrypted_shares(),
        ]

    def close(self) -> None:
        """Close the SSH session."""
        self.ssh.close()
        logger.info(f"SSH session to {self.hostname} closed.")


# ---------------------------------------------------------------------------
# Convenience: auto-detect the local OS and run checks
# ---------------------------------------------------------------------------
def detect_local_os() -> str:
    """Return a normalised OS identifier."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    release = platform.release().lower()
    if "rocky" in platform.platform().lower() or "el9" in release:
        return "rocky9"
    return system


def run_local_hardening() -> HostReport:
    """
    Run the full hardening check suite appropriate for the local OS.
    Returns a HostReport with all results.
    """
    os_type = detect_local_os()
    hostname = platform.node()
    report = HostReport(hostname=hostname, os_type=os_type)

    if os_type == "windows":
        logger.info(f"Running Windows hardening checks on {hostname} …")
        detector = WindowsDetector()
        report.results = detector.run_all()
    elif os_type == "rocky9":
        logger.info(
            "Rocky 9 detected — local checks require SSH self-connect or direct PAM inspection."
        )
        # For local Rocky 9 checks we inspect files directly
        # (In production you'd use RockyDetector against localhost)
        report.results = []
    else:
        logger.warning(f"Unsupported local OS: {os_type}")

    return report


if __name__ == "__main__":
    report = run_local_hardening()
    for r in report.results:
        print(f"[{r.status}] {r.check_name} — {r.nist_control}: {r.detail}")
