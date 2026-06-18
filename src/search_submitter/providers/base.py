from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import AppConfig
from ..http import HttpClient
from ..models import IndexCheck, IndexState, SiteTarget, SubmissionResult


class Provider(ABC):
    id: str
    display_name: str

    def __init__(self, config: AppConfig, client: HttpClient):
        self.config = config
        self.client = client

    def check_indexed(self, target: SiteTarget, url: str) -> IndexCheck:
        return IndexCheck(IndexState.UNKNOWN, "该平台没有配置可用的精确 URL 查询接口")

    @abstractmethod
    def submit(self, target: SiteTarget, sitemap_url: str, dry_run: bool = False) -> SubmissionResult:
        raise NotImplementedError
