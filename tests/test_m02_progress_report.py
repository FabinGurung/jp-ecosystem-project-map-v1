from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M02_DATA = ROOT / "assets" / "data" / "m02_progress_report.json"
M01_DATA = ROOT / "assets" / "data" / "m01_schedule_gantt.json"


class M02ProgressReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(M02_DATA.read_text(encoding="utf-8"))

    def test_contract_and_sample_are_public_safe(self) -> None:
        self.assertEqual(self.payload["module"], "M02_PROGRESS_REPORT")
        self.assertEqual(self.payload["schema_version"], "1.0")
        self.assertEqual(self.payload["dataset_status"], "SYNTHETIC_DEMO_NOT_LIVE_SITE_DATA")
        self.assertGreaterEqual(len(self.payload["projects"]), 1)
        forbidden = {"phone", "email", "supplier_balance", "boq_rate", "contract_value", "password", "token", "secret"}
        blob = json.dumps(self.payload).lower()
        for key in forbidden:
            self.assertNotIn(f'"{key}"', blob)

    def test_required_progress_contract(self) -> None:
        allowed = {"NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ON_HOLD", "BLOCKED", "NOT_APPLICABLE"}
        for project in self.payload["projects"]:
            for field in ["canonical_project_id", "company_project_code", "project_name", "update_date", "source_status", "progress_updates"]:
                self.assertIn(field, project)
            date.fromisoformat(project["update_date"])
            ids = []
            for update in project["progress_updates"]:
                for field in ["work_id", "work_name", "progress_percent", "status", "update_date", "evidence_note", "evidence_reference"]:
                    self.assertIn(field, update)
                    self.assertNotEqual(str(update[field]).strip(), "")
                self.assertIn(update["status"], allowed)
                self.assertTrue(0 <= float(update["progress_percent"]) <= 100)
                date.fromisoformat(update["update_date"])
                ids.append(update["work_id"])
            self.assertEqual(len(ids), len(set(ids)))

    def test_status_progress_invariants(self) -> None:
        for project in self.payload["projects"]:
            for update in project["progress_updates"]:
                if update["status"] == "COMPLETED":
                    self.assertEqual(float(update["progress_percent"]), 100)
                if update["status"] == "NOT_STARTED":
                    self.assertEqual(float(update["progress_percent"]), 0)

    def test_m02_sample_uses_m01_shared_work_ids(self) -> None:
        m01 = json.loads(M01_DATA.read_text(encoding="utf-8"))
        m01_by_project = {
            p["company_project_code"]: {w["work_id"]: w["work_name"] for w in p["works"]}
            for p in m01["projects"]
        }
        for project in self.payload["projects"]:
            self.assertIn(project["company_project_code"], m01_by_project)
            work_names = m01_by_project[project["company_project_code"]]
            for update in project["progress_updates"]:
                self.assertIn(update["work_id"], work_names)
                self.assertEqual(update["work_name"], work_names[update["work_id"]])

    def test_map_wires_m02_after_m01_before_legacy_prototype(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m01 = 'assets/js/m01-schedule-gantt.js'
        m02 = 'assets/js/m02-progress-report.js'
        legacy = 'assets/js/site-operations-prototype.js'
        self.assertIn(m01, html)
        self.assertIn(m02, html)
        self.assertIn(legacy, html)
        self.assertLess(html.index(m01), html.index(m02))
        self.assertLess(html.index(m02), html.index(legacy))

    def test_m02_renderer_is_separate_from_m01_render_root(self) -> None:
        source = (ROOT / "assets" / "js" / "m02-progress-report.js").read_text(encoding="utf-8")
        self.assertIn('data-site-ops-progress', source)
        self.assertIn('data-m02', source)
        self.assertNotIn('root.dataset.siteOpsSchedule', source)

    def test_m02_observer_does_not_watch_its_own_render_panel(self) -> None:
        source = (ROOT / "assets" / "js" / "m02-progress-report.js").read_text(encoding="utf-8")
        initialize = source[source.index("function initializeM02()"):]
        initialize = initialize[:initialize.index("initializeM02();")]
        self.assertIn('document.getElementById("detail-code")', initialize)
        self.assertNotIn('document.getElementById("panel-works")', initialize)

    def test_workflow_syntax_checks_m02(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate-projects.yml").read_text(encoding="utf-8")
        self.assertIn("node --check assets/js/m02-progress-report.js", workflow)


if __name__ == "__main__":
    unittest.main()
