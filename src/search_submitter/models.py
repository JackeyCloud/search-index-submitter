from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    MANUAL = "manual"
    DRY_RUN = "dry_run"


class IndexState(str, Enum):
    INDEXED = "indexed"
    NOT_INDEXED = "not_indexed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IndexCheck:
    state: IndexState
    message: str


@dataclass(frozen=True)
class SiteTarget:
    original: str
    site_url: str
    urls: tuple[str, ...] = ()
    sitemap_url: str | None = None

    @property
    def host(self) -> str:
        from urllib.parse import urlsplit

        return urlsplit(self.site_url).hostname or ""


@dataclass(frozen=True)
class SubmissionResult:
    provider: str
    target: str
    status: Status
    message: str
    details: dict[str, object] = field(default_factory=dict)
