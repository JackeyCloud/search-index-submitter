from __future__ import annotations

import re
from urllib.parse import urljoin

from .http import HttpClient
from .models import SiteTarget


SITEMAP_RE = re.compile(r"^\s*Sitemap:\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE)


def discover_sitemap(target: SiteTarget, client: HttpClient) -> tuple[str, str]:
    if target.sitemap_url:
        return target.sitemap_url, "指定"

    robots_url = urljoin(target.site_url, "/robots.txt")
    response = client.get(robots_url)
    if response.status == 200:
        matches = SITEMAP_RE.findall(response.body)
        if matches:
            return urljoin(target.site_url, matches[0]), "robots.txt"

    for path in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
        candidate = urljoin(target.site_url, path)
        response = client.get(candidate)
        content_type = response.headers.get("Content-Type", "").lower()
        if response.status == 200 and ("xml" in content_type or "<urlset" in response.body[:500] or "<sitemapindex" in response.body[:500]):
            return candidate, "常见路径"
    return urljoin(target.site_url, "/sitemap.xml"), "默认路径（未验证存在）"
