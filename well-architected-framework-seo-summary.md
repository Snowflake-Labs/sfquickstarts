# Well Architected Framework: SEO Review Request

**Date:** January 23, 2026  
**For:** SEO Team  
**Full requirements:** `well-architected-framework-url-recommendations.md`

---

## Overview

We're planning to restructure the Well Architected Framework content from 5 flat URLs to a hierarchical structure with 33 standalone pages. Before we proceed, we'd like your input on two key structural decisions.

### Current State (Flat)
```
/developers/guides/well-architected-framework-cost-optimization-and-finops/
/developers/guides/well-architected-framework-reliability/
...
```

### Proposed State (Hierarchical)
```
/developers/guides/well-architected-framework/
├── cost-optimization/
│   ├── business-impact/
│   ├── visibility/
│   └── ...
├── reliability/
│   ├── strategy-governance/
│   ├── disaster-recovery/
│   └── ...
└── ...
```

---

## Input Requested: Hub Pages vs. Redirects

We're leaning toward making pillar URLs (e.g., `/reliability/`) serve as **hub pages** rather than 301 redirects to the first guide. We'd appreciate your perspective on whether this is the right approach.

### Our Thinking

| Factor | Hub Page | Redirect to First Guide |
|--------|----------|------------------------|
| **SEO** | Pillar URL can rank for "Snowflake reliability" | Cannot rank — passes through to child page |
| **Link Equity** | External links build authority on pillar URL | Diluted through redirect chain |
| **User Intent** | User gets orientation before diving in | Lands on unexpected sub-page |
| **Analytics** | Can track pillar engagement separately | Conflated with first guide metrics |

### Cases Where Redirect Might Be Better
- Parent is purely organizational (e.g., `/docs/` → `/docs/getting-started/`)
- No meaningful content at parent level
- Users always want the first item (sequential tutorial)

We don't think these apply here since each pillar has meaningful intro content (Overview + Principles, 500-700 words) and users may enter at any guide. But we'd welcome your take.

### Proposed Hub Page Content
- Hero (title + description)
- Overview (~100 words)
- Principles (~300 words)
- Guide cards linking to standalone pages

**Question for SEO team:** Does this hub page approach make sense from an SEO standpoint, or would you recommend a different pattern?

---

## Input Requested: URL Depth

The proposed structure results in URLs up to 6 levels deep. We wanted to flag this for your review.

### Proposed Depth Breakdown

| Level | Example | Depth |
|-------|---------|-------|
| Domain | `snowflake.com` | 0 |
| Locale | `/en/` | 1 |
| Section | `/developers/` | 2 |
| Area | `/guides/` | 3 |
| Journey | `/well-architected-framework/` | 4 |
| Pillar | `/reliability/` | 5 |
| Guide | `/disaster-recovery/` | **6** |

**Deepest URL:** `snowflake.com/en/developers/guides/well-architected-framework/reliability/disaster-recovery/` (~95 characters)

### What We Found (Industry Comparison)

| Site | Example URL | Depth |
|------|-------------|-------|
| AWS Well-Architected | `/wellarchitected/latest/reliability-pillar/design-principles/` | 5 |
| Azure Well-Architected | `/en-us/azure/well-architected/reliability/principles/` | 6 |
| Google Cloud Architecture | `/architecture/framework/reliability/design-scale/` | 5 |
| **Snowflake (proposed)** | `/en/developers/guides/well-architected-framework/reliability/disaster-recovery/` | 6 |

### Our Understanding

| Concern | What we've read |
|---------|-----------------|
| URL depth as ranking factor | Google has stated depth alone isn't a ranking factor |
| Crawl priority | Could be minor concern, but strong internal linking should help |
| URL length | ~95 chars is well under practical limits |

**Question for SEO team:** Are there concerns with 6-level depth we should be aware of? Would you recommend a flatter structure?

---

## Additional Decisions (For Your Awareness)

| Decision | Our Rationale |
|----------|---------------|
| **"Secure the Perimeter" as standalone page** | High-value keywords ("network security," "MFA," "authentication") — seemed worth a standalone URL even at ~450 words. Does this align with your thinking? |
| **500+ word threshold for standalone pages** | Sections under 500 words would stay as anchors on hub pages. Is this a reasonable threshold? |

---

## Planned 301 Redirects

| Old URL | New URL |
|---------|---------|
| `/developers/guides/well-architected-framework-cost-optimization-and-finops/` | `/developers/guides/well-architected-framework/cost-optimization/` |
| `/developers/guides/well-architected-framework-security-and-governance/` | `/developers/guides/well-architected-framework/security-governance/` |
| `/developers/guides/well-architected-framework-reliability/` | `/developers/guides/well-architected-framework/reliability/` |
| `/developers/guides/well-architected-framework-performance/` | `/developers/guides/well-architected-framework/performance/` |
| `/developers/guides/well-architected-framework-operational-excellence/` | `/developers/guides/well-architected-framework/operational-excellence/` |

---

## Page Count by Pillar

| Pillar | Standalone Pages | Hub Page Words |
|--------|------------------|----------------|
| Cost Optimization | 4 | 717 |
| Security & Governance | 4 | 720 |
| Reliability | 6 | 522 |
| Performance | 12 | 483 |
| Operational Excellence | 7 | 305 |
| **Total** | **33** | — |

---

## Post-Launch SEO Checklist

Once we have alignment on structure, we'll need to:

- [ ] Configure and test 301 redirects
- [ ] Add new URLs to sitemap.xml
- [ ] Submit sitemap to Google Search Console
- [ ] Monitor crawl errors for 2 weeks post-launch
- [ ] Track rankings for target keywords

---

## Summary: What We Need From You

1. **Hub pages vs. redirects** — Does the hub page approach work, or should we redirect pillar URLs?

2. **URL depth** — Any concerns with 6 levels? Recommendations for flattening?

3. **Anything else** — Are there SEO considerations we're missing?

We're happy to adjust the plan based on your guidance. Full details are in `well-architected-framework-url-recommendations.md` if you'd like to dig deeper.

Thanks!
