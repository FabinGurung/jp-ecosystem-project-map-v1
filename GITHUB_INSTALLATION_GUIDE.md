# Install This v1.2 Package on the Existing GitHub Repository

Repository:

`https://github.com/FabinGurung/jp-ecosystem-project-map-v1`

Live site:

`https://fabingurung.github.io/jp-ecosystem-project-map-v1/`

This guide does **not** create a new repository and does **not** alter the
existing `v1.1.0` tag.

## Recommended method: Windows + GitHub Desktop

This is safer than uploading dozens of files individually through an iPhone.
It preserves folders such as `.github`, `assets`, `docs`, `scripts`, and
`tests`.

### Part 1 — Download and inspect the ZIP

1. Download the final ZIP from ChatGPT.
2. In Windows File Explorer, right-click the ZIP.
3. Select **Extract All**.
4. Open the extracted folder.
5. Confirm you can see:

   - `index.html`
   - `projects.csv`
   - `map-config.json`
   - `organizations.csv`
   - `assets`
   - `docs`
   - `scripts`
   - `tests`
   - `.github`
   - `.nojekyll`

6. If Windows hides dotfiles, turn on **View → Show → Hidden items**.

The ZIP contains no `.git` folder and no passwords or API keys.

### Part 2 — Install GitHub Desktop

1. Go to `https://desktop.github.com/`.
2. Download GitHub Desktop.
3. Install it.
4. Sign in using the GitHub account that owns or can edit
   `FabinGurung/jp-ecosystem-project-map-v1`.

### Part 3 — Clone the existing repository

1. Open GitHub Desktop.
2. Choose **File → Clone repository**.
3. Open the **URL** tab.
4. Enter:

   `https://github.com/FabinGurung/jp-ecosystem-project-map-v1.git`

5. Choose a local path you can find, for example:

   `Documents\GitHub\jp-ecosystem-project-map-v1`

6. Click **Clone**.
7. Confirm the current branch shown at the top is `main`.

Do not delete or rename `main`.

### Part 4 — Create the v1.2 development branch

1. In GitHub Desktop, click **Current branch**.
2. Click **New branch**.
3. Enter exactly:

   `v1.2-operational-map`

4. Base it on `main`.
5. Click **Create branch**.
6. Confirm GitHub Desktop now shows:

   `Current branch: v1.2-operational-map`

This keeps the live `main` branch unchanged while you review v1.2.

### Part 5 — Copy the package correctly

1. In GitHub Desktop, choose **Repository → Show in Explorer**.
2. Open the extracted ChatGPT package in another File Explorer window.
3. Select the **contents inside** the package folder.
4. Copy those contents into the cloned GitHub repository folder.
5. When Windows asks, choose **Replace the files in the destination**.

Important:

- Copy the package contents, not the outside package folder itself.
- `index.html` must remain at the repository root.
- Do not produce:

  `jp-ecosystem-project-map-v1/jp-ecosystem-project-map-v1/index.html`

- The correct path is:

  `jp-ecosystem-project-map-v1/index.html`

### Part 6 — Confirm the changed files

Return to GitHub Desktop. The left side should show changes including:

- modified `index.html`
- modified `projects.csv`
- modified `map-config.json`
- modified documentation and workflow
- new normalized CSV files
- new `assets`, `docs`, `scripts`, and `tests` folders

Confirm `.nojekyll` still exists.

Do not commit if the file list contains:

- `.env`
- passwords
- API keys
- private client contacts
- confidential BOQ or stock data
- a nested duplicate project folder

### Part 7 — Commit locally

1. In the **Summary** box, enter:

   `Build v1.2 operational project map`

2. Optionally enter:

   `Add normalized IDs, organizations, works/material schemas, validation, and responsive operational project details.`

3. Confirm the button says:

   **Commit to v1.2-operational-map**

4. Click the commit button.

If it says **Commit to main**, stop and switch to the development branch first.

### Part 8 — Publish the branch

1. Click **Publish branch**.
2. Wait for the upload to complete.
3. Open the repository on GitHub.
4. Open the branch selector.
5. Confirm `v1.2-operational-map` exists.
6. Confirm `main` still contains the stable v1.1 application.

### Part 9 — Check GitHub validation

1. Open the repository’s **Actions** tab.
2. Open **Validate operational map data**.
3. Confirm all steps have green checks:

   - normalized CSV and configuration validation
   - Python regression tests
   - JavaScript syntax
   - JavaScript CSV tests

