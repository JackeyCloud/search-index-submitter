from __future__ import annotations

from collections.abc import Callable, Iterable

from .config import AppConfig
from .engine import build_providers
from .http import HttpClient
from .models import IndexCheck, SiteTarget
from .targets import parse_targets


IndexCallback = Callable[[str, str, IndexCheck], None]


def refresh_index_statuses(
    urls: Iterable[str],
    provider_ids: Iterable[str],
    config: AppConfig,
    callback: IndexCallback | None = None,
) -> list[tuple[str, str, IndexCheck]]:
    targets = parse_targets("\n".join(urls))
    client = HttpClient(timeout=config.request_timeout)
    providers = build_providers(config, client)
    results: list[tuple[str, str, IndexCheck]] = []
    for target in targets:
        for url in target.urls:
            for provider_id in provider_ids:
                provider = providers[provider_id]
                check = provider.check_indexed(target, url)
                item = (url, provider_id, check)
                results.append(item)
                if callback:
                    callback(*item)
    return results
