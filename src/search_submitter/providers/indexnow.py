from __future__ import annotations

from urllib.parse import urlsplit

from ..models import SiteTarget, Status, SubmissionResult
from .base import Provider


class IndexNowProvider(Provider):
    id = "indexnow"
    display_name = "IndexNow（Bing / Yandex 等）"
    endpoint = "https://api.indexnow.org/indexnow"

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        key = self.config.indexnow_key.strip()
        if not key:
            return SubmissionResult(self.display_name, target.site_url, Status.SKIPPED, "未配置 IndexNow Key")
        urls = list(target.urls)
        payload = {"host": target.host, "key": key, "urlList": urls[:10000]}
        if self.config.indexnow_key_location.strip():
            payload["keyLocation"] = self.config.indexnow_key_location.strip()
        if dry_run:
            return SubmissionResult(self.display_name, target.site_url, Status.DRY_RUN, f"将提交 {len(urls)} 个 URL")
        response = self.client.post(self.endpoint, json_body=payload)
        if response.status in {200, 202}:
            return SubmissionResult(self.display_name, target.site_url, Status.SUCCESS, f"已接收 {len(urls)} 个 URL（HTTP {response.status}）")
        messages = {400: "请求格式无效", 403: "Key 与主机不匹配", 422: "URL 不属于该主机", 429: "请求过于频繁"}
        return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"{messages.get(response.status, '提交失败')}（HTTP {response.status}）", {"body": response.body[:500]})
