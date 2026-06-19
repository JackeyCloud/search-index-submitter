from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from .config import CONFIG_DIR
from .models import IndexState, SubmissionResult


HISTORY_PATH = CONFIG_DIR / "history.db"
ENGINE_IDS = ("google", "baidu", "bing", "yandex", "360", "shenma")


@dataclass(frozen=True)
class HistoryRecord:
    url: str
    first_submitted_at: str
    last_submitted_at: str
    submission_count: int
    submitted_providers: dict[str, str]
    index_statuses: dict[str, str]
    last_checked_at: str | None


class HistoryStore:
    def __init__(self, path: Path = HISTORY_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS submission_history (
                    url TEXT PRIMARY KEY,
                    first_submitted_at TEXT NOT NULL,
                    last_submitted_at TEXT NOT NULL,
                    submission_count INTEGER NOT NULL DEFAULT 1,
                    submitted_providers TEXT NOT NULL DEFAULT '{}',
                    index_statuses TEXT NOT NULL DEFAULT '{}',
                    last_checked_at TEXT
                )
                """
            )

    def record_submission(self, urls: list[str], results: list[SubmissionResult]) -> None:
        now = _now()
        for url in urls:
            submitted: dict[str, str] = {}
            indexed: dict[str, str] = {}
            for result in results:
                if not _same_site(url, result.target):
                    continue
                provider_id = str(result.details.get("provider_id", ""))
                if provider_id:
                    submitted[provider_id] = result.status.value
                for check in result.details.get("index_checks", []):
                    if isinstance(check, dict) and check.get("url") == url:
                        state = str(check.get("state", IndexState.UNKNOWN.value))
                        if provider_id in ENGINE_IDS and state != IndexState.UNKNOWN.value:
                            indexed[provider_id] = state
            self._upsert(url, now, submitted, indexed)

    def _upsert(self, url: str, now: str, submitted: dict[str, str], indexed: dict[str, str]) -> None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM submission_history WHERE url = ?", (url,)).fetchone()
            if row:
                old_submitted = _json_dict(row["submitted_providers"])
                old_indexed = _json_dict(row["index_statuses"])
                old_submitted.update(submitted)
                old_indexed.update(indexed)
                connection.execute(
                    """
                    UPDATE submission_history
                    SET last_submitted_at = ?, submission_count = submission_count + 1,
                        submitted_providers = ?, index_statuses = ?
                    WHERE url = ?
                    """,
                    (now, _dump(old_submitted), _dump(old_indexed), url),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO submission_history
                    (url, first_submitted_at, last_submitted_at, submitted_providers, index_statuses)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (url, now, now, _dump(submitted), _dump(indexed)),
                )

    def update_index_status(self, url: str, provider_id: str, state: IndexState) -> None:
        if provider_id not in ENGINE_IDS:
            return
        now = _now()
        with self._connect() as connection:
            row = connection.execute("SELECT index_statuses FROM submission_history WHERE url = ?", (url,)).fetchone()
            if not row:
                return
            statuses = _json_dict(row["index_statuses"])
            if state is not IndexState.UNKNOWN:
                statuses[provider_id] = state.value
            connection.execute(
                "UPDATE submission_history SET index_statuses = ?, last_checked_at = ? WHERE url = ?",
                (_dump(statuses), now, url),
            )

    def list_records(self, limit: int = 500) -> list[HistoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM submission_history ORDER BY last_submitted_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            HistoryRecord(
                url=row["url"],
                first_submitted_at=row["first_submitted_at"],
                last_submitted_at=row["last_submitted_at"],
                submission_count=row["submission_count"],
                submitted_providers=_json_dict(row["submitted_providers"]),
                index_statuses=_json_dict(row["index_statuses"]),
                last_checked_at=row["last_checked_at"],
            )
            for row in rows
        ]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _same_site(url: str, site_url: str) -> bool:
    left = urlsplit(url)
    right = urlsplit(site_url)
    return left.scheme == right.scheme and left.netloc == right.netloc


def _json_dict(value: str) -> dict[str, str]:
    try:
        data = json.loads(value)
        return {str(key): str(item) for key, item in data.items()} if isinstance(data, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _dump(value: dict[str, str]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
