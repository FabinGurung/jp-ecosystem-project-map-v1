from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SiteOperationsPrototypeTests(unittest.TestCase):
    def test_ceo_tabs_and_assets_are_wired(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Schedule &amp; Progress", html)
        self.assertIn(">Resources <", html)
        self.assertIn("assets/css/site-operations-prototype.css", html)
        self.assertIn("assets/js/site-operations-prototype.js", html)

    def test_demo_is_explicit_and_scoped(self) -> None:
        source = (ROOT / "assets/js/site-operations-prototype.js").read_text(encoding="utf-8")
        self.assertIn('const DEMO_PROJECT_CODE = "FBL-005";', source)
        self.assertIn("SYNTHETIC DEMO — NOT LIVE SITE DATA", source)
        self.assertIn("These schedule, progress, equipment and stock values are not read from Drive", source)
        for work_id in ["WRK-000005", "WRK-000006", "WRK-000011", "WRK-000013", "WRK-000016", "WRK-000009"]:
            self.assertIn(work_id, source)

    def test_private_inventory_gate_remains_closed(self) -> None:
        config = json.loads((ROOT / "map-config.json").read_text(encoding="utf-8"))
        self.assertFalse(config["features"]["show_inventory_quantities"])
        app = (ROOT / "assets/js/app.js").read_text(encoding="utf-8")
        self.assertIn("function materialQuantitiesAllowed(project)", app)
        self.assertIn('visibility === "PUBLIC"', app)

    def test_no_live_schedule_or_inventory_rows_are_committed(self) -> None:
        for filename in ["project_work_items.csv", "project_material_inventory.csv"]:
            with (ROOT / filename).open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [], f"{filename} should remain header-only in the public prototype")

    def test_workflow_validates_new_branch_and_module(self) -> None:
        workflow = (ROOT / ".github/workflows/validate-projects.yml").read_text(encoding="utf-8")
        self.assertIn("v1.2-site-operations-dashboard", workflow)
        self.assertIn("node --check assets/js/site-operations-prototype.js", workflow)


if __name__ == "__main__":
    unittest.main()
