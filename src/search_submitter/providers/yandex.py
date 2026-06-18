from __future__ import annotations

from urllib.parse import quote

from ..models import SiteTarget, Status, SubmissionResult
from .base import Provider


class YandexProvider(Provider):
    id = "yandex"
    display_name = "Yandex Webmaster Sitemap"
    api = "https://api.webmaster.yandex.net/v4"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"OAuth {self.config.yandex_oauth_token.strip()}"}

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        if not self.config.yandex_oauth_token.strip():
            return SubmissionResult(self.display_name, target.site_url, Status.SKIPPED, "未配置 Yandex OAuth Token；URL 仍可通过 IndexNow 通知")
        if dry_run:
            return SubmissionResult(self.display_name, target.site_url, Status.DRY_RUN, f"将提交 Sitemap: {sitemap_url}")
        try:
            user_response = self.client.get(f"{self.api}/user", headers=self._headers())
            if user_response.status != 200:
                return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"无法读取 Yandex 用户（HTTP {user_response.status}）")
            user_id = user_response.json()["user_id"]
            hosts_response = self.client.get(f"{self.api}/user/{user_id}/hosts", headers=self._headers())
            hosts = hosts_response.json().get("hosts", []) if hosts_response.status == 200 else []
            host = next((item for item in hosts if item.get("ascii_host_url", "").rstrip("/") == target.site_url.rstrip("/")), None)
            if not host:
                return SubmissionResult(self.display_name, target.site_url, Status.FAILED, "站点尚未添加到 Yandex Webmaster 或协议不匹配")
            host_id = quote(str(host["host_id"]), safe="")
            endpoint = f"{self.api}/user/{user_id}/hosts/{host_id}/sitemaps"
            response = self.client.post(endpoint, headers=self._headers(), json_body={"url": sitemap_url})
            if response.status in {200, 201, 202}:
                return SubmissionResult(self.display_name, target.site_url, Status.SUCCESS, f"Sitemap 已提交: {sitemap_url}")
            return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"Yandex API 返回 HTTP {response.status}", {"body": response.body[:500]})
        except (KeyError, TypeError, ValueError) as exc:
            return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"Yandex 响应解析失败: {exc}")
