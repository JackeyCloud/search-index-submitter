from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .config import AppConfig
from .engine import run_submissions
from .targets import parse_targets


PROVIDER_IDS = ("indexnow", "baidu", "google", "bing", "yandex", "360", "shenma")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量提交网站 URL 和 Sitemap 到搜索平台")
    parser.add_argument("targets", nargs="*", help="域名或完整 URL，可输入多个")
    parser.add_argument("--file", help="从文本文件读取域名/URL")
    parser.add_argument("--sitemap", default="", help="Sitemap URL，支持 {site} 和 {host}")
    parser.add_argument("--providers", default="indexnow,baidu,google,bing,yandex", help="逗号分隔的平台 ID")
    parser.add_argument("--dry-run", action="store_true", help="仅预检，不调用提交接口")
    parser.add_argument("--no-deduplicate", action="store_true", help="跳过提交前收录查重")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    values = list(args.targets)
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as handle:
                values.append(handle.read())
        except OSError as exc:
            print(f"读取文件失败: {exc}", file=sys.stderr)
            return 2
    if not values:
        print("请至少提供一个域名或 URL", file=sys.stderr)
        return 2
    provider_ids = [item.strip() for item in args.providers.split(",") if item.strip()]
    invalid = sorted(set(provider_ids) - set(PROVIDER_IDS))
    if invalid:
        print(f"未知平台: {', '.join(invalid)}", file=sys.stderr)
        return 2
    try:
        targets = parse_targets("\n".join(values), args.sitemap)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    results = run_submissions(
        targets,
        provider_ids,
        AppConfig.load(),
        dry_run=args.dry_run,
        check_existing=not args.no_deduplicate,
    )
    if args.json:
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"[{item.status.value:8}] {item.provider} | {item.target} | {item.message}")
    return 1 if any(item.status.value == "failed" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
