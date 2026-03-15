"""
RCA Logic Engine: Maps discovered asset telemetry to NIST 800-171 controls.
Supports dual-baseline cross-referencing against Rev 2 (110 controls, current
CMMC baseline) and Rev 3 (97 controls, future-proof baseline).

# Satisfies NIST 800-171 Rev 3:
# 3.4.1.  - Establish and maintain baseline configurations and inventories.
# 3.11.2  - Scan for vulnerabilities in organizational systems periodically.
# 3.14.1  - Identify, report, and correct system flaws in a timely manner.
# 3.12.1  - Periodically assess the security controls in organizational systems.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd

# Configure logging for the Mapper module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Mapper - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths (relative to the project root)
# ---------------------------------------------------------------------------
_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")
DEFAULT_REV2_PATH = os.path.join(_SCHEMA_DIR, "nist_rev2.json")
DEFAULT_REV3_PATH = os.path.join(_SCHEMA_DIR, "nist_rev3.json")


class NISTMapper:
    """
    RCA Logic Engine: Dual-baseline compliance mapper.

    Loads both Rev 2 and Rev 3 control schemas and generates a compliance
    matrix that lets auditors track each discovered asset against every
    individual control in both baselines simultaneously.

    # Satisfies NIST 800-171 3.12.1 (Security Assessments)
    """

    def __init__(
        self,
        rev2_path: str = DEFAULT_REV2_PATH,
        rev3_path: str = DEFAULT_REV3_PATH,
    ):
        self.rev2_controls = self._load_schema(rev2_path, "rev2")
        self.rev3_controls = self._load_schema(rev3_path, "rev3")
        self.df_compliance: pd.DataFrame = pd.DataFrame()

    # ------------------------------------------------------------------
    # Schema loading
    # ------------------------------------------------------------------
    @staticmethod
    def _load_schema(path: str, label: str) -> Dict[str, Any]:
        """Load a NIST schema JSON file and return the families dict."""
        try:
            with open(path, "r") as fh:
                data = json.load(fh)
                # Handle both top-level key variants
                for key in (
                    "nist_800_171_rev2",
                    "nist_800_171_rev3",
                ):
                    if key in data:
                        families = data[key].get("families", {})
                        total = sum(
                            len(f.get("controls", {})) for f in families.values()
                        )
                        logger.info(
                            f"Loaded {label} schema: {total} controls across "
                            f"{len(families)} families from {path}"
                        )
                        return families
            logger.warning(f"No recognised top-level key in {path}")
            return {}
        except FileNotFoundError:
            logger.error(f"Schema not found: {path}")
            return {}
        except Exception as exc:
            logger.error(f"Failed to parse schema {path}: {exc}")
            return {}

    # ------------------------------------------------------------------
    # Matrix generation
    # ------------------------------------------------------------------
    def generate_compliance_matrix(
        self, inventory: Dict[str, Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Build a wide-format DataFrame where every row is an asset and
        every column beyond the base fields is a single NIST control
        from *both* Rev 2 and Rev 3.

        # Satisfies NIST 800-171 3.11.2 and 3.14.1
        """
        logger.info(
            f"Generating dual-baseline compliance matrix for "
            f"{len(inventory)} assets …"
        )

        records: List[Dict[str, str]] = []
        for ip, asset in inventory.items():
            row: Dict[str, str] = {
                "Asset_IP": ip,
                "Asset_MAC": asset.get("mac_address", "Unknown"),
                "Discovery_Method": asset.get("discovery_method", "Unknown"),
            }

            # Rev 2 columns  — e.g. "R2_AC_3.1.1"
            for fam_code, fam in self.rev2_controls.items():
                for ctrl_id in fam.get("controls", {}):
                    col = f"R2_{fam_code}_{ctrl_id}"
                    row[col] = "Untested"

            # Rev 3 columns  — e.g. "R3_AC_3.1.1"
            for fam_code, fam in self.rev3_controls.items():
                for ctrl_id in fam.get("controls", {}):
                    col = f"R3_{fam_code}_{ctrl_id}"
                    row[col] = "Untested"

            records.append(row)

        self.df_compliance = pd.DataFrame(records)
        logger.info("Dual-baseline compliance matrix generated successfully.")
        return self.df_compliance

    # ------------------------------------------------------------------
    # Per-asset / per-control updates
    # ------------------------------------------------------------------
    def audit_control(
        self,
        ip_address: str,
        revision: str,
        family_code: str,
        control_id: str,
        status: str,
    ) -> None:
        """
        Set the compliance status for a specific asset + control.

        Args:
            ip_address:  Target asset IP.
            revision:    "R2" or "R3".
            family_code: Family short code (e.g. "AC", "IA").
            control_id:  Full control id (e.g. "3.5.3").
            status:      One of "Compliant", "Non-Compliant",
                         "Not-Applicable", "Untested".

        # Satisfies NIST 800-171 3.4.1 (Inventories and Status)
        """
        if self.df_compliance.empty:
            logger.warning(
                "Compliance matrix is empty — run generate_compliance_matrix first."
            )
            return

        col = f"{revision}_{family_code}_{control_id}"
        if col not in self.df_compliance.columns:
            logger.error(f"Column {col} not found in compliance matrix.")
            return

        mask = self.df_compliance["Asset_IP"] == ip_address
        if mask.any():
            self.df_compliance.loc[mask, col] = status
            logger.info(f"Updated {ip_address} | {col} → '{status}'")
        else:
            logger.warning(f"Asset {ip_address} not found in matrix.")

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Dict[str, int]]:
        """
        Return a quick rollup of Compliant / Non-Compliant / Untested
        counts per revision.
        """
        result: Dict[str, Dict[str, int]] = {}
        for prefix in ("R2", "R3"):
            cols = [c for c in self.df_compliance.columns if c.startswith(prefix)]
            vals = self.df_compliance[cols].values.flatten()
            result[prefix] = {
                "Compliant": int((vals == "Compliant").sum()),
                "Non-Compliant": int((vals == "Non-Compliant").sum()),
                "Not-Applicable": int((vals == "Not-Applicable").sum()),
                "Untested": int((vals == "Untested").sum()),
            }
        return result

    def export_report(self, filepath: str) -> None:
        """
        Export the compliance matrix to CSV.

        # Satisfies NIST 800-171 3.3.1 (Audit Records)
        """
        if not self.df_compliance.empty:
            self.df_compliance.to_csv(filepath, index=False)
            logger.info(f"Compliance report exported → {filepath}")
        else:
            logger.warning("No data to export.")


if __name__ == "__main__":
    mapper = NISTMapper()
    print(
        f"Mapper loaded — Rev 2 families: {len(mapper.rev2_controls)}, "
        f"Rev 3 families: {len(mapper.rev3_controls)}"
    )
