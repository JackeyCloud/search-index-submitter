---
name: submit-new-site-indexing
description: Batch-submit newly launched websites, page URLs, and sitemaps to supported search engines using the local Python search-index-submitter. Use when Codex needs to check indexing and notify Baidu, Google Search Console, Bing, Yandex, IndexNow participants, 360 Search, or Shenma after a site or page launches.
---

# Submit New Site Indexing

Use `scripts/submit_sites.py`. Preflight first; live submission requires an explicit user request.

```bash
python scripts/submit_sites.py example.com
python scripts/submit_sites.py example.com --execute
```

Keep duplicate checking enabled. Skip only URLs conclusively reported as indexed; submit unknown URLs to prevent false negatives. Use `--providers`, `--sitemap`, or `--file` for batch control. Use `--no-deduplicate` only when the user requests forced resubmission.

Read `references/platforms.md` before explaining coverage. Never print credential values, and never claim submission guarantees indexing or ranking.
