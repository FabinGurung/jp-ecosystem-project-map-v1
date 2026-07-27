# JP Ecosystem Operational Project Map

A public, data-driven construction-project map for the JP Ecosystem in Nepal.

This package is the development candidate for:

- Application version: `1.2.0-dev`
- Data schema version: `2.0.0`
- Stable predecessor: `v1.1.0` at commit `9c51563`
- Development branch: `v1.2-operational-map`

The existing `v1.1.0` release and tag must remain unchanged.

## What v1.2 adds

- Immutable global project IDs such as `PRJ-000001`
- Human-facing company project codes such as `REB-001` and `FBL-001`
- Preserved legacy codes `P001`–`P007`
- Reusable organization and person masters
- Normalized project-party relationships
- Separate funding, works, and material-inventory structures
- Operational project drawer with Overview, Works, and Materials tabs
- Desktop drawer and mobile bottom sheet
- Company-code marker labels
- Public-data privacy controls
- Cross-file primary-key and foreign-key validation
- Detection of Excel errors such as `#REF!`
- Repeatable Python and JavaScript tests

No unverified BOQ group or material quantity has been assigned to a project.

## Application architecture

```text
index.html
├── assets/css/app.css
├── assets/js/csv.js
├── assets/js/app.js
├── map-config.json
└── normalized public CSV files
    ├── projects.csv
    ├── organizations.csv
    ├── people.csv
    ├── project_parties.csv
    ├── project_funding.csv
    ├── work_catalog.csv
    ├── project_work_items.csv
    ├── materials_master.csv
    └── project_material_inventory.csv
```

This remains a static website. It needs no npm build, database, API key, or
server-side application. GitHub Pages serves the files directly.

## Important: do not double-click `index.html`

The website loads CSV and JSON files with `fetch()`. Most browsers block those
requests when `index.html` is opened as a `file://` page.

Use one of these:

1. GitHub Pages after uploading the package; or
2. `START_LOCAL_SERVER_WINDOWS.bat`; or
3. `python serve-local.py`.

## Current verified project migration

| Global ID | Map code | Legacy code | Project | Company |
|---|---|---|---|---|
| PRJ-000001 | REB-001 | P001 | 14 Bishal Paija | Rohini Engineering and Builders Pvt Ltd |
| PRJ-000002 | FBL-001 | P002 | 17 Samir Man Ghubaju | Fishtail Builders Pvt Ltd |
| PRJ-000003 | FBL-002 | P003 | 13 Hari Baral | Fishtail Builders Pvt Ltd |
| PRJ-000004 | FBL-003 | P004 | 16 Yamuna Pun Adai | Fishtail Builders Pvt Ltd |
| PRJ-000005 | FBL-004 | P005 | 30 Sabitri Giri / Dipti Giri | Fishtail Builders Pvt Ltd |
| PRJ-000006 | FBL-005 | P006 | 31 Sharada Adhikari | Fishtail Builders Pvt Ltd |
| PRJ-000007 | FBL-006 | P007 | 15 Narayani Parajuli | Fishtail Builders Pvt Ltd |

These mappings were derived directly from the stable `v1.1.0` `projects.csv`.

## Routine public project update

For a simple project status, coordinate, or approved public-update change:

1. Edit `projects.csv`.
2. Keep `project_id`, `company_project_code`, and `legacy_project_code`
   unchanged for an existing project.
3. Use `YYYY-MM-DD` dates.
4. Use a status defined in `map-config.json`.
5. Run `python scripts/validate_data.py`.
6. Commit only after validation reports zero errors.

## Public repository warning

Every file committed here is publicly downloadable. `is_public=FALSE` hides a
row from the interface; it does **not** make the row private.

Do not commit:

- private phone numbers or email addresses
- citizenship or personal identity numbers
- detailed confidential BOQ rates or amounts
- exact internal material stock unless explicitly approved
- supplier balances or internal payments
- bank details
- contracts or documents not approved for publication
- passwords, API keys, tokens, or secrets

Use an authenticated Supabase/PostgreSQL application later for internal
operational data.

## Validation

Run:

```bash
python scripts/validate_data.py
python -m unittest discover -s tests -p "test_*.py"
node --test tests/*.test.mjs
```

The GitHub Action performs the same validation. It validates data only; it is
not a Pages deployment workflow.

Warnings for blank `project_sector` and `implementation_mechanism` are
intentional. Unknown facts stay blank until verified.

## Main documentation

- [`START_HERE.md`](START_HERE.md) — package orientation
- [`PACKAGE_MANIFEST.md`](PACKAGE_MANIFEST.md) — complete package contents
- [`VALIDATION_REPORT.md`](VALIDATION_REPORT.md) — final QA evidence
- [`GITHUB_INSTALLATION_GUIDE.md`](GITHUB_INSTALLATION_GUIDE.md) — complete upload and release steps
- [`MOBILE_EDITING_GUIDE.md`](MOBILE_EDITING_GUIDE.md) — safe iPhone updates
- [`docs/V1_2_SYSTEM_DESIGN.md`](docs/V1_2_SYSTEM_DESIGN.md) — audit, relationships, government model, migration, and implementation plan
- [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) — field-by-field schema and privacy classification
- [`docs/DATA_ENTRY_GUIDE.md`](docs/DATA_ENTRY_GUIDE.md) — normal-user editing instructions
- [`docs/TESTING_CHECKLIST.md`](docs/TESTING_CHECKLIST.md) — desktop, mobile, data, and privacy checks
- [`CHANGELOG.md`](CHANGELOG.md) — version history

## GitHub Pages

Keep the current deployment model:

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/ (root)`

Do not replace this with an unnecessary Pages Action. After v1.2 is reviewed,
merge the development branch into `main`; GitHub Pages will republish.
