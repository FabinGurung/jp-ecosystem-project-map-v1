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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("write_rows requires at least one row")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class RepositoryValidationTests(unittest.TestCase):
    def test_current_repository_has_no_validation_errors(self) -> None:
        result = validate_repository(ROOT)
        self.assertEqual([], result.errors)
        self.assertEqual(28, result.row_counts["projects"])
        self.assertEqual(9, result.row_counts["organizations"])
        self.assertEqual(28, result.row_counts["project_parties"])
        self.assertEqual(18, result.row_counts["project_funding"])
        self.assertEqual(5, result.row_counts["project_components"])
        self.assertEqual(4, result.row_counts["project_source_links"])
        self.assertEqual(1, result.row_counts["project_opportunities"])
        self.assertEqual(1, result.row_counts["organization_locations"])
        self.assertEqual(28, result.row_counts["project_publication_settings"])
        self.assertEqual(29, result.row_counts["work_catalog"])

    def test_protected_v1_1_identifiers_and_optional_legacy_codes(self) -> None:
        rows = read_rows(ROOT / "projects.csv")

        protected_actual = [
            (
                row["project_id"],
                row["company_project_code"],
                row["legacy_project_code"],
                row["executing_company_id"],
            )
            for row in rows[:7]
        ]
        protected_expected = [
            ("PRJ-000001", "REB-001", "P001", "ORG-000002"),
            ("PRJ-000002", "FBL-001", "P002", "ORG-000001"),
            ("PRJ-000003", "FBL-002", "P003", "ORG-000001"),
            ("PRJ-000004", "FBL-003", "P004", "ORG-000001"),
            ("PRJ-000005", "FBL-004", "P005", "ORG-000001"),
            ("PRJ-000006", "FBL-005", "P006", "ORG-000001"),
            ("PRJ-000007", "FBL-006", "P007", "ORG-000001"),
        ]
        self.assertEqual(protected_expected, protected_actual)

        self.assertEqual(
            [""] * 21,
            [row["legacy_project_code"] for row in rows[7:]],
        )

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

    def test_component_foreign_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_root = Path(temporary_directory) / "repository"
            shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git"))
            path = copy_root / "project_components.csv"
            rows = read_rows(path)
            rows[0]["project_id"] = "PRJ-999999"
            write_rows(path, rows)

            result = validate_repository(copy_root)
            messages = [issue.message for issue in result.errors]
            self.assertTrue(
                any(
                    "project_id 'PRJ-999999' does not exist" in message
                    for message in messages
                )
            )

    def test_publication_setting_is_required_for_every_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_root = Path(temporary_directory) / "repository"
            shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git"))
            path = copy_root / "project_publication_settings.csv"
            rows = read_rows(path)
            removed_project_id = rows[-1]["project_id"]
            write_rows(path, rows[:-1])

            result = validate_repository(copy_root)
            messages = [issue.message for issue in result.errors]
            self.assertTrue(
                any(
                    removed_project_id in message
                    and "missing publication settings" in message
                    for message in messages
                )
            )

    def test_ward_budget_funder_must_match_project_ward(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_root = Path(temporary_directory) / "repository"
            shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git"))
            path = copy_root / "project_funding.csv"
            rows = read_rows(path)
            rows[0]["funding_party_id"] = "ORG-000005"
            write_rows(path, rows)

            result = validate_repository(copy_root)
            messages = [issue.message for issue in result.errors]
            self.assertTrue(
                any(
                    "funder ward_number must match" in message
                    for message in messages
                )
            )

    def test_not_awarded_opportunity_cannot_have_awarded_company(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_root = Path(temporary_directory) / "repository"
            shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git"))
            path = copy_root / "project_opportunities.csv"
            rows = read_rows(path)
            rows[0]["awarded_company_id"] = "ORG-000001"
            write_rows(path, rows)

            result = validate_repository(copy_root)
            messages = [issue.message for issue in result.errors]
            self.assertTrue(
                any(
                    "NOT_AWARDED opportunity must not contain awarded_company_id"
                    in message
                    for message in messages
                )
            )


if __name__ == "__main__":
    unittest.main()
