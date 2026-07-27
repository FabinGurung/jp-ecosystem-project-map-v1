# Changelog

All notable changes to the JP Ecosystem Project Map are recorded here.

## [v1.2.0-dev] — Operational Project Map

### Added

- Immutable global project IDs (`PRJ-000001` format)
- Human-facing company project codes (`REB-001`, `FBL-001`, etc.)
- Preserved legacy project codes (`P001`–`P007`)
- Stable organization records for FBL and REB
- Separate organization and person masters
- Normalized project-party relationships
- Project-funding schema independent from implementation
- Reusable 29-item work catalog
- Project work-item and BOQ/progress schema
- Reusable 11-item material master
- Project material-inventory snapshot schema
- Data provenance and quality fields
- Desktop operational project drawer
- Mobile operational bottom sheet
- Overview, Works, and Materials tabs
- Shared active-project state between map markers and project list
- Company-code marker labels
- Public-safe GeoJSON export
- Expanded cross-file validator
- Spreadsheet-error detection for `#REF!`, `#VALUE!`, `#DIV/0!`, and related values
- Python and JavaScript regression tests
- Local preview server
- Detailed schema, data-entry, testing, migration, and GitHub installation guides

### Changed

- Application code split into maintainable HTML, CSS, and JavaScript files
- Project primary key migrated from legacy `PK_ID` to canonical `project_id`
- Contractor-name comparison replaced by organization IDs
- Search expanded to global, company, and legacy codes
- Contractor filter evolved into a stable company-ID filter
- Data schema version increased from `1.0.0` to `2.0.0`
- Validation workflow expanded without becoming a Pages deployment workflow

### Privacy

- Exact public inventory display is disabled by default
- Financial progress display is disabled by default
- Rate and amount display is disabled by default
- Obvious private-contact and secret columns are rejected by validation
- Documentation states that hidden rows remain downloadable in a public repository

### Data integrity

- Seven existing project/company assignments were verified from v1.1.0
- No project sector or implementation mechanism was invented
- No source BOQ group was assigned to a project without verified association
- No material quantity or storage location was invented
- Factor is preserved only with definition `TO_BE_CONFIRMED`

### Status

Development candidate. Keep on `v1.2-operational-map` until review and testing
are complete. Promote `app_version` to `1.2.0` immediately before the approved
merge and release.

## [v1.1.0] — 2026-07-26

### Added

- Data-driven architecture using `projects.csv`
- Central map configuration using `map-config.json`
- Search by project ID, project name, and contractor
- Status filtering
- Contractor filtering
- Public project list
- Status-coloured project markers
- Marker popups
- Google Maps directions
- GeoJSON download
- Responsive desktop and mobile interface
- Automatic project-data validation through GitHub Actions

### Fixed

- Corrected Leaflet CSS integrity configuration
- Fixed broken and disconnected map-tile rendering
- Added Leaflet resize handling for changing browser and mobile viewport sizes
- Improved mobile map layout

### Architecture

- `projects.csv` — public project information
- `map-config.json` — map settings, statuses, and visual configuration
- `index.html` — map application and interface
- GitHub Pages — website hosting
- `.github/workflows/validate-projects.yml` — project-data validation

### Status

Stable baseline for future development of the JP Ecosystem Project Map.
