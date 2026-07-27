# v1.2 Testing Checklist

## Automated validation

- [ ] `python scripts/validate_data.py` reports 0 errors.
- [ ] Python unit tests pass.
- [ ] JavaScript CSV tests pass.
- [ ] JavaScript syntax checks pass.
- [ ] GitHub Action is green on the development branch.
- [ ] No literal `#REF!`, `#VALUE!`, `#DIV/0!`, or `#N/A` exists in data.
- [ ] No duplicate primary key exists.
- [ ] No orphan foreign key exists.
- [ ] No invalid coordinate exists.
- [ ] No percentage is outside 0–100.
- [ ] No unsupported controlled value exists.

## Desktop

- [ ] Open the site through the local server, not `file://`.
- [ ] Leaflet CSS and JavaScript load.
- [ ] OpenStreetMap tiles remain connected.
- [ ] All seven public projects load.
- [ ] Marker labels show `REB-001` and `FBL-001` through `FBL-006`.
- [ ] Search finds a project by global ID.
- [ ] Search finds a project by company code.
- [ ] Search finds a project by legacy code.
- [ ] Search finds a project by name.
- [ ] Search finds a project by company name.
- [ ] Status filter works.
- [ ] Company filter works.
- [ ] Reset works.
- [ ] Clicking a list item focuses the matching marker.
- [ ] Clicking a marker activates the matching list item.
- [ ] Popup stays compact.
- [ ] View Project opens the detail drawer.
- [ ] Overview shows known fields and omits unnecessary blank rows.
- [ ] Works explains that no project BOQ is assigned.
- [ ] Materials explains that public quantities are disabled.
- [ ] Directions opens the selected coordinate.
- [ ] GeoJSON downloads.
- [ ] GeoJSON coordinates are `[longitude, latitude]`.
- [ ] Closing/reopening the detail drawer does not break map sizing.
- [ ] Browser resize does not break Leaflet.

## Mobile

- [ ] Map remains the first/prominent content.
- [ ] Filters are collapsed until requested.
- [ ] Filters button opens and closes controls.
- [ ] Project list can be shown/hidden.
- [ ] Marker tap selects the project.
- [ ] List tap selects the project.
- [ ] Bottom sheet opens.
- [ ] Overview tab is readable.
- [ ] Works tab is readable.
- [ ] Materials tab is readable.
- [ ] Bottom sheet scrolls.
- [ ] Close button works.
- [ ] Screen rotation does not split or disconnect map tiles.
- [ ] Viewport resize does not break Leaflet.
- [ ] No horizontal page overflow appears.
- [ ] Safe-area spacing works on iPhone.

## Data and privacy

- [ ] Current company assignments match v1.1.0.
- [ ] P001–P007 are preserved in `legacy_project_code`.
- [ ] Map codes match the company prefix.
- [ ] No client, manager, engineer, ward, funding, BOQ, or stock fact was guessed.
- [ ] Empty operational CSV files are intentionally empty.
- [ ] No private phone/email/identity/bank information is present.
- [ ] No API key, password, token, or secret is present.
- [ ] No detailed confidential rate or amount is present.
- [ ] No exact stock quantity is published without approval.
- [ ] `is_public=FALSE` is not treated as security.

## Release

- [ ] `main` remains v1.1 during development review.
- [ ] The `v1.1.0` tag still points to commit `9c51563`.
- [ ] Pages remains Deploy-from-branch, `main`, `/ (root)`.
- [ ] Validation workflow remains separate from Pages deployment.
- [ ] Pull request validation is green.
- [ ] App version is promoted from `1.2.0-dev` to `1.2.0` only after review.
- [ ] Release/tag `v1.2.0` is created only after merge.
