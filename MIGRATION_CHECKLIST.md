# v1.1.0 to v1.2.0 Migration Checklist

## Protect the stable release

- [ ] Confirm `main` still represents v1.1 before starting.
- [ ] Confirm tag `v1.1.0` still points to commit `9c51563`.
- [ ] Do not move, delete, or recreate `v1.1.0`.
- [ ] Do not change GitHub Pages away from `main` and `/ (root)`.
- [ ] Create/use branch `v1.2-operational-map`.

## Copy the complete package

- [ ] Replace root `index.html`.
- [ ] Replace root `projects.csv`.
- [ ] Replace root `map-config.json`.
- [ ] Add `organizations.csv`.
- [ ] Add `people.csv`.
- [ ] Add `project_parties.csv`.
- [ ] Add `project_funding.csv`.
- [ ] Add `work_catalog.csv`.
- [ ] Add `project_work_items.csv`.
- [ ] Add `materials_master.csv`.
- [ ] Add `project_material_inventory.csv`.
- [ ] Add the complete `assets` folder.
- [ ] Add the complete `docs` folder.
- [ ] Add the complete `scripts` folder.
- [ ] Add the complete `tests` folder.
- [ ] Replace `.github/workflows/validate-projects.yml`.
- [ ] Keep `.nojekyll`.
- [ ] Add root guides and local-server files.
- [ ] Confirm no extra outer package folder was created.

## Verify identity migration

- [ ] P001 → PRJ-000001 → REB-001.
- [ ] P002 → PRJ-000002 → FBL-001.
- [ ] P003 → PRJ-000003 → FBL-002.
- [ ] P004 → PRJ-000004 → FBL-003.
- [ ] P005 → PRJ-000005 → FBL-004.
- [ ] P006 → PRJ-000006 → FBL-005.
- [ ] P007 → PRJ-000007 → FBL-006.
- [ ] FBL resolves to ORG-000001.
- [ ] REB resolves to ORG-000002.
- [ ] Seven contractor relationships exist in `project_parties.csv`.

## Verify intentional blanks

- [ ] Project sector remains blank unless verified.
- [ ] Implementation mechanism remains blank unless verified.
- [ ] People file has no invented rows.
- [ ] Funding file has no invented rows.
- [ ] Project work file has no unverified BOQ assignments.
- [ ] Material inventory has no invented quantities.

## Validate

- [ ] Run `python scripts/validate_data.py`.
- [ ] Confirm zero validation errors.
- [ ] Review the 14 expected unknown-classification warnings.
- [ ] Run Python tests.
- [ ] Run JavaScript tests.
- [ ] Confirm GitHub Action is green.

## Preview and test

- [ ] Use local HTTP preview; do not double-click `index.html`.
- [ ] Complete `docs/TESTING_CHECKLIST.md`.
- [ ] Confirm all seven markers.
- [ ] Confirm company-code labels.
- [ ] Confirm search, status filter, company filter, directions, and GeoJSON.
- [ ] Confirm desktop drawer.
- [ ] Confirm mobile bottom sheet.
- [ ] Confirm Leaflet survives resize and rotation.

## Privacy

- [ ] No private contact data.
- [ ] No personal identity numbers.
- [ ] No bank data.
- [ ] No API keys, passwords, tokens, or secrets.
- [ ] No confidential rates, amounts, procurement, or supplier balances.
- [ ] No exact stock published without approval.
- [ ] Every committed CSV is safe to download publicly.

## Release

- [ ] Open pull request from `v1.2-operational-map` to `main`.
- [ ] Wait for green validation.
- [ ] Promote app version from `1.2.0-dev` to `1.2.0`.
- [ ] Update changelog release status/date.
- [ ] Merge intentionally.
- [ ] Confirm Pages deployment succeeds.
- [ ] Test the live site.
- [ ] Create tag/release `v1.2.0`.
- [ ] Reconfirm `v1.1.0` remains unchanged.
