"""
Tests for engine.core.sentinel — SentinelEngine
All network calls are mocked; no real packets are sent.
"""

import unittest
from unittest.mock import MagicMock, patch

from engine.core.sentinel import SentinelEngine


class TestSentinelPassiveSniffing(unittest.TestCase):
    """Test passive sniffing discovery."""

    def _make_ip_ether_packet(self, src_ip: str, src_mac: str) -> MagicMock:
        """Build a mock Scapy packet with IP and Ethernet layers."""
        pkt = MagicMock()
        pkt.haslayer.side_effect = lambda layer: layer.__name__ in ("IP", "Ether")
        pkt.__getitem__ = lambda self, layer: (
            MagicMock(src=src_ip) if layer.__name__ == "IP"
            else MagicMock(src=src_mac)
        )
        return pkt

    @patch("engine.core.sentinel.sniff")
    def test_passive_sniffing_calls_sniff(self, mock_sniff):
        """passive_sniffing() should call scapy.sniff with the right args."""
        sentinel = SentinelEngine()
        sentinel.passive_sniffing(timeout=5, packet_count=10)
        mock_sniff.assert_called_once()
        kwargs = mock_sniff.call_args.kwargs
        self.assertEqual(kwargs["count"], 10)
        self.assertEqual(kwargs["timeout"], 5)

    def test_packet_callback_adds_asset(self):
        """_packet_callback should add a new asset to the inventory."""
        sentinel = SentinelEngine()

        # Build a minimal fake packet with IP + Ether layers
        ip_layer = MagicMock()
        ip_layer.src = "10.0.0.5"
        ether_layer = MagicMock()
        ether_layer.src = "de:ad:be:ef:00:01"

        pkt = MagicMock()
        pkt.haslayer.side_effect = lambda cls: cls.__name__ in ("IP", "Ether")

        from scapy.all import IP, Ether
        pkt.__getitem__ = lambda _, cls: ip_layer if cls is IP else ether_layer

        sentinel._packet_callback(pkt)

        self.assertIn("10.0.0.5", sentinel.inventory)
        self.assertEqual(sentinel.inventory["10.0.0.5"]["mac_address"], "de:ad:be:ef:00:01")

    def test_packet_callback_no_duplicate(self):
        """_packet_callback should not add the same IP twice."""
        sentinel = SentinelEngine()
        sentinel.seen_ips.add("10.0.0.5")  # pre-populate

        from scapy.all import IP, Ether
        ip_layer = MagicMock()
        ip_layer.src = "10.0.0.5"
        pkt = MagicMock()
        pkt.haslayer.side_effect = lambda cls: cls.__name__ == "IP"
        pkt.__getitem__ = lambda _, cls: ip_layer

        sentinel._packet_callback(pkt)
        self.assertEqual(len(sentinel.inventory), 0)  # was not added


class TestSentinelARPScan(unittest.TestCase):
    """Test active ARP scanning."""

    @patch("engine.core.sentinel.srp")
    def test_arp_scan_discovers_device(self, mock_srp):
        """active_arp_scan should parse srp() replies and add assets."""
        # Build a fake ARP reply
        rcv = MagicMock()
        rcv.psrc = "192.168.1.10"
        rcv.hwsrc = "aa:bb:cc:dd:ee:01"
        mock_srp.return_value = ([(None, rcv)], [])

        sentinel = SentinelEngine()
        discovered = sentinel.active_arp_scan("192.168.1.0/24", timeout=1)

        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0]["ip_address"], "192.168.1.10")
        self.assertIn("192.168.1.10", sentinel.inventory)

    @patch("engine.core.sentinel.srp")
    def test_arp_scan_no_duplicates(self, mock_srp):
        """active_arp_scan should not re-add an already-known IP."""
        rcv = MagicMock()
        rcv.psrc = "192.168.1.10"
        rcv.hwsrc = "aa:bb:cc:dd:ee:01"
        mock_srp.return_value = ([(None, rcv)], [])

        sentinel = SentinelEngine()
        sentinel.seen_ips.add("192.168.1.10")
        discovered = sentinel.active_arp_scan("192.168.1.0/24", timeout=1)

        self.assertEqual(len(discovered), 0)

    @patch("engine.core.sentinel.srp")
    def test_arp_scan_empty_network(self, mock_srp):
        """active_arp_scan on a silent network should return an empty list."""
        mock_srp.return_value = ([], [])
        sentinel = SentinelEngine()
        discovered = sentinel.active_arp_scan("10.0.0.0/24", timeout=1)
        self.assertEqual(discovered, [])


class TestSentinelICMPSweep(unittest.TestCase):
    """Test ICMP sweep discovery."""

    @patch("engine.core.sentinel.sr1")
    def test_icmp_sweep_adds_alive_host(self, mock_sr1):
        """icmp_sweep should add a responsive host to inventory."""
        mock_sr1.return_value = MagicMock()  # non-None = host responded

        sentinel = SentinelEngine()
        discovered = sentinel.icmp_sweep(["10.0.0.1"], timeout=1)

        self.assertEqual(len(discovered), 1)
        self.assertIn("10.0.0.1", sentinel.inventory)

    @patch("engine.core.sentinel.sr1")
    def test_icmp_sweep_skips_silent_host(self, mock_sr1):
        """icmp_sweep should skip hosts that don't respond."""
        mock_sr1.return_value = None  # host did not respond

        sentinel = SentinelEngine()
        discovered = sentinel.icmp_sweep(["10.0.0.99"], timeout=1)

        self.assertEqual(len(discovered), 0)
        self.assertNotIn("10.0.0.99", sentinel.inventory)

    @patch("engine.core.sentinel.sr1")
    def test_icmp_sweep_skips_known_ip(self, mock_sr1):
        """icmp_sweep should skip IPs already in seen_ips."""
        mock_sr1.return_value = MagicMock()
        sentinel = SentinelEngine()
        sentinel.seen_ips.add("10.0.0.1")
        discovered = sentinel.icmp_sweep(["10.0.0.1"], timeout=1)

        self.assertEqual(len(discovered), 0)
        # sr1 should not have been called at all
        mock_sr1.assert_not_called()

    def test_get_inventory_returns_dict(self):
        """get_inventory() should always return a dict."""
        sentinel = SentinelEngine()
        inv = sentinel.get_inventory()
        self.assertIsInstance(inv, dict)


if __name__ == "__main__":
    unittest.main()
