## Quickstarts → AEM migration: Redirect implementation plan (Firebase + Codelabs)

### Context and goals

- **Goal**: Deprecate the current Quickstarts site on `quickstarts.snowflake.com` while keeping it online in a minimal form to serve clean, direct 301 redirects to new AEM URLs on `www.snowflake.com` without redirect chains.
- **Constraints**:
  - Multiple legacy URL variants exist per page (clean, trailing slash, `index.html`, with query parameters, etc.). All must 301 directly to the new canonical AEM URL.
  - Some legacy URLs already 301 or 404. Decide per-URL whether to 301 (to AEM), 410 (gone), or 404 (not found).
  - Image assets sometimes receive backlinks; where appropriate, redirect these to the new AEM page rather than serving old assets.

### What “Firebase” vs “Codelabs” means in this repo

- **Firebase Hosting**: Controlled by `site/firebase.json`. This is where server-side 301 redirects are configured and deployed to `quickstarts.snowflake.com`.
- **Codelabs UI/build**: The static site and build system under `site/app` (and the generator tooling). For deprecation, we’ll keep a minimal page only; the redirect logic lives in Firebase Hosting.

### Redirect design (SEO-safe; no chains)

For each legacy Quickstart page that maps to a new AEM URL, create explicit 301 redirects for all server-addressable variants, each pointing directly to the new AEM URL:

- Variant set per legacy path `O` (e.g., `/guide/getting_started_datameer`):
  - `O`
  - `O/`
  - `O/index.html`
  - `O/index.html/` (defensive)
  - Note: Query parameters (e.g., `?index=..%2F..index`) are ignored by Firebase matchers and will be captured by the same rule. URL fragments (e.g., `#3`) never reach the server and require no special handling.

Additional recommendations:

- For pages with notable image backlinks under the legacy path (e.g., `O/img-1.png`), add redirects from those asset URLs to the new AEM page `N` to consolidate link equity.
- For legacy URLs determined to be permanently removed: return **410** (Gone) rather than 404, if we want to explicitly signal deprecation to crawlers.
- Avoid broad catch-alls that could accidentally redirect unrelated resources; prefer explicit per-URL entries generated from the audit mapping.

### Source of truth for mappings

- **Authoritative mapping**: `quickstarts-redirects.csv` (from SEO audit) at the repo root.
  - Columns: `Old URL, Existing page status Code, New URL`.
  - The “Existing page status Code” is informational only and is NOT used as the final redirect status.
  - Destinations are normalized by the generator to include `https://` and a trailing slash.

### Implementation status and steps

Completed:
- CSV present: `quickstarts-redirects.csv` (root).
- Generator added: `site/tasks/helpers/generate_firebase_redirects.js`.
  - Ensures destinations use `https://` and end with `/`.
  - Generates variant rules for clean, trailing slash, `index.html`, and `index.html/`.
- Generated file: `site/firebase.redirects.generated.json`.
- Merged 2,959 entries into `site/firebase.json` under `hosting.redirects`, preserving existing rules and avoiding redirect chains.

Optional/remaining:
- Minimal deprecation page: `site/app/deprecated.html` (if keeping a human-readable root).
- Optional root redirect to AEM Quickstarts landing page if desired.

Deployment and verification:
- After merge, deploy Firebase Hosting so `firebase.json` changes take effect.
- Verify sample URLs (including variants) return a single 301 directly to the AEM destination and that unmapped URLs behave per policy.

Recommended commands (from the `site/` directory, with Firebase CLI access):

```bash
cd site
npm install
# Option A: deploy hosting only (fastest for redirect changes)
firebase deploy --only hosting
# Option B: use repo script (per package.json), which rebuilds and deploys
npm run deploy
```

If CI/CD is configured to deploy on merge to `master`, a manual deploy may not be necessary; otherwise run one of the commands above using an account authorized for the Firebase project.

### Firebase Hosting redirect examples

For a mapping from `/guide/getting_started_datameer` to `https://www.snowflake.com/en/quickstarts/getting-started-datameer/`:

```json
{
  "source": "/guide/getting_started_datameer",
  "destination": "https://www.snowflake.com/en/quickstarts/getting-started-datameer/",
  "type": 301
},
{
  "source": "/guide/getting_started_datameer/",
  "destination": "https://www.snowflake.com/en/quickstarts/getting-started-datameer/",
  "type": 301
},
{
  "source": "/guide/getting_started_datameer/index.html",
  "destination": "https://www.snowflake.com/en/quickstarts/getting-started-datameer/",
  "type": 301
}
```

If the legacy page is being removed with no replacement:

```json
{
  "source": "/guide/old_unmaintained_guide",
  "type": 410
}
```

### Handling parameterized URLs and anchors

- Firebase Hosting redirect matching does not include the query string. A rule on `/guide/foo/index.html` will match requests like `/guide/foo/index.html?index=..%2F..index` and redirect them to the specified destination.
- URL fragments (e.g., `#3`) are client-side only and never reach the server; no rules are needed.

### Policy for legacy 404s and existing 301s

- Where a legacy URL already 301s, replace it with a single direct 301 to the final AEM URL to avoid chains.
- Where a legacy URL 404s today, decide per-URL:
  - If there is a meaningful replacement: 301 to that AEM page.
  - If not: 410 (Gone) is preferred for permanently removed content.

### Changes introduced by this work

- Added generator: `site/tasks/helpers/generate_firebase_redirects.js`.
- Produced: `site/firebase.redirects.generated.json` from `quickstarts-redirects.csv`.
- Updated `site/firebase.json` with 2,959 redirect entries (direct 301s to AEM, normalized to https and trailing slash).
- Plan for optional deprecation UI at root.

### Appendix A: Current Firebase Hosting config location

- Redirects live in: `site/firebase.json` under `hosting.redirects`.

### Appendix B: Notes on images/assets

- If specific asset URLs under a legacy path receive backlinks, add explicit 301 rules to the new AEM page rather than serving legacy assets. Consider keeping a very small allowlist of truly canonical assets (e.g., brand logos) if needed, but default to redirecting to the page.

### Appendix C: QA checklist

- Sample 50–100 URLs (including known variants) from the CSV and verify with `curl -I`:
  - Exactly one hop (301) to AEM; status 200 on final page.
  - No 302/temporary redirects.
  - Correct handling for `index.html` + query params.
  - Correct handling for internationalized paths.
  - Asset backlinks consolidate to page URLs as intended.


