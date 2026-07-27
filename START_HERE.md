# Start Here

This is the complete upload-ready development package for the existing
repository:

`FabinGurung/jp-ecosystem-project-map-v1`

Do not create a new repository.

## Fastest safe path

1. Read `GITHUB_INSTALLATION_GUIDE.md`.
2. Use a Windows computer and GitHub Desktop for the one-time full package
   upload.
3. Clone the existing repository.
4. Create the branch `v1.2-operational-map`.
5. Copy the **contents** of this package into the cloned repository folder.
6. Commit and publish the branch.
7. Confirm the validation Action is green.
8. Preview locally with `START_LOCAL_SERVER_WINDOWS.bat`.
9. Open a pull request into `main`.
10. Merge only after the checklist passes.

## What is intentionally blank

- `people.csv`
- `project_funding.csv`
- `project_work_items.csv`
- `project_material_inventory.csv`
- Project sector and implementation mechanism for all seven current projects

These are not mistakes. The source did not establish those facts, so they were
not invented.

## What is already populated

- Seven migrated projects
- Two stable company organizations
- Seven verified project-contractor relationships
- Twenty-nine reusable work-catalog descriptions
- Eleven reusable material-master records

## Before putting v1.2 on `main`

Keep `map-config.json` at `app_version: 1.2.0-dev` during review. After all
checks pass, change it to `1.2.0`, update the changelog date if necessary, merge
the pull request, and create the `v1.2.0` release/tag.
