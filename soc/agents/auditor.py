"""
RCA Auditor Agent: Gap Analysis Report Generator.
Consumes the latest compliance matrix from RCAMapper and inventory
snapshots from Scout, then generates a professional PDF report with:
  - Cover page (client, date, auditor)
  - Executive summary with risk score
  - Per-family breakdown tables (Rev 2 + Rev 3)
  - Remediation priority matrix

Uses reportlab for PDF generation — no LaTeX dependency.

# Satisfies NIST 800-171 Rev 3:
# 3.12.1 - Periodically assess the security controls.
# 3.12.2 - Develop and implement plans of action to correct deficiencies.
# 3.3.1  - Create and retain system audit logs and records.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - RCA Auditor - %(message)s",
)
logger = logging.getLogger(__name__)

# Output directory
_REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------
def _compute_risk_score(stats: Dict[str, int]) -> float:
    """
    Compute a 0–100 risk score.
    100 = fully compliant, 0 = nothing tested or everything non-compliant.
    """
    total = stats.get("Compliant", 0) + stats.get("Non-Compliant", 0)
    if total == 0:
        return 0.0
    return round((stats["Compliant"] / total) * 100, 1)


def _risk_label(score: float) -> str:
    """Human-readable risk posture label."""
    if score >= 90:
        return "LOW RISK"
    elif score >= 70:
        return "MODERATE RISK"
    elif score >= 50:
        return "HIGH RISK"
    return "CRITICAL RISK"


# ---------------------------------------------------------------------------
# Per-family statistics
# ---------------------------------------------------------------------------
def _family_stats(
    df: pd.DataFrame, prefix: str
) -> List[Dict[str, Any]]:
    """
    Break down compliance by NIST family for a given revision prefix
    (e.g. "R2" or "R3").
    """
    cols = [c for c in df.columns if c.startswith(prefix)]
    # Extract family code from column name like "R2_AC_3.1.1"
    families: Dict[str, Dict[str, int]] = {}
    for col in cols:
        parts = col.split("_")
        if len(parts) >= 3:
            fam = parts[1]  # e.g. "AC"
            if fam not in families:
                families[fam] = {
                    "Compliant": 0,
                    "Non-Compliant": 0,
                    "Untested": 0,
                    "Not-Applicable": 0,
                }
            for val in df[col].values:
                families[fam][val] = families[fam].get(val, 0) + 1

    result = []
    for fam, counts in sorted(families.items()):
        total_tested = counts["Compliant"] + counts["Non-Compliant"]
        score = (
            round(counts["Compliant"] / total_tested * 100, 1)
            if total_tested > 0
            else 0.0
        )
        result.append({"family": fam, "score": score, **counts})
    return result


# ---------------------------------------------------------------------------
# PDF Builder
# ---------------------------------------------------------------------------
class AuditorAgent:
    """
    Generates a branded Gap Analysis PDF from compliance data.

    # Satisfies NIST 800-171 3.12.1 and 3.12.2
    """

    def __init__(
        self,
        client_name: str = "Client",
        auditor_name: str = "RCA Automated Auditor",
    ):
        self.client_name = client_name
        self.auditor_name = auditor_name
        os.makedirs(_REPORT_DIR, exist_ok=True)

    def generate_report(
        self,
        compliance_csv: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Build the gap analysis PDF.

        Args:
            compliance_csv: Path to the CSV exported by NISTMapper.
            output_path:    Optional override for the PDF output path.

        Returns:
            Absolute path to the generated PDF.
        """
        logger.info(f"Loading compliance data from {compliance_csv} …")
        df = pd.read_csv(compliance_csv)

        if output_path is None:
            ts = datetime.utcnow().strftime("%Y%m%d")
            output_path = os.path.join(
                _REPORT_DIR, f"gap_analysis_{ts}.pdf"
            )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        elements: List[Any] = []

        # -- Cover page --
        elements.append(Spacer(1, 2 * inch))
        elements.append(
            Paragraph(
                "NIST 800-171 Gap Analysis Report",
                ParagraphStyle(
                    "CoverTitle",
                    parent=styles["Title"],
                    fontSize=28,
                    textColor=colors.HexColor("#1a237e"),
                ),
            )
        )
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(
            Paragraph(
                f"Prepared for: <b>{self.client_name}</b>",
                styles["Heading2"],
            )
        )
        elements.append(
            Paragraph(
                f"Date: {datetime.utcnow().strftime('%B %d, %Y')}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"Auditor: {self.auditor_name}", styles["Normal"])
        )
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(
            Paragraph(
                "<i>CONFIDENTIAL — Do not distribute without authorization.</i>",
                ParagraphStyle(
                    "Conf",
                    parent=styles["Normal"],
                    textColor=colors.red,
                ),
            )
        )
        elements.append(PageBreak())

        # -- Executive Summary --
        elements.append(
            Paragraph("Executive Summary", styles["Heading1"])
        )
        elements.append(Spacer(1, 0.2 * inch))

        total_assets = len(df)
        elements.append(
            Paragraph(
                f"Total assets assessed: <b>{total_assets}</b>",
                styles["Normal"],
            )
        )

        for prefix, label in [("R2", "Rev 2 (CMMC Baseline)"), ("R3", "Rev 3 (Future Baseline)")]:
            cols = [c for c in df.columns if c.startswith(prefix)]
            if not cols:
                continue
            vals = df[cols].values.flatten()
            stats = {
                "Compliant": int((vals == "Compliant").sum()),
                "Non-Compliant": int((vals == "Non-Compliant").sum()),
                "Untested": int((vals == "Untested").sum()),
                "Not-Applicable": int((vals == "Not-Applicable").sum()),
            }
            score = _compute_risk_score(stats)
            rlabel = _risk_label(score)

            elements.append(Spacer(1, 0.15 * inch))
            elements.append(
                Paragraph(
                    f"<b>{label}</b> — Score: <b>{score}%</b> ({rlabel})",
                    styles["Heading3"],
                )
            )
            summary_data = [
                ["Status", "Count"],
                ["Compliant", str(stats["Compliant"])],
                ["Non-Compliant", str(stats["Non-Compliant"])],
                ["Untested", str(stats["Untested"])],
                ["Not-Applicable", str(stats["Not-Applicable"])],
            ]
            t = Table(summary_data, colWidths=[2.5 * inch, 1.5 * inch])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ]
                )
            )
            elements.append(t)

        elements.append(PageBreak())

        # -- Per-family breakdown --
        for prefix, label in [("R2", "NIST 800-171 Rev 2"), ("R3", "NIST 800-171 Rev 3")]:
            fstats = _family_stats(df, prefix)
            if not fstats:
                continue

            elements.append(
                Paragraph(
                    f"{label} — Family Breakdown", styles["Heading1"]
                )
            )
            elements.append(Spacer(1, 0.15 * inch))

            table_data = [
                ["Family", "Score %", "Compliant", "Non-Compliant", "Untested"]
            ]
            for fs in fstats:
                table_data.append(
                    [
                        fs["family"],
                        f"{fs['score']}%",
                        str(fs["Compliant"]),
                        str(fs["Non-Compliant"]),
                        str(fs["Untested"]),
                    ]
                )

            t = Table(
                table_data,
                colWidths=[1 * inch, 1 * inch, 1.2 * inch, 1.4 * inch, 1 * inch],
            )
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ]
                )
            )
            elements.append(t)
            elements.append(Spacer(1, 0.3 * inch))

        # -- Remediation Priority Matrix --
        elements.append(PageBreak())
        elements.append(
            Paragraph("Remediation Priority Matrix", styles["Heading1"])
        )
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(
            Paragraph(
                "The following families have the lowest compliance scores "
                "and should be prioritised for remediation:",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Combine R2+R3 stats and sort by lowest score
        all_fstats = []
        for prefix, rev in [("R2", "Rev 2"), ("R3", "Rev 3")]:
            for fs in _family_stats(df, prefix):
                all_fstats.append({**fs, "revision": rev})

        all_fstats.sort(key=lambda x: x["score"])
        priority_data = [["Priority", "Revision", "Family", "Score %", "Non-Compliant"]]
        for i, fs in enumerate(all_fstats[:15], start=1):
            priority_data.append(
                [
                    str(i),
                    fs["revision"],
                    fs["family"],
                    f"{fs['score']}%",
                    str(fs["Non-Compliant"]),
                ]
            )

        if len(priority_data) > 1:
            t = Table(
                priority_data,
                colWidths=[0.8 * inch, 0.9 * inch, 0.9 * inch, 1 * inch, 1.3 * inch],
            )
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b71c1c")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ffebee")]),
                    ]
                )
            )
            elements.append(t)

        # Build PDF
        doc.build(elements)
        logger.info(f"Gap analysis report generated → {output_path}")
        return output_path


if __name__ == "__main__":
    auditor = AuditorAgent(client_name="Demo Client")
    print("Auditor agent loaded. Provide a compliance CSV to generate a report.")
