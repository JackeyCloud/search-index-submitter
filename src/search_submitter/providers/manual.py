from __future__ import annotations

from ..models import SiteTarget, Status, SubmissionResult
from .base import Provider


class ManualProvider(Provider):
    def __init__(self, provider_id: str, display_name: str, portal: str, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.id = provider_id
        self.display_name = display_name
        self.portal = portal

    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        return SubmissionResult(self.display_name, target.site_url, Status.MANUAL, f"暂无稳定公开提交 API，请在站长平台验证站点后提交：{self.portal}", {"portal": self.portal, "sitemap": sitemap_url})
