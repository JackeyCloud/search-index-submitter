from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace

from .config import AppConfig
from .discovery import discover_sitemap
from .http import HttpClient
from .models import IndexState, SiteTarget, Status, SubmissionResult
from .providers import BaiduProvider, BingProvider, GoogleProvider, IndexNowProvider, ManualProvider, YandexProvider


ProgressCallback = Callable[[SubmissionResult], None]


def build_providers(config: AppConfig, client: HttpClient):
    args = (config, client)
    return {
        "indexnow": IndexNowProvider(*args),
        "baidu": BaiduProvider(*args),
        "google": GoogleProvider(*args),
        "bing": BingProvider(*args),
        "yandex": YandexProvider(*args),
        "360": ManualProvider("360", "360 搜索站长平台", "https://zhanzhang.so.com/", *args),
        "shenma": ManualProvider("shenma", "神马搜索站长平台", "https://zhanzhang.sm.cn/", *args),
    }


def run_submissions(
    targets: Iterable[SiteTarget],
    provider_ids: Iterable[str],
    config: AppConfig,
    *,
    dry_run: bool = False,
    check_existing: bool = True,
    callback: ProgressCallback | None = None,
) -> list[SubmissionResult]:
    client = HttpClient(timeout=config.request_timeout)
    providers = build_providers(config, client)
    results: list[SubmissionResult] = []
    for target in targets:
        sitemap_url, source = discover_sitemap(target, client)
        for provider_id in provider_ids:
            provider = providers[provider_id]
            submit_target = target
            checks = []
            if check_existing:
                remaining = []
                for url in target.urls:
                    check = provider.check_indexed(target, url)
                    checks.append({"url": url, "state": check.state.value, "message": check.message})
                    if check.state is not IndexState.INDEXED:
                        remaining.append(url)
                if not remaining and target.urls:
                    result = SubmissionResult(provider.display_name, target.site_url, Status.SKIPPED, f"查重完成：{len(target.urls)} 个 URL 均已收录，无需重复提交")
                else:
                    submit_target = replace(target, urls=tuple(remaining))
                    result = provider.submit(submit_target, sitemap_url, dry_run=dry_run)
                    indexed_count = len(target.urls) - len(remaining)
                    unknown_count = sum(item["state"] == IndexState.UNKNOWN.value for item in checks)
                    result = replace(result, message=f"查重：{indexed_count} 已收录，{len(remaining)} 待处理，{unknown_count} 无法确认；{result.message}")
            else:
                result = provider.submit(submit_target, sitemap_url, dry_run=dry_run)
            details = dict(result.details)
            details.update({"sitemap": sitemap_url, "sitemap_source": source, "index_checks": checks})
            result = SubmissionResult(result.provider, result.target, result.status, result.message, details)
            results.append(result)
            if callback:
                callback(result)
    return results
