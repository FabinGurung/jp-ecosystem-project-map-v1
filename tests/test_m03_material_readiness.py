from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M03_DATA = ROOT / "assets" / "data" / "m03_material_readiness.json"
M01_DATA = ROOT / "assets" / "data" / "m01_schedule_gantt.json"
MATERIALS = ROOT / "materials_master.csv"


class M03MaterialReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(M03_DATA.read_text(encoding="utf-8"))

    def test_contract_and_sample_are_explicitly_synthetic_public_safe(self) -> None:
        self.assertEqual(self.payload["module"], "M03_MATERIAL_QUANTITY_READINESS")
        self.assertEqual(self.payload["schema_version"], "1.0")
        self.assertEqual(self.payload["dataset_status"], "SYNTHETIC_UI_EVIDENCE_NOT_LIVE_INVENTORY")
        blob = json.dumps(self.payload).lower()
        for forbidden in ["phone", "email", "supplier_balance", "boq_rate", "contract_value", "password", "token", "secret", "drive.google.com"]:
            self.assertNotIn(forbidden, blob)

    def test_required_fields_and_allowed_states(self) -> None:
        allowed = {"READY", "SHORT", "MISSING", "UNKNOWN", "NOT_APPLICABLE"}
        required = {
            "work_id", "work_name", "material_id", "material_name", "required_quantity",
            "available_quantity", "unit", "readiness_status", "evidence_note", "evidence_reference"
        }
        for project in self.payload["projects"]:
            self.assertTrue(project["canonical_project_id"])
            self.assertTrue(project["company_project_code"])
            self.assertTrue(project["work_materials"])
            for row in project["work_materials"]:
                self.assertTrue(required.issubset(row))
                self.assertIn(row["readiness_status"], allowed)
                self.assertTrue(row["evidence_note"].strip())
                self.assertTrue(row["evidence_reference"].strip())

    def test_unknown_rows_do_not_smuggle_numeric_zero_or_unreconciled_units(self) -> None:
        unknown_rows = [
            row
            for project in self.payload["projects"]
            for row in project["work_materials"]
            if row["readiness_status"] == "UNKNOWN"
        ]
        self.assertGreaterEqual(len(unknown_rows), 1)
        for row in unknown_rows:
            self.assertIsNone(row["required_quantity"])
            self.assertIsNone(row["available_quantity"])
            self.assertIsNone(row["unit"])

    def test_known_readiness_invariants(self) -> None:
        for project in self.payload["projects"]:
            for row in project["work_materials"]:
                status = row["readiness_status"]
                if status in {"READY", "SHORT", "MISSING"}:
                    req = float(row["required_quantity"])
                    avail = float(row["available_quantity"])
                    self.assertGreater(req, 0)
                    self.assertTrue(row["unit"])
                    if status == "READY":
                        self.assertGreaterEqual(avail, req)
                    elif status == "SHORT":
                        self.assertGreater(avail, 0)
                        self.assertLess(avail, req)
                    elif status == "MISSING":
                        self.assertEqual(avail, 0)

    def test_canonical_material_ids_exist_in_material_master(self) -> None:
        with MATERIALS.open(encoding="utf-8", newline="") as fh:
            master = {row["material_id"]: row for row in csv.DictReader(fh)}
        for project in self.payload["projects"]:
            for row in project["work_materials"]:
                if row["material_id"] is not None:
                    self.assertIn(row["material_id"], master)

    def test_sample_work_ids_and_names_match_m01(self) -> None:
        m01 = json.loads(M01_DATA.read_text(encoding="utf-8"))
        m01_by_project = {
            p["company_project_code"]: {w["work_id"]: w["work_name"] for w in p["works"]}
            for p in m01["projects"]
        }
        for project in self.payload["projects"]:
            work_names = m01_by_project[project["company_project_code"]]
            for row in project["work_materials"]:
                self.assertIn(row["work_id"], work_names)
                self.assertEqual(row["work_name"], work_names[row["work_id"]])

    def test_index_wires_m03_after_m02_before_legacy_prototype(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m02 = 'assets/js/m02-progress-report.js'
        m03 = 'assets/js/m03-material-readiness.js'
        legacy = 'assets/js/site-operations-prototype.js'
        self.assertIn(m02, html)
        self.assertIn(m03, html)
        self.assertIn(legacy, html)
        self.assertLess(html.index(m02), html.index(m03))
        self.assertLess(html.index(m03), html.index(legacy))

    def test_m03_owns_material_tab_and_legacy_resource_renderer_is_suppressed(self) -> None:
        m03 = (ROOT / "assets" / "js" / "m03-material-readiness.js").read_text(encoding="utf-8")
        legacy = (ROOT / "assets" / "js" / "site-operations-prototype.js").read_text(encoding="utf-8")
        self.assertIn("JP_M03_MATERIAL_READINESS_ACTIVE", m03)
        self.assertIn('window.addEventListener("jp:m01-work-selected", handleM03WorkSelected)', m03)
        self.assertIn("JP_M03_MATERIAL_READINESS_ACTIVE", legacy)
        self.assertIn("renderResourcePrototype", legacy)

    def test_m03_renderer_never_converts_missing_values_to_zero(self) -> None:
        source = (ROOT / "assets" / "js" / "m03-material-readiness.js").read_text(encoding="utf-8")
        self.assertIn('return "UNKNOWN"', source)
        self.assertNotIn("Number(value) || 0", source)
        self.assertNotIn("available_quantity || 0", source)
        self.assertNotIn("required_quantity || 0", source)

    def test_workflow_syntax_checks_m03(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate-projects.yml").read_text(encoding="utf-8")
        self.assertIn("node --check assets/js/m03-material-readiness.js", workflow)


if __name__ == "__main__":
    unittest.main()
