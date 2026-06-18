from __future__ import annotations

import re
from collections import OrderedDict
from urllib.parse import urlsplit, urlunsplit

from .models import SiteTarget


SPLIT_RE = re.compile(r"[\s,，;；]+")


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("地址不能为空")
    if "://" not in value:
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"无效网址: {value}")
    netloc = parsed.hostname.encode("idna").decode("ascii")
    if parsed.port:
        netloc += f":{parsed.port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc.lower(), path, parsed.query, ""))


def parse_targets(text: str, sitemap_template: str = "") -> list[SiteTarget]:
    grouped: OrderedDict[str, dict[str, object]] = OrderedDict()
    for raw in SPLIT_RE.split(text.strip()):
        if not raw:
            continue
        url = normalize_url(raw)
        parsed = urlsplit(url)
        site_url = urlunsplit((parsed.scheme, parsed.netloc, "/", "", ""))
        entry = grouped.setdefault(site_url, {"original": raw, "urls": []})
        entry["urls"].append(url)

    targets: list[SiteTarget] = []
    for site_url, entry in grouped.items():
        sitemap_url = None
        if sitemap_template:
            sitemap_url = normalize_url(
                sitemap_template.format(site=site_url.rstrip("/"), host=urlsplit(site_url).hostname)
            )
        targets.append(
            SiteTarget(
                original=str(entry["original"]),
                site_url=site_url,
                urls=tuple(dict.fromkeys(entry["urls"])),
                sitemap_url=sitemap_url,
            )
        )
    return targets
