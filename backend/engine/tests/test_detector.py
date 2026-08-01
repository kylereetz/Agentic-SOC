"""
Tests for engine.core.detector — WindowsDetector / run_local_hardening
subprocess.run is mocked; no real PowerShell commands are executed.
"""

import unittest
from unittest.mock import MagicMock, patch

from engine.core.detector import (
    WindowsDetector,
    HardeningResult,
    HostReport,
    run_local_hardening,
    detect_local_os,
)


def _make_ps_result(stdout: str) -> MagicMock:
    """Build a mock CompletedProcess with the given stdout string."""
    result = MagicMock()
    result.stdout = stdout
    result.returncode = 0
    return result


class TestWindowsDetectorCredentialGuard(unittest.TestCase):

    @patch("engine.core.detector.subprocess.run")
    def test_credential_guard_pass(self, mock_run):
        """Output containing '1' → Credential Guard is running → Pass."""
        mock_run.return_value = _make_ps_result("1")
        detector = WindowsDetector()
        result = detector.check_mfa_status()
        self.assertIsInstance(result, HardeningResult)
        self.assertEqual(result.status, "Pass")
        self.assertEqual(result.nist_control, "3.5.3")

    @patch("engine.core.detector.subprocess.run")
    def test_credential_guard_fail_empty(self, mock_run):
        """Empty output → Credential Guard not detected → Fail."""
        mock_run.return_value = _make_ps_result("")
        detector = WindowsDetector()
        result = detector.check_mfa_status()
        self.assertEqual(result.status, "Fail")

    @patch("engine.core.detector.subprocess.run")
    def test_credential_guard_fail_other_output(self, mock_run):
        """Output without '1' → Fail."""
        mock_run.return_value = _make_ps_result("0")
        detector = WindowsDetector()
        result = detector.check_mfa_status()
        self.assertEqual(result.status, "Fail")


class TestWindowsDetectorGuestAccount(unittest.TestCase):

    @patch("engine.core.detector.subprocess.run")
    def test_guest_disabled_pass(self, mock_run):
        """Output 'False' → Guest account disabled → Pass."""
        mock_run.return_value = _make_ps_result("False")
        detector = WindowsDetector()
        result = detector.check_guest_account()
        self.assertEqual(result.status, "Pass")
        self.assertEqual(result.nist_control, "3.1.1")

    @patch("engine.core.detector.subprocess.run")
    def test_guest_enabled_fail(self, mock_run):
        """Output 'True' → Guest account enabled → Fail."""
        mock_run.return_value = _make_ps_result("True")
        detector = WindowsDetector()
        result = detector.check_guest_account()
        self.assertEqual(result.status, "Fail")

    @patch("engine.core.detector.subprocess.run")
    def test_guest_unknown_fail(self, mock_run):
        """Empty / unexpected output → Fail."""
        mock_run.return_value = _make_ps_result("")
        detector = WindowsDetector()
        result = detector.check_guest_account()
        self.assertEqual(result.status, "Fail")


class TestWindowsDetectorSMBEncryption(unittest.TestCase):

    @patch("engine.core.detector.subprocess.run")
    def test_smb_encryption_enforced_pass(self, mock_run):
        """Output 'True' → SMB EncryptData is on → Pass."""
        mock_run.return_value = _make_ps_result("True")
        detector = WindowsDetector()
        result = detector.check_unencrypted_shares()
        self.assertEqual(result.status, "Pass")
        self.assertEqual(result.nist_control, "3.13.8")

    @patch("engine.core.detector.subprocess.run")
    def test_smb_encryption_not_enforced_fail(self, mock_run):
        """Output 'False' → SMB encryption off → Fail."""
        mock_run.return_value = _make_ps_result("False")
        detector = WindowsDetector()
        result = detector.check_unencrypted_shares()
        self.assertEqual(result.status, "Fail")


class TestWindowsDetectorRunAll(unittest.TestCase):

    @patch("engine.core.detector.subprocess.run")
    def test_run_all_returns_three_results(self, mock_run):
        """run_all() should return exactly 3 HardeningResult instances."""
        mock_run.return_value = _make_ps_result("1")  # makes all checks pass
        detector = WindowsDetector()
        results = detector.run_all()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, HardeningResult)

    @patch("engine.core.detector.subprocess.run")
    def test_run_all_mixed_results(self, mock_run):
        """run_all() should tolerate a mix of Pass/Fail results."""
        # First call (MFA): pass; second (Guest): fail; third (SMB): pass
        mock_run.side_effect = [
            _make_ps_result("1"),  # MFA → Pass
            _make_ps_result("True"),  # Guest → Fail (True = enabled)
            _make_ps_result("True"),  # SMB → Pass
        ]
        detector = WindowsDetector()
        results = detector.run_all()
        self.assertEqual(results[0].status, "Pass")
        self.assertEqual(results[1].status, "Fail")
        self.assertEqual(results[2].status, "Pass")


class TestPowerShellErrorHandling(unittest.TestCase):

    @patch("engine.core.detector.subprocess.run", side_effect=Exception("timeout"))
    def test_ps_exception_does_not_propagate(self, _):
        """If PowerShell throws, _ps() should return '' without raising."""
        detector = WindowsDetector()
        output = detector._ps("SomeCommand")
        self.assertEqual(output, "")


class TestDetectLocalOS(unittest.TestCase):

    @patch("engine.core.detector.platform.system", return_value="Windows")
    def test_detects_windows(self, _):
        self.assertEqual(detect_local_os(), "windows")

    @patch("engine.core.detector.platform.system", return_value="Linux")
    @patch("engine.core.detector.platform.release", return_value="5.14.0-el9")
    @patch("engine.core.detector.platform.platform", return_value="Linux-5.14-rocky9")
    def test_detects_rocky9(self, *_):
        self.assertEqual(detect_local_os(), "rocky9")


class TestRunLocalHardening(unittest.TestCase):

    @patch("engine.core.detector.platform.system", return_value="Windows")
    @patch("engine.core.detector.subprocess.run")
    def test_run_local_hardening_windows_returns_host_report(self, mock_run, _):
        """run_local_hardening() on Windows should return a HostReport."""
        mock_run.return_value = _make_ps_result("1")
        report = run_local_hardening()
        self.assertIsInstance(report, HostReport)
        self.assertEqual(report.os_type, "windows")
        self.assertGreater(len(report.results), 0)


if __name__ == "__main__":
    unittest.main()
