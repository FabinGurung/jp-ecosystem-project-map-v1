# Package Manifest

Package: JP Ecosystem Operational Project Map  
Application: `1.2.0-dev`  
Data schema: `2.0.0`  
Stable source baseline: `v1.1.0` / commit `9c51563`

## Root application

| File | Purpose |
|---|---|
| `index.html` | Accessible application shell |
| `map-config.json` | Versions, data paths, controlled values, map settings, privacy switches |
| `assets/css/app.css` | Desktop, tablet, and mobile styling |
| `assets/js/csv.js` | Tested CSV parser and primitive converters |
| `assets/js/app.js` | Data loading, map, filters, project state, drawer/sheet, tabs, GeoJSON |
| `.nojekyll` | Direct GitHub Pages static serving |

## Public normalized data

| File | Current rows | Purpose |
|---|---:|---|
| `projects.csv` | 7 | Mapped projects with global/company/legacy IDs |
| `organizations.csv` | 2 | FBL and REB organization masters |
| `people.csv` | 0 | Empty public-safe person master |
| `project_parties.csv` | 7 | Verified contractor relationships |
| `project_funding.csv` | 0 | Empty funding relationship schema |
| `work_catalog.csv` | 29 | Reusable work descriptions |
| `project_work_items.csv` | 0 | Empty project BOQ/progress schema |
| `materials_master.csv` | 11 | Reusable material definitions |
| `project_material_inventory.csv` | 0 | Empty inventory snapshot schema |

Zero-row files are intentional. Unknown records were not fabricated.

## Validation and tests

| File | Purpose |
|---|---|
| `scripts/validate_data.py` | Cross-file schema, PK/FK, coordinate, numeric, date, quality, and privacy validation |
| `scripts/__init__.py` | Python package marker |
| `tests/test_validator.py` | Validation and exact ID-migration regression tests |
| `tests/csv.test.mjs` | JavaScript CSV parser tests |
| `.github/workflows/validate-projects.yml` | GitHub QA workflow; not a deployment workflow |

## Human guides

| File | Purpose |
|---|---|
| `START_HERE.md` | Fast package orientation |
| `GITHUB_INSTALLATION_GUIDE.md` | Detailed existing-repository upload, branch, PR, Pages, and release steps |
| `README.md` | Technical and operational overview |
| `MOBILE_EDITING_GUIDE.md` | Safe iPhone editing |
| `MIGRATION_CHECKLIST.md` | v1.1→v1.2 migration controls |
| `CHANGELOG.md` | Preserved v1.1 history plus v1.2 changes |
| `docs/V1_2_SYSTEM_DESIGN.md` | Repository/data audit, ER model, government model, works/materials, privacy, and migration |
| `docs/DATA_DICTIONARY.md` | Field-level datatypes, requirements, FKs, controls, and privacy |
| `docs/DATA_ENTRY_GUIDE.md` | Plain-language update instructions |
| `docs/TESTING_CHECKLIST.md` | Desktop, mobile, data, privacy, and release tests |

## Local preview

| File | Purpose |
|---|---|
| `serve-local.py` | Dependency-free local static server |
| `START_LOCAL_SERVER_WINDOWS.bat` | Double-click Windows launcher |

## Deliberately excluded

- `.git` history and credentials
- GitHub access tokens
- `.env` files
- dependencies or `node_modules`
- private contacts and identity data
- confidential BOQ values
- internal financial records
- unapproved material stock
- artificial sample project assignments
