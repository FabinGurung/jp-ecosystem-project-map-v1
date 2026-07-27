from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_data import validate_repository  # noqa: E402


class RepositoryValidationTests(unittest.TestCase):
    def test_current_repository_has_no_validation_errors(self) -> None:
        result = validate_repository(ROOT)
        self.assertEqual([], result.errors)
        self.assertEqual(7, result.row_counts["projects"])
        self.assertEqual(2, result.row_counts["organizations"])
        self.assertEqual(29, result.row_counts["work_catalog"])

    def test_project_id_migration_is_exact(self) -> None:
        with (ROOT / "projects.csv").open(
            newline="", encoding="utf-8-sig"
        ) as handle:
            rows = list(csv.DictReader(handle))

        actual = [
            (
                row["project_id"],
                row["company_project_code"],
                row["legacy_project_code"],
                row["executing_company_id"],
            )
            for row in rows
        ]
        expected = [
            ("PRJ-000001", "REB-001", "P001", "ORG-000002"),
            ("PRJ-000002", "FBL-001", "P002", "ORG-000001"),
            ("PRJ-000003", "FBL-002", "P003", "ORG-000001"),
            ("PRJ-000004", "FBL-003", "P004", "ORG-000001"),
            ("PRJ-000005", "FBL-004", "P005", "ORG-000001"),
            ("PRJ-000006", "FBL-005", "P006", "ORG-000001"),
            ("PRJ-000007", "FBL-006", "P007", "ORG-000001"),
        ]
        self.assertEqual(expected, actual)

    def test_spreadsheet_error_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_root = Path(temporary_directory) / "repository"
            shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git"))
            projects_path = copy_root / "projects.csv"
            rows = projects_path.read_text(encoding="utf-8").splitlines()
            rows[1] = rows[1].replace("28.200667", "#REF!", 1)
            projects_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

            result = validate_repository(copy_root)
            messages = [issue.message for issue in result.errors]
            self.assertTrue(
                any("spreadsheet error" in message for message in messages)
            )


if __name__ == "__main__":
    unittest.main()
