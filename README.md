# JP Ecosystem Project Map

A public, coordinate-verified project map hosted with GitHub Pages.

## Live architecture

```text
index.html
├── loads map-config.json
├── loads projects.csv
├── creates filters, project list, markers and popups
└── downloads filtered data as GeoJSON
```

The live website no longer stores project records inside `index.html`.

## Routine update

For ordinary changes, edit only:

```text
projects.csv
```

Examples:

- Add a project
- Change a status
- Correct coordinates
- Update contractor
- Add progress percentages
- Add a latest update
- Hide a record by setting `is_public` to `FALSE`

GitHub Pages republishes after the commit reaches `main`.

## Files

- `index.html` — map interface and logic
- `projects.csv` — live public project dataset
- `map-config.json` — title, map settings and status colours
- `.github/workflows/validate-projects.yml` — automatic validation
- `MOBILE_EDITING_GUIDE.md` — iPhone editing instructions
- `.nojekyll` — tells GitHub Pages to serve files directly

## Coordinate rules

- CSV columns: `latitude` and `longitude`
- Leaflet uses `[latitude, longitude]`
- GeoJSON uses `[longitude, latitude]`

Never swap the order.

## Dates

Use `YYYY-MM-DD`, for example `2026-07-23`.

## Status values

The status must exactly match a key in `map-config.json`:

- Construction
- Completed
- Approval
- Planned
- On Hold
- Cancelled

## Public/private rule

GitHub Pages and this repository are public. Only public information belongs in `projects.csv`.

`is_public=FALSE` hides a record from the map, but does not secure it because the CSV remains public. Remove genuinely sensitive information from the public repository.

## Safe change workflow

For tiny corrections, editing `projects.csv` directly on `main` is acceptable.

For larger changes:

1. Create a branch.
2. Make changes.
3. Open a pull request.
4. Confirm validation is green.
5. Merge into `main`.
6. GitHub Pages republishes automatically.