The validator may print warnings that project sector and implementation
mechanism are not entered. Those warnings are intentional and do not fail the
Action.

### Part 10 — Preview before merging

GitHub Pages currently publishes `main`, so the development branch should not
replace the live site yet.

To preview locally:

1. Open the cloned repository folder.
2. Double-click `START_LOCAL_SERVER_WINDOWS.bat`.
3. If Windows asks, allow Python on the private network only.
4. Your browser should open:

   `http://127.0.0.1:8000/`

5. Keep the command window open while testing.
6. Press `Ctrl+C` in that window to stop the server.

Do not preview by double-clicking `index.html`; browsers normally block its CSV
loading.

### Part 11 — Test the package

Use `docs/TESTING_CHECKLIST.md`.

At minimum confirm:

- all seven markers appear
- labels are `REB-001` and `FBL-001`–`FBL-006`
- clicking a marker and clicking the list select the same project
- Overview opens
- Works explains that no verified project BOQ is assigned
- Materials explains that public stock quantities are disabled
- search finds global, company, and legacy codes
- status and company filters work
- directions work
- GeoJSON downloads
- mobile bottom sheet is usable
- map tiles remain joined after screen rotation/resize

### Part 12 — Open a pull request

1. On GitHub, switch to `v1.2-operational-map`.
2. Click **Compare & pull request**.
3. Base branch: `main`.
4. Compare branch: `v1.2-operational-map`.
5. Suggested title:

   `v1.2.0 — Operational Project Map`

6. Describe:

   - new global and company-facing project IDs
   - legacy-code preservation
   - normalized public CSV foundation
   - operational project panel
   - expanded validation
   - no invented project work or inventory
   - no change to the v1.1.0 tag or Pages deployment method

7. Create the pull request.
8. Wait for the validation check to become green.

### Part 13 — Promote the reviewed build to v1.2.0

Only after the checklist passes:

1. On the development branch, edit `map-config.json`.
2. Change:

   `"app_version": "1.2.0-dev"`

   to:

   `"app_version": "1.2.0"`

3. Update the changelog’s v1.2 status from development candidate to released.
4. Commit:

   `Prepare v1.2.0 release`

5. Confirm validation is green again.
6. Merge the pull request into `main`.

### Part 14 — Confirm GitHub Pages

1. Open **Actions**.
2. Confirm **pages build and deployment** succeeds.
3. Open:

   `https://fabingurung.github.io/jp-ecosystem-project-map-v1/`

4. Hard-refresh:

   - Windows: `Ctrl+F5`
   - iPhone Safari: close the tab and reopen it, or clear website data if an
     old cached version persists

5. Repeat the critical live-site checks.

Keep Pages set to:

- Source: **Deploy from a branch**
- Branch: **main**
- Folder: **/ (root)**

Do not convert `validate-projects.yml` into a deployment workflow.

### Part 15 — Create the v1.2.0 release and tag

1. Open the repository’s **Releases** page.
2. Click **Draft a new release**.
3. Click **Choose a tag**.
4. Create:

   `v1.2.0`

5. Target: `main`.
6. Title:

   `v1.2.0 — Operational Project Map`

7. Use the v1.2 changelog as the release notes.
8. Publish the release.

Never move or recreate `v1.1.0`.

## Browser-only upload alternative

Use this only if GitHub Desktop is unavailable.

1. On GitHub, create `v1.2-operational-map` from `main`.
2. Switch to that branch.
3. Choose **Add file → Upload files**.
4. On a desktop browser, drag the package’s root files and folders into the
   upload area.
5. Confirm the upload preserves `assets/...`, `docs/...`, `scripts/...`,
   `tests/...`, and `.github/workflows/...`.
6. Commit directly to `v1.2-operational-map`.

The GitHub web file picker is awkward for hidden folders and large folder
trees. GitHub Desktop is strongly preferred for this migration.

## iPhone recommendation

Use iPhone GitHub/Safari later for small edits to one CSV row. Do the one-time
v1.2 package installation from Windows so folder structure, hidden files, and
validation scripts are not missed.

## Recovery

If v1.2 does not work:

1. Do not delete `v1.1.0`.
2. Do not move the `v1.1.0` tag.
3. If the pull request is not merged, close it or continue fixing the branch.
4. If already merged, use a normal revert commit on `main`.
5. The stable v1.1 source remains available at tag `v1.1.0`.
