# AEM Staging GitHub Actions Migration

This document describes the GitHub Actions workflow that replaces the Workato automation for staging quickstart tutorials to Adobe Experience Manager (AEM).

## Required GitHub Secrets

Configure these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AEM_USERNAME` | AEM username for basic authentication | `aem-user@company.com` |
| `AEM_PASSWORD` | AEM password for basic authentication | `********` |
| `AEM_AUTHOR_URL` | AEM author instance base URL (no trailing slash) | `https://author-p57963-e462109.adobeaemcloud.com` |
| `AEM_PUBLISH_URL` | AEM publish instance base URL (no trailing slash) | `https://publish-p57963-e462098.adobeaemcloud.com` |

### AEM User Requirements

The AEM user account must have permissions for:
- DAM asset upload/modification
- Content fragment CRUD operations
- Page creation/modification
- Replication (publish)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    validate-and-stage.yml                        │
│  ┌─────────────────────┐    ┌────────────────────────────────┐  │
│  │ validate_and_stage  │───▶│      stage_to_aem (matrix)     │  │
│  │   - validations     │    │  uses: stage-to-aem.yml        │  │
│  │   - detect files    │    │                                │  │
│  └─────────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      stage-to-aem.yml                            │
│  Reusable workflow that:                                         │
│  1. Checkouts the PR commit                                      │
│  2. Parses markdown frontmatter (parse_markdown.py)              │
│  3. Copies base content fragment to staging                      │
│  4. Updates CF with parsed content                               │
│  5. Uploads images to AEM DAM                                    │
│  6. Creates staging page from base template                      │
│  7. Publishes and comments PR with preview URL                   │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created

| File | Purpose |
|------|---------|
| `.github/workflows/stage-to-aem.yml` | Reusable workflow with all AEM staging logic |
| `scripts/aem-staging/parse_markdown.py` | Python script to parse frontmatter and transform image URLs |

## Workflow Inputs

The `stage-to-aem.yml` reusable workflow accepts:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `quickstart_name` | string | Yes | Name of the quickstart folder |
| `language` | string | Yes | Language code (en, es, it, fr, de, ja, ko, pt_br) |
| `commit_sha` | string | Yes | Commit SHA for unique staging URL |
| `pr_number` | number | Yes | PR number for commenting |

## AEM API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `{path}` + `:operation=copy` | POST | Copy content fragment from base template |
| `{cf_path}/jcr:content` | POST | Update content fragment properties |
| `{dam_path}.createasset.html` | POST | Upload image to DAM |
| `/bin/asynccommand` | POST | Trigger image reprocessing |
| `/bin/replicate.json` | POST | Publish content (activate) |

## Differences from Workato

| Aspect | Workato | GitHub Actions |
|--------|---------|----------------|
| Trigger | Webhook from GitHub | Native workflow_call |
| Auth | Connection configuration | GitHub secrets |
| Rate limiting | 2-min sleep between calls | Matrix with max-parallel: 1 |
| Image upload | Async callable recipe | Sequential in same job |
| Error handling | Try/catch blocks | Step-level failure handling |
| PR comment | GitHub API via connection | Native github-script action |

## Staging URL Format

Preview URLs follow this pattern:
```
https://{AEM_PUBLISH_URL}/{language}/developers/guides/{quickstart_name}-{commit_sha}
```

Example:
```
https://publish-p57963-e462098.adobeaemcloud.com/en/developers/guides/getting-started-with-snowflake-abc1234
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check `AEM_USERNAME` and `AEM_PASSWORD` are correct
2. **403 Forbidden**: Verify the AEM user has required permissions
3. **404 Not Found**: Base content fragment or page template may be missing
4. **Images not appearing**: Wait a few minutes for async processing

### Debug Steps

1. Check workflow logs in GitHub Actions
2. Verify secrets are properly configured
3. Test AEM API manually with curl: `curl -u "user:pass" {AEM_AUTHOR_URL}/content/dam.json`
4. Check AEM author instance for created assets/fragments
