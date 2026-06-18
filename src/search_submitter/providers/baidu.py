from __future__ import annotations

import re
from urllib.parse import urlencode

from ..models import SiteTarget, Status, SubmissionResult
from .base import Provider


class BaiduProvider(Provider):
    id = "baidu"
    display_name = "百度普通收录 API"

    def _token_for(self, target: SiteTarget) -> str:
        mapping = {}
        for line in re.split(r"[\n,，;；]+", self.config.baidu_token_map):
            if "=" in line:
                host, token = line.split("=", 1)
                mapping[host.strip().lower()] = token.strip()
        return mapping.get(target.host.lower(), self.config.baidu_token.strip())

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        token = self._token_for(target)
        if not token:
            return SubmissionResult(self.display_name, target.site_url, Status.SKIPPED, "未配置百度准入密钥 token")
        urls = list(target.urls)
        endpoint = "https://data.zz.baidu.com/urls?" + urlencode({"site": target.site_url.rstrip("/"), "token": token})
        if dry_run:
            return SubmissionResult(self.display_name, target.site_url, Status.DRY_RUN, f"将推送 {len(urls)} 个 URL")
        response = self.client.post(endpoint, data="\n".join(urls).encode("utf-8"), headers={"Content-Type": "text/plain"})
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.body[:500]}
        if response.status == 200 and isinstance(body, dict) and "error" not in body:
            success = body.get("success", len(urls))
            remain = body.get("remain", "未知")
            return SubmissionResult(self.display_name, target.site_url, Status.SUCCESS, f"成功推送 {success} 条，今日剩余 {remain}", body)
        message = body.get("message") if isinstance(body, dict) else None
        return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"{message or '百度 API 拒绝请求'}（HTTP {response.status}）", body if isinstance(body, dict) else {})
