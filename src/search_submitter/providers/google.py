from __future__ import annotations

from pathlib import Path

from ..models import IndexCheck, IndexState, SiteTarget, Status, SubmissionResult
from .base import Provider


class GoogleProvider(Provider):
    id = "google"
    display_name = "Google Search Console Sitemap"
    scopes = ["https://www.googleapis.com/auth/webmasters"]

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service
        secrets = Path(self.config.google_client_secrets).expanduser() if self.config.google_client_secrets else None
        if not secrets or not secrets.exists():
            raise FileNotFoundError("未配置 Google OAuth 客户端 JSON")
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        token_path = Path(self.config.google_token_file).expanduser() if self.config.google_token_file else secrets.with_name("google-token.json")
        credentials = Credentials.from_authorized_user_file(str(token_path), self.scopes) if token_path.exists() else None
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            credentials = InstalledAppFlow.from_client_secrets_file(str(secrets), self.scopes).run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        self._service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
        return self._service

    def check_indexed(self, target: SiteTarget, url: str) -> IndexCheck:
        try:
            response = self._get_service().urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": target.site_url}
            ).execute()
            result = response.get("inspectionResult", {}).get("indexStatusResult", {})
            verdict = result.get("verdict", "VERDICT_UNSPECIFIED")
            coverage = result.get("coverageState", "状态未知")
            if verdict == "PASS":
                return IndexCheck(IndexState.INDEXED, f"Google 已收录：{coverage}")
            return IndexCheck(IndexState.NOT_INDEXED, f"Google 暂未确认收录：{coverage}")
        except FileNotFoundError as exc:
            return IndexCheck(IndexState.UNKNOWN, str(exc))
        except Exception as exc:
            return IndexCheck(IndexState.UNKNOWN, f"Google URL Inspection 查询失败: {exc}")

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        secrets = Path(self.config.google_client_secrets).expanduser() if self.config.google_client_secrets else None
        if not secrets or not secrets.exists():
            return SubmissionResult(self.display_name, target.site_url, Status.SKIPPED, "未配置 Google OAuth 客户端 JSON")
        if dry_run:
            return SubmissionResult(self.display_name, target.site_url, Status.DRY_RUN, f"将提交 Sitemap: {sitemap_url}")
        try:
            service = self._get_service()
            service.sitemaps().submit(siteUrl=target.site_url, feedpath=sitemap_url).execute()
            return SubmissionResult(self.display_name, target.site_url, Status.SUCCESS, f"Sitemap 已提交: {sitemap_url}")
        except Exception as exc:
            return SubmissionResult(self.display_name, target.site_url, Status.FAILED, f"Google 提交失败: {exc}")
