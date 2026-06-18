from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: str
    headers: dict[str, str]

    def json(self) -> object:
        return json.loads(self.body) if self.body else {}


class HttpClient:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def request(
        self,
        method: str,
        url: str,
        *,
        json_body: object | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        request_headers = {"User-Agent": "SearchIndexSubmitter/0.1"}
        request_headers.update(headers or {})
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            request_headers["Content-Type"] = "application/json; charset=utf-8"
        req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return HttpResponse(response.status, response.read().decode("utf-8", "replace"), dict(response.headers))
        except urllib.error.HTTPError as exc:
            return HttpResponse(exc.code, exc.read().decode("utf-8", "replace"), dict(exc.headers))

    def get(self, url: str, **kwargs: object) -> HttpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: object) -> HttpResponse:
        return self.request("POST", url, **kwargs)
