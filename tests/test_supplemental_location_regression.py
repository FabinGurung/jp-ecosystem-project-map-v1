from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "imports/photo-groups-2026-08-02/supplemental_location_corrections_2026-08-07.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class SupplementalLocationRegressionTests(unittest.TestCase):
    def test_bachi_and_ama_foundation_coordinate(self) -> None:
        rows = read_rows(ROOT / "project_opportunities.csv")
        row = next(item for item in rows if item["opportunity_id"] == "OPP-000001")
        self.assertAlmostEqual(float(row["latitude"]), 28.181302, places=6)
        self.assertAlmostEqual(float(row["longitude"]), 84.033216, places=6)
        self.assertEqual(row["data_quality_status"], "VALID")
        self.assertEqual(row["data_quality_issue"].strip(), "")

    def test_fishtail_builders_office_coordinate(self) -> None:
        rows = read_rows(ROOT / "organization_locations.csv")
        row = next(item for item in rows if item["organization_location_id"] == "OLOC-000001")
        self.assertAlmostEqual(float(row["latitude"]), 28.225246, places=6)
        self.assertAlmostEqual(float(row["longitude"]), 83.987354, places=6)
        self.assertEqual(row["data_quality_status"], "VALID")
        self.assertEqual(row["data_quality_issue"].strip(), "")

    def test_supplemental_coordinate_audit(self) -> None:
        rows = read_rows(AUDIT)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["entity_id"] for row in rows}, {"OPP-000001", "OLOC-000001"})
        for row in rows:
            self.assertEqual(row["coordinate_verification_status"], "VERIFIED")
            self.assertIn("does not verify", row["notes"])

    def test_bhalam_200m_road_segments_remain_distinct(self) -> None:
        rows = read_rows(ROOT / "project_components.csv")
        segments = [
            row for row in rows
            if row["project_id"] == "PRJ-000024" and row["component_type"] == "ROAD_SEGMENT"
        ]
        self.assertEqual(len(segments), 3)
        by_sequence = {row["sequence_no"]: row for row in segments}
        expected = {
            "1": (28.251966, 83.995884),
            "2": (28.252861, 83.996621),
            "3": (28.247575, 83.999227),
        }
        self.assertEqual(set(by_sequence), set(expected))
        for sequence, (lat, lon) in expected.items():
            self.assertAlmostEqual(float(by_sequence[sequence]["latitude"]), lat, places=6)
            self.assertAlmostEqual(float(by_sequence[sequence]["longitude"]), lon, places=6)

    def test_frontend_renders_road_segments_without_project_selection(self) -> None:
        source = (ROOT / "assets/js/app.js").read_text(encoding="utf-8")
        self.assertIn('component.component_type === "ROAD_SEGMENT"', source)
        self.assertIn('permanent: true', source)
        self.assertIn('renderSelectedComponents(state.activeProjectId);', source)
        self.assertNotIn(
            'if (state.activeProjectId) renderSelectedComponents(state.activeProjectId);',
            source,
        )


if __name__ == "__main__":
    unittest.main()
