from __future__ import annotations

from urllib.parse import urlencode

from ..models import IndexCheck, IndexState, SiteTarget, Status, SubmissionResult
from .base import Provider


class BingProvider(Provider):
    id = "bing"
    display_name = "Bing Webmaster URL API"
    endpoint = "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch"

    def check_indexed(self, target: SiteTarget, url: str) -> IndexCheck:
        key = self.config.bing_api_key.strip()
        if not key:
            return IndexCheck(IndexState.UNKNOWN, "未配置 Bing Webmaster API Key")
        endpoint = "https://ssl.bing.com/webmaster/api.svc/json/GetUrlInfo?" + urlencode(
            {"siteUrl": target.site_url, "url": url, "apikey": key}
        )
        response = self.client.get(endpoint)
        if response.status != 200:
            return IndexCheck(IndexState.UNKNOWN, f"Bing 查询返回 HTTP {response.status}")
        try:
            data = response.json()
        except ValueError:
            return IndexCheck(IndexState.UNKNOWN, "Bing 查询响应不是有效 JSON")
        record = data.get("d") if isinstance(data, dict) else None
        if isinstance(record, dict) and record:
            return IndexCheck(IndexState.INDEXED, "Bing Webmaster 已有该 URL 记录")
        return IndexCheck(IndexState.NOT_INDEXED, "Bing Webmaster 暂无该 URL 记录")

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        key = self.config.bing_api_key.strip()
        if not key:
            return SubmissionResult(self.display_name, target.site_url, Status.SKIPPED, "未配置 Bing Webmaster API Key；仍可使用 IndexNow")
        urls = list(target.urls)
        if dry_run:
            return SubmissionResult(self.display_name, target.site_url, Status.DRY_RUN, f"将提交 {len(urls)} 个 URL")
        response = self.client.post(self.endpoint + "?" + urlencode({"apikey": key}), json_body={"siteUrl": target.site_url, "urlList": urls})
        if response.status == 200:
            return SubmissionResult(self.display_name, target.site_url, Status.SUCCESS, f"已提交 {len(urls)} 个 URL")
        return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"Bing API 返回 HTTP {response.status}", {"body": response.body[:500]})
