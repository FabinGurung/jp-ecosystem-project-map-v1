from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "imports/photo-groups-2026-08-02/coordinate_corrections_2026-08-04.csv"

EXPECTED = {
    "PRJ-000003": (28.2181667, 84.0382222),
    "PRJ-000008": (28.2257095, 83.9821248),
    "PRJ-000009": (28.2276034, 83.9844513),
    "PRJ-000010": (28.2271493, 83.9851520),
    "PRJ-000011": (28.2283378, 83.9817348),
    "PRJ-000012": (28.2285729, 83.9863023),
    "PRJ-000013": (28.2179568, 83.9764690),
    "PRJ-000014": (28.2189403, 83.9785772),
    "PRJ-000015": (28.2232024, 83.9788233),
    "PRJ-000017": (28.2086944, 83.9596389),
    "PRJ-000018": (28.2114489, 83.9915658),
    "PRJ-000019": (28.2154589, 84.0053933),
    "PRJ-000021": (28.1902064, 84.0112143),
    "PRJ-000022": (28.1897729, 84.0148618),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class CoordinateRegressionTests(unittest.TestCase):
    def test_canonical_project_coordinates(self) -> None:
        projects = {row["project_id"]: row for row in read_rows(ROOT / "projects.csv")}
        for project_id, expected in EXPECTED.items():
            actual = (float(projects[project_id]["latitude"]), float(projects[project_id]["longitude"]))
            self.assertAlmostEqual(actual[0], expected[0], places=7, msg=project_id)
            self.assertAlmostEqual(actual[1], expected[1], places=7, msg=project_id)

    def test_firke_components_follow_the_parent_location(self) -> None:
        components = [
            row for row in read_rows(ROOT / "project_components.csv")
            if row["project_id"] == "PRJ-000011"
        ]
        self.assertEqual(len(components), 2)
        for row in components:
            self.assertAlmostEqual(float(row["latitude"]), EXPECTED["PRJ-000011"][0], places=7)
            self.assertAlmostEqual(float(row["longitude"]), EXPECTED["PRJ-000011"][1], places=7)

    def test_coordinate_audit_is_complete_and_field_specific(self) -> None:
        audit = read_rows(AUDIT)
        self.assertEqual(len(audit), len(EXPECTED))
        self.assertEqual({row["project_id"] for row in audit}, set(EXPECTED))
        for row in audit:
            self.assertEqual(row["coordinate_verification_status"], "VERIFIED")
            self.assertIn("does not verify", row["notes"])


if __name__ == "__main__":
    unittest.main()
