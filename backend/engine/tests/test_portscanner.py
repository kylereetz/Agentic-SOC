"""
Tests for engine.core.portscanner — PortScanner
python-nmap is mocked; no real network scans are performed.
"""

import unittest
from unittest.mock import MagicMock, patch

from engine.core.portscanner import PortScanner, PortScanResult, OpenPort, HIGH_RISK_PORTS


def _build_mock_nm(ip: str, state: str = "up", ports: dict = None):
    """
    Build a mock nmap.PortScanner instance pre-populated with fake scan data.

    Args:
        ip:    The target IP address string.
        state: nmap host state ("up" or "down").
        ports: Dict of {port_num: port_data_dict} under "tcp".
    """
    ports = ports or {}
    nm_instance = MagicMock()
    nm_instance.all_hosts.return_value = [ip]
    nm_instance.__getitem__.return_value = MagicMock(
        state=lambda: state,
        hostname=lambda: "",
        all_protocols=lambda: ["tcp"] if ports else [],
        __getitem__=lambda self, proto: MagicMock(keys=lambda: list(ports.keys()),
                                                   __getitem__=lambda self, p: ports[p]),
    )
    # Wire per-port data
    host_mock = nm_instance[ip]
    if ports:
        proto_mock = host_mock["tcp"]
        proto_mock.keys.return_value = list(ports.keys())
        proto_mock.__getitem__ = lambda self, p: ports[p]
    return nm_instance


class TestPortScannerInit(unittest.TestCase):

    def test_default_ports_set(self):
        scanner = PortScanner()
        self.assertIn("502", scanner.ports)   # Modbus
        self.assertIn("445", scanner.ports)   # SMB
        self.assertIn("44818", scanner.ports) # EtherNet/IP

    @patch.dict("sys.modules", {"nmap": None})
    def test_nmap_missing_does_not_raise(self):
        """If nmap is not installed, PortScanner should init without crashing."""
        with patch("engine.core.portscanner.PortScanner._load_nmap", return_value=None):
            scanner = PortScanner()
            self.assertIsNone(scanner._nm)


class TestPortScannerSingleHost(unittest.TestCase):

    @patch("engine.core.portscanner.PortScanner._load_nmap")
    def test_scan_returns_port_scan_result(self, mock_load):
        """scan() should always return a PortScanResult."""
        mock_module = MagicMock()
        mock_module.PortScanner.return_value = _build_mock_nm("10.0.0.1", state="up", ports={})
        mock_load.return_value = mock_module

        scanner = PortScanner()
        result = scanner.scan("10.0.0.1")
        self.assertIsInstance(result, PortScanResult)

    @patch("engine.core.portscanner.PortScanner._load_nmap")
    def test_open_port_parsed_correctly(self, mock_load):
        """An open port from nmap should be parsed into an OpenPort dataclass."""
        port_data = {
            80: {"state": "open", "name": "http", "product": "Apache", "version": "2.4"}
        }
        mock_nm_instance = MagicMock()
        mock_nm_instance.all_hosts.return_value = ["10.0.0.1"]
        host_mock = MagicMock()
        host_mock.state.return_value = "up"
        host_mock.hostname.return_value = "test-host"
        host_mock.all_protocols.return_value = ["tcp"]
        proto_mock = MagicMock()
        proto_mock.keys.return_value = [80]
        proto_mock.__getitem__ = lambda self, p: port_data[p]
        host_mock.__getitem__ = lambda self, proto: proto_mock
        mock_nm_instance.__getitem__ = lambda self, ip: host_mock

        mock_module = MagicMock()
        mock_module.PortScanner.return_value = mock_nm_instance
        mock_load.return_value = mock_module

        scanner = PortScanner()
        result = scanner.scan("10.0.0.1")

        self.assertEqual(len(result.open_ports), 1)
        self.assertEqual(result.open_ports[0].port, 80)
        self.assertEqual(result.open_ports[0].service, "http")
        self.assertEqual(result.open_ports[0].product, "Apache")

    @patch("engine.core.portscanner.PortScanner._load_nmap")
    def test_high_risk_port_flagged(self, mock_load):
        """Modbus port 502 should be flagged as high-risk."""
        port_data = {502: {"state": "open", "name": "modbus", "product": "", "version": ""}}
        mock_nm_instance = MagicMock()
        mock_nm_instance.all_hosts.return_value = ["10.0.0.1"]
        host_mock = MagicMock()
        host_mock.state.return_value = "up"
        host_mock.hostname.return_value = ""
        host_mock.all_protocols.return_value = ["tcp"]
        proto_mock = MagicMock()
        proto_mock.keys.return_value = [502]
        proto_mock.__getitem__ = lambda self, p: port_data[p]
        host_mock.__getitem__ = lambda self, proto: proto_mock
        mock_nm_instance.__getitem__ = lambda self, ip: host_mock

        mock_module = MagicMock()
        mock_module.PortScanner.return_value = mock_nm_instance
        mock_load.return_value = mock_module

        scanner = PortScanner()
        result = scanner.scan("10.0.0.1")

        self.assertTrue(result.has_high_risk_ports)
        self.assertTrue(result.open_ports[0].is_high_risk)

    @patch("engine.core.portscanner.PortScanner._load_nmap")
    def test_down_host_returns_empty_ports(self, mock_load):
        """A host that doesn't respond should return an empty open_ports list."""
        mock_nm_instance = MagicMock()
        mock_nm_instance.all_hosts.return_value = []   # host not in results
        mock_module = MagicMock()
        mock_module.PortScanner.return_value = mock_nm_instance
        mock_load.return_value = mock_module

        scanner = PortScanner()
        result = scanner.scan("10.0.0.99")

        self.assertEqual(result.open_ports, [])
        self.assertEqual(result.scan_status, "down")

    def test_nmap_missing_returns_nmap_missing_status(self):
        """If nmap module is None, scan() should return status='nmap_missing'."""
        with patch("engine.core.portscanner.PortScanner._load_nmap", return_value=None):
            scanner = PortScanner()
        result = scanner.scan("10.0.0.1")
        self.assertEqual(result.scan_status, "nmap_missing")
        self.assertEqual(result.open_ports, [])


class TestPortScannerBatch(unittest.TestCase):

    @patch("engine.core.portscanner.PortScanner._load_nmap")
    def test_scan_targets_returns_one_result_per_host(self, mock_load):
        """scan_targets() should return exactly one PortScanResult per target."""
        mock_nm_instance = MagicMock()
        mock_nm_instance.all_hosts.return_value = []
        mock_module = MagicMock()
        mock_module.PortScanner.return_value = mock_nm_instance
        mock_load.return_value = mock_module

        scanner = PortScanner()
        targets = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
        results = scanner.scan_targets(targets)

        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, PortScanResult)


class TestHighRiskPortConstants(unittest.TestCase):
    """Sanity-check the HIGH_RISK_PORTS constant."""

    def test_modbus_in_high_risk(self):
        self.assertIn(502, HIGH_RISK_PORTS)

    def test_ethernetip_in_high_risk(self):
        self.assertIn(44818, HIGH_RISK_PORTS)

    def test_rdp_in_high_risk(self):
        self.assertIn(3389, HIGH_RISK_PORTS)


if __name__ == "__main__":
    unittest.main()
