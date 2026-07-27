# iPhone Editing Guide

Use iPhone for small, careful updates after the full v1.2 package has already
been installed from a computer.

Do not try to upload the entire v1.2 folder structure from iPhone. Hidden files
and nested folders are easy to miss.

## Simple project correction

1. Open the repository in Safari or the GitHub app.
2. Confirm the branch:

   - use `main` only for a tiny approved production correction
   - use a new branch for multiple or structural changes

3. Open `projects.csv`.
4. Tap the pencil/Edit button.
5. Change only the intended field.
6. Do not change the three IDs of an existing project:

   - `project_id`
   - `company_project_code`
   - `legacy_project_code`

7. Commit with a clear message such as:

   `Update PRJ-000004 public progress`

8. Open **Actions**.
9. Confirm **Validate operational map data** is green.
10. If committed to `main`, wait for Pages deployment and check the live map.

## Add a project from iPhone

Adding a row is possible but easier in Numbers/Excel on a computer.

Required concepts:

- new immutable `project_id`
- new company-specific `company_project_code`
- legacy code only when one already exists
- valid executing organization ID
- project/source names
- latitude and longitude
- status
- last updated
- public flag
- data quality and verification status

Do not copy the last row and forget to change its IDs.

## Add an organization

1. Add it to `organizations.csv`.
2. Give it the next unused `ORG-000000` ID.
3. Use the real verified name.
4. Choose a controlled organization type.
5. Do not enter private contact information or registration numbers publicly.
6. Add a separate row to `project_parties.csv` if it has a project role.

## User Committee / Samiti

Use:

```text
organization_type = USER_COMMITTEE
implementation_mechanism = GOVERNMENT_USER_COMMITTEE
```

Do not create separate Samiti or Community Implementation mechanism values.

## Work and materials

Avoid entering detailed BOQ and inventory data from iPhone until the source and
public-visibility decision are verified.

Remember:

- rate and amount are internal by default
- exact stock is internal by default
- `is_public=FALSE` does not secure a committed row
- never paste `#REF!` into a numeric field

## CSV safety

- Keep the header row unchanged.
- Use `YYYY-MM-DD`.
- Use a dot for decimals.
- Store money as `526262.43`, not `5,26,262.43`.
- Put text containing a comma inside double quotes.
- Preserve latitude/longitude order in CSV.
- GeoJSON automatically exports longitude/latitude order.

## If the Action turns red

1. Open the failed Action.
2. Read the first `ERROR:` line.
3. Return to the CSV.
4. Correct the exact row/field.
5. Commit the correction.
6. Confirm the next Action is green.

Warnings about an unknown sector or implementation mechanism are allowed when
the real source has not yet been verified.

## Useful mobile tools

- Safari for a one-cell correction
- GitHub mobile app for pull requests and Action status
- Apple Numbers or Microsoft Excel for reviewing a CSV

Use Windows + GitHub Desktop for full package migrations and folder changes.
