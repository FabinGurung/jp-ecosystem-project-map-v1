# Validation Report

Validated: 26 July 2026  
Package: `1.2.0-dev`  
Data schema: `2.0.0`

## Result

- Data validation errors: **0**
- Intentional data warnings: **14**
- Python regression tests: **3 passed**
- JavaScript unit tests: **3 passed**
- HTML conformance errors: **0**
- JavaScript syntax errors: **0**
- Real-browser desktop QA: **passed**
- Real-browser mobile QA: **passed**
- Serious/critical automated accessibility violations: **0**
- Required static files served over HTTP: **14 of 14 passed**

## Intentional warnings

Each of the seven projects has:

- blank `project_sector`
- blank `implementation_mechanism`

That produces fourteen warnings. These are accepted because the stable source
does not establish those facts and the project rules prohibit guessing them.

## Browser interactions verified

- seven list items
- seven company-code marker labels
- marker/list shared selection
- operational detail opening
- Overview, Works, and Materials tabs
- empty verified-work state
- private-inventory state
- company filtering
- legacy-code search
- project-list collapse and map expansion
- desktop layout
- mobile map-first layout
- mobile fixed bottom sheet
- no horizontal overflow at tested desktop/mobile widths

OpenStreetMap tile requests were replaced with local blank test tiles during
automated browser QA. The Leaflet 1.9.4 CSS and JavaScript used by production
were loaded and exercised. The existing external tile provider configuration
is unchanged from v1.1.

## Privacy result

The package contains no:

- password, API key, or access token
- `.env` file
- phone/email/citizenship/bank field
- detailed BOQ rate or amount row
- funding amount row
- inventory quantity row
- unverified project-party person row

This report describes the packaged source state; every future data update must
be validated again.
