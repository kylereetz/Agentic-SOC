"""
Tests for engine.core.mapper — NISTMapper
Uses the real schema JSON files (static, no network required).
"""

import os
import unittest

import pandas as pd

from engine.core.mapper import NISTMapper

# Paths to the real schema files
_HERE = os.path.dirname(__file__)
_SCHEMA_DIR = os.path.join(_HERE, "..", "schemas")
REV2_PATH = os.path.join(_SCHEMA_DIR, "nist_rev2.json")
REV3_PATH = os.path.join(_SCHEMA_DIR, "nist_rev3.json")


def _make_mapper() -> NISTMapper:
    """Helper: always load from the real schema files."""
    return NISTMapper(rev2_path=REV2_PATH, rev3_path=REV3_PATH)


def _sample_inventory():
    return {
        "192.168.1.1": {
            "ip_address": "192.168.1.1",
            "mac_address": "aa:bb:cc:dd:ee:01",
            "discovery_method": "active_arp",
        },
        "192.168.1.2": {
            "ip_address": "192.168.1.2",
            "mac_address": "aa:bb:cc:dd:ee:02",
            "discovery_method": "passive_sniff",
        },
    }


class TestNISTMapperLoading(unittest.TestCase):
    """Test schema loading."""

    def test_schemas_load_with_controls(self):
        """Both Rev 2 and Rev 3 schemas should load successfully with > 0 families."""
        mapper = _make_mapper()
        self.assertGreater(len(mapper.rev2_controls), 0, "Rev 2 schema is empty")
        self.assertGreater(len(mapper.rev3_controls), 0, "Rev 3 schema is empty")

    def test_missing_schema_does_not_crash(self):
        """Loading a non-existent schema file should log an error but not raise."""
        mapper = NISTMapper(
            rev2_path="/nonexistent/path.json", rev3_path="/nonexistent/path.json"
        )
        self.assertEqual(mapper.rev2_controls, {})
        self.assertEqual(mapper.rev3_controls, {})


class TestComplianceMatrixGeneration(unittest.TestCase):
    """Test matrix generation."""

    def setUp(self):
        self.mapper = _make_mapper()
        self.inventory = _sample_inventory()

    def test_matrix_has_expected_rows(self):
        """Matrix should have one row per asset."""
        df = self.mapper.generate_compliance_matrix(self.inventory)
        self.assertEqual(len(df), 2)

    def test_matrix_has_asset_ip_column(self):
        """Matrix should include Asset_IP column."""
        df = self.mapper.generate_compliance_matrix(self.inventory)
        self.assertIn("Asset_IP", df.columns)
        self.assertIn("192.168.1.1", df["Asset_IP"].values)

    def test_matrix_has_r2_columns(self):
        """Matrix should have at least one R2_ column."""
        df = self.mapper.generate_compliance_matrix(self.inventory)
        r2_cols = [c for c in df.columns if c.startswith("R2_")]
        self.assertGreater(len(r2_cols), 0)

    def test_matrix_has_r3_columns(self):
        """Matrix should have at least one R3_ column."""
        df = self.mapper.generate_compliance_matrix(self.inventory)
        r3_cols = [c for c in df.columns if c.startswith("R3_")]
        self.assertGreater(len(r3_cols), 0)

    def test_default_status_is_untested(self):
        """All cells should default to 'Untested' after generation."""
        df = self.mapper.generate_compliance_matrix(self.inventory)
        ctrl_cols = [c for c in df.columns if c.startswith(("R2_", "R3_"))]
        for col in ctrl_cols:
            self.assertTrue(
                (df[col] == "Untested").all(),
                f"Column {col} has non-Untested values after generation",
            )

    def test_empty_inventory_returns_empty_df(self):
        """An empty inventory should return an empty DataFrame."""
        df = self.mapper.generate_compliance_matrix({})
        self.assertTrue(df.empty)


class TestAuditControl(unittest.TestCase):
    """Test per-asset / per-control status updates."""

    def setUp(self):
        self.mapper = _make_mapper()
        self.mapper.generate_compliance_matrix(_sample_inventory())

    def _first_r2_col(self) -> str:
        cols = [c for c in self.mapper.df_compliance.columns if c.startswith("R2_")]
        return cols[0]

    def test_audit_control_sets_cell(self):
        """audit_control() should update the correct cell."""
        col = self._first_r2_col()
        # col format: R2_<FAMILY>_<CTRL_ID>  e.g. "R2_AC_3.1.1"
        parts = col.split("_")
        revision = parts[0]  # "R2"
        family_code = parts[1]  # e.g. "AC"
        # Remaining parts joined form the control ID (e.g. "3.1.1")
        control_id = "_".join(parts[i] for i in range(2, len(parts)))

        self.mapper.audit_control(
            "192.168.1.1", revision, family_code, control_id, "Compliant"
        )
        row = self.mapper.df_compliance[
            self.mapper.df_compliance["Asset_IP"] == "192.168.1.1"
        ]
        self.assertEqual(row[col].values[0], "Compliant")

    def test_audit_control_does_not_affect_other_asset(self):
        """Updating one asset's control should not change another asset's value."""
        col = self._first_r2_col()
        parts = col.split("_")
        revision = parts[0]
        family_code = parts[1]
        control_id = "_".join(parts[i] for i in range(2, len(parts)))
        self.mapper.audit_control(
            "192.168.1.1", revision, family_code, control_id, "Compliant"
        )

        other_row = self.mapper.df_compliance[
            self.mapper.df_compliance["Asset_IP"] == "192.168.1.2"
        ]
        self.assertEqual(other_row[col].values[0], "Untested")

    def test_audit_control_invalid_column(self):
        """audit_control() should log an error and not crash for a bad column name."""
        try:
            self.mapper.audit_control("192.168.1.1", "R2", "XX", "9.9.9", "Compliant")
        except Exception:
            self.fail("audit_control raised an exception on an invalid column name")

    def test_audit_control_before_matrix_generation(self):
        """audit_control() called on empty matrix should not crash."""
        fresh_mapper = _make_mapper()
        try:
            fresh_mapper.audit_control("192.168.1.1", "R2", "AC", "3.1.1", "Compliant")
        except Exception:
            self.fail("audit_control raised an exception on an empty matrix")


class TestSummary(unittest.TestCase):
    """Test the summary() rollup."""

    def test_summary_returns_r2_and_r3(self):
        """summary() should return keys 'R2' and 'R3'."""
        mapper = _make_mapper()
        mapper.generate_compliance_matrix(_sample_inventory())
        s = mapper.summary()
        self.assertIn("R2", s)
        self.assertIn("R3", s)

    def test_summary_untested_count(self):
        """After generation, Untested count should equal (num_assets * num_controls)."""
        mapper = _make_mapper()
        inventory = _sample_inventory()
        df = mapper.generate_compliance_matrix(inventory)
        s = mapper.summary()

        r2_cols = [c for c in df.columns if c.startswith("R2_")]
        expected_r2_untested = len(inventory) * len(r2_cols)
        self.assertEqual(s["R2"]["Untested"], expected_r2_untested)


if __name__ == "__main__":
    unittest.main()
