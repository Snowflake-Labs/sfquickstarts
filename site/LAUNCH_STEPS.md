## Quickstarts → AEM soft launch: Step-by-step guide

### Purpose

Runbook for deploying Firebase Hosting redirects that move Quickstarts traffic to AEM, with validation and rollback.

### Prerequisites

- Access to the Firebase project used by `quickstarts.snowflake.com` (Hosting deploy permission).
- Firebase CLI installed and authenticated (`firebase login`).
- Repo up to date on `master` (or the target branch for deployment).

### References in repo

- Plan: `site/REDIRECTS_AEM_MIGRATION.md`
- Redirects JSON (generated): `site/firebase.redirects.generated.json`
- Firebase config (live): `site/firebase.json`
- Overrides used for Well Architected pages: `site/manual_redirect_overrides.json`

### T-1: Pre-flight checks (10–15 minutes)

1) Verify generated redirects file exists and looks sane
   - Open `site/firebase.redirects.generated.json` and spot-check a few entries for https and trailing slash.
2) Verify overrides are present at top of Hosting redirects
   - Open `site/firebase.json` and confirm the first entries cover the five Well Architected pages.
3) Confirm no chains
   - Ensure destinations in `site/firebase.json` point directly to `https://www.snowflake.com/.../` (no intermediate Quickstarts URLs).
4) Commit status
   - Ensure all changes are committed and reviewed in a PR; merge to the deploy branch.

### Deploy

From the repo’s `site/` directory (use one of the following):

```bash
cd site
# Fastest for redirect-only updates:
firebase deploy --only hosting

# Or use the repo script (build + deploy):
npm install
npm run deploy
```

Notes:
- If CI/CD deploys on merge to `master`, you may skip the manual deploy and monitor the pipeline.

### Validate (spot checks)

Run these with curl; expect a single 301 to the AEM URL, followed by 200 on the final page.

```bash
# Example variant checks
curl -I https://quickstarts.snowflake.com/guide/zero_to_snowflake
curl -I https://quickstarts.snowflake.com/guide/zero_to_snowflake/
curl -I "https://quickstarts.snowflake.com/guide/zero_to_snowflake/index.html?index=..%2F..index"

# Well Architected (sample)
curl -I https://quickstarts.snowflake.com/guide/cost_optimization
curl -I https://quickstarts.snowflake.com/guide/security_and_governance/
curl -I https://quickstarts.snowflake.com/guide/performance/index.html
curl -I https://quickstarts.snowflake.com/guide/reliability
curl -I https://quickstarts.snowflake.com/guide/operational_excellence/

# International landing examples
curl -I https://quickstarts.snowflake.com/ja/
curl -I https://quickstarts.snowflake.com/ptbr/
```

Checklist:
- Destination Location header is `https://www.snowflake.com/.../` (https + trailing slash).
- Exactly one hop (301) to AEM; no further 3xx.
- Known unmapped URLs return 404 or 410 per policy.

### SEO final validation

Share with SEO:
- We used their mapping to generate redirects and added manual overrides for Well Architected pages.
- Ask them to spot-check: a handful of top URLs, parameterized `index.html` variants, and international pages.

### Rollback

- If needed, revert the redirect changes commit in Git (revert the PR) and redeploy Hosting:

```bash
cd site
firebase deploy --only hosting
```

- Alternatively, redeploy a prior Hosting version from the Firebase Console (Hosting versions) if available.

### Post-launch monitoring (24–72 hours)

- Watch Search Console for crawl and index signals; look for spikes in 404s.
- Review analytics for top legacy URLs to confirm they resolve as expected.
- Add/update redirects for any newly reported parameters or assets with backlinks.


