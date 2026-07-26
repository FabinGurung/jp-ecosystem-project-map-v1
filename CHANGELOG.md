# Changelog

All notable changes to the JP Ecosystem Project Map are recorded here.

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
