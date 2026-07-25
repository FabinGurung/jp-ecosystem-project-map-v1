# iPhone Editing Guide

## Routine editing: change only `projects.csv`

### Small correction in Safari

1. Open the repository.
2. Open `projects.csv`.
3. Tap the pencil icon or **Edit file**.
4. Change the value.
5. Tap **Commit changes**.
6. Use a clear message, such as `Correct P004 coordinates`.
7. For a tiny correction, commit to `main`. For a large update, create a new branch.
8. Wait for GitHub Actions and GitHub Pages to finish.

### Several changes using Numbers or Excel mobile

1. Download `projects.csv`.
2. Open it in Apple Numbers or Microsoft Excel.
3. Edit the rows.
4. Export as CSV.
5. Keep the filename exactly `projects.csv`.
6. Replace the existing file in GitHub.
7. Commit the replacement.

## Add a project

Add a new row without changing the header row.

Important rules:

- `PK_ID` must be unique.
- Latitude must be between -90 and 90.
- Longitude must be between -180 and 180.
- Status must match `map-config.json`.
- Progress fields must be blank or between 0 and 100.
- Use `TRUE` or `FALSE` for `is_public`.
- Put text containing commas inside double quotes.

## Change title, subtitle or colours

Edit `map-config.json`.

## Large interface changes

Replace or edit `index.html`. Do not delete it first. Commit the replacement in one change.

## Check every update

1. Open **Actions**.
2. Confirm **Validate project data** has a green check.
3. Confirm **pages build and deployment** has a green check.
4. Open the live website.
5. Test the edited marker, search and filters.

## Useful mobile tools

- Safari for settings and quick edits
- GitHub mobile app for issues and pull requests
- Apple Numbers or Microsoft Excel for CSV
- `github.dev/FabinGurung/jp-ecosystem-project-map` for a browser-based code editor
