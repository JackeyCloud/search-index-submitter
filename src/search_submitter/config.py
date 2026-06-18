from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("SEARCH_SUBMITTER_CONFIG_DIR", Path.home() / ".search-index-submitter"))
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    indexnow_key: str = ""
    indexnow_key_location: str = ""
    baidu_token: str = ""
    baidu_token_map: str = ""
    bing_api_key: str = ""
    google_client_secrets: str = ""
    google_token_file: str = ""
    yandex_oauth_token: str = ""
    request_timeout: int = 20

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value for key, value in raw.items() if key in allowed})

    def save(self, path: Path = CONFIG_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def masked(self) -> dict[str, object]:
        raw = asdict(self)
        for key in ("indexnow_key", "baidu_token", "baidu_token_map", "bing_api_key", "yandex_oauth_token"):
            value = str(raw[key])
            raw[key] = f"{value[:3]}...{value[-3:]}" if len(value) > 8 else ("***" if value else "")
        return raw
