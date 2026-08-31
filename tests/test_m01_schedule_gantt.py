from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "data" / "m01_schedule_gantt.json"


class M01ScheduleGanttTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(DATA.read_text(encoding="utf-8"))

    def test_contract_and_sample_are_public_safe(self) -> None:
        self.assertEqual(self.payload["module"], "M01_SCHEDULE_GANTT")
        self.assertEqual(self.payload["schema_version"], "1.0")
        self.assertEqual(self.payload["dataset_status"], "SYNTHETIC_DEMO_NOT_LIVE_SITE_DATA")
        self.assertGreaterEqual(len(self.payload["projects"]), 1)

        forbidden = {"phone", "email", "supplier_balance", "boq_rate", "contract_value", "password", "token", "secret"}
        blob = json.dumps(self.payload).lower()
        for key in forbidden:
            self.assertNotIn(f'"{key}"', blob)

    def test_project_and_work_contract(self) -> None:
        allowed_statuses = {"NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ON_HOLD", "BLOCKED", "NOT_APPLICABLE"}
        for project in self.payload["projects"]:
            for field in ["canonical_project_id", "company_project_code", "project_name", "overall_progress_percent", "update_date", "source_status", "works"]:
                self.assertIn(field, project)
            self.assertTrue(0 <= float(project["overall_progress_percent"]) <= 100)
            date.fromisoformat(project["update_date"])

            ids = []
            sequences = []
            for work in project["works"]:
                for field in ["work_id", "work_name", "sequence", "planned_start", "planned_finish", "status", "progress_percent", "milestone", "note"]:
                    self.assertIn(field, work)
                self.assertIn(work["status"], allowed_statuses)
                self.assertTrue(0 <= float(work["progress_percent"]) <= 100)
                self.assertLessEqual(date.fromisoformat(work["planned_start"]), date.fromisoformat(work["planned_finish"]))
                if work.get("actual_finish"):
                    date.fromisoformat(work["actual_finish"])
                ids.append(work["work_id"])
                sequences.append(int(work["sequence"]))

            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(sequences), len(set(sequences)))

    def test_map_wires_m01_before_legacy_prototype(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        m01 = 'assets/js/m01-schedule-gantt.js'
        legacy = 'assets/js/site-operations-prototype.js'
        self.assertIn(m01, html)
        self.assertIn(legacy, html)
        self.assertLess(html.index(m01), html.index(legacy))

    def test_m01_renderer_keeps_existing_site_ops_contract(self) -> None:
        source = (ROOT / "assets" / "js" / "m01-schedule-gantt.js").read_text(encoding="utf-8")
        self.assertIn('data-site-ops-schedule', source)
        self.assertIn('M01_SCHEDULE_GANTT', source)
        self.assertIn('SYNTHETIC DEMO — NOT LIVE SITE DATA', source)
        self.assertIn('M01', source)

    def test_m01_observer_does_not_watch_its_own_render_panel(self) -> None:
        source = (ROOT / "assets" / "js" / "m01-schedule-gantt.js").read_text(encoding="utf-8")
        initialize = source[source.index("function initializeM01()"):]
        initialize = initialize[:initialize.index("initializeM01();")]
        self.assertIn('document.getElementById("detail-code")', initialize)
        self.assertNotIn('document.getElementById("panel-works")', initialize)

    def test_m01_to_resource_bridge_is_explicit(self) -> None:
        m01 = (ROOT / "assets" / "js" / "m01-schedule-gantt.js").read_text(encoding="utf-8")
        legacy = (ROOT / "assets" / "js" / "site-operations-prototype.js").read_text(encoding="utf-8")

        self.assertIn('new CustomEvent("jp:m01-work-selected"', m01)
        self.assertIn('window.addEventListener("jp:m01-work-selected"', legacy)
        self.assertIn("selectedDemoWorkId = workId", legacy)
        self.assertIn('document.getElementById("tab-materials")?.click()', legacy)

    def test_workflow_syntax_checks_m01(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate-projects.yml").read_text(encoding="utf-8")
        self.assertIn("node --check assets/js/m01-schedule-gantt.js", workflow)


if __name__ == "__main__":
    unittest.main()
