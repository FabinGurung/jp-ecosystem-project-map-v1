from __future__ import annotations

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRST_AUDIT = ROOT / "imports/photo-groups-2026-08-02/coordinate_corrections_2026-08-04.csv"
SECOND_REVIEW = ROOT / "imports/photo-groups-2026-08-02/coordinate_reviews_2026-08-05.csv"

EXPECTED_PROJECTS = {
    "PRJ-000001": (28.2006670, 84.0182220),
    "PRJ-000002": (28.1967780, 83.9707780),
    "PRJ-000003": (28.2181667, 84.0382222),
    "PRJ-000004": (28.2555000, 83.9797500),
    "PRJ-000005": (28.1602780, 84.0825000),
    "PRJ-000006": (28.1657989, 84.1153390),
    "PRJ-000007": (28.1951080, 83.9957550),
    "PRJ-000008": (28.2257095, 83.9821248),
    "PRJ-000009": (28.2276034, 83.9844513),
    "PRJ-000010": (28.2271493, 83.9851520),
    "PRJ-000011": (28.2283378, 83.9817348),
    "PRJ-000012": (28.2285729, 83.9863023),
    "PRJ-000013": (28.2179568, 83.9764690),
    "PRJ-000014": (28.2189403, 83.9785772),
    "PRJ-000015": (28.2232024, 83.9788233),
    "PRJ-000016": (28.1994167, 83.9787500),
    "PRJ-000017": (28.2086944, 83.9596389),
    "PRJ-000018": (28.2114489, 83.9915658),
    "PRJ-000019": (28.2154589, 84.0053933),
    "PRJ-000020": (28.1929350, 84.0018950),
    "PRJ-000021": (28.1902064, 84.0112143),
    "PRJ-000022": (28.1897729, 84.0148618),
    "PRJ-000023": (28.2525690, 83.9933420),
    "PRJ-000024": (28.2519660, 83.9958840),
    "PRJ-000025": (28.2545700, 84.0088640),
    "PRJ-000026": (28.2551900, 84.0088040),
    "PRJ-000027": (28.2504660, 83.9948780),
    "PRJ-000028": (28.2504660, 83.9948780),
}

EXPECTED_COMPONENTS = {
    "PCO-000001": (28.2283378, 83.9817348),
    "PCO-000002": (28.2283378, 83.9817348),
    "PCO-000003": (28.2519660, 83.9958840),
    "PCO-000004": (28.2528610, 83.9966210),
    "PCO-000005": (28.2475750, 83.9992270),
}

def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

class CoordinateRegressionTests(unittest.TestCase):
    def test_all_canonical_project_coordinates(self) -> None:
        projects = {row["project_id"]: row for row in read_rows(ROOT / "projects.csv")}
        self.assertEqual(set(projects), set(EXPECTED_PROJECTS))
        for project_id, expected in EXPECTED_PROJECTS.items():
            actual = (float(projects[project_id]["latitude"]), float(projects[project_id]["longitude"]))
            self.assertAlmostEqual(actual[0], expected[0], places=7, msg=project_id)
            self.assertAlmostEqual(actual[1], expected[1], places=7, msg=project_id)

    def test_all_component_coordinates(self) -> None:
        components = {row["component_id"]: row for row in read_rows(ROOT / "project_components.csv")}
        self.assertEqual(set(components), set(EXPECTED_COMPONENTS))
        for component_id, expected in EXPECTED_COMPONENTS.items():
            actual = (float(components[component_id]["latitude"]), float(components[component_id]["longitude"]))
            self.assertAlmostEqual(actual[0], expected[0], places=7, msg=component_id)
            self.assertAlmostEqual(actual[1], expected[1], places=7, msg=component_id)

    def test_first_coordinate_audit_remains_intact(self) -> None:
        audit = read_rows(FIRST_AUDIT)
        self.assertEqual(len(audit), 14)
        for row in audit:
            self.assertEqual(row["coordinate_verification_status"], "VERIFIED")
            self.assertIn("does not verify", row["notes"])

    def test_second_coordinate_review_is_complete_and_field_specific(self) -> None:
        review = read_rows(SECOND_REVIEW)
        self.assertEqual(len(review), 17)
        self.assertEqual(sum(row["review_result"] == "CONFIRMED_UNCHANGED" for row in review), 5)
        self.assertEqual(sum(row["review_result"] == "CORRECTED" for row in review), 12)
        self.assertEqual(sum(row["entity_type"] == "PROJECT" for row in review), 14)
        self.assertEqual(sum(row["entity_type"] == "PROJECT_COMPONENT" for row in review), 3)
        for row in review:
            self.assertEqual(row["coordinate_verification_status"], "VERIFIED")
            self.assertIn("does not verify", row["notes"])

if __name__ == "__main__":
    unittest.main()
