from __future__ import annotations

import json as json_lib
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


try:  # Prefer real requests when the runtime/venv provides it.
    import requests as requests  # type: ignore
except Exception:  # pragma: no cover - exercised only in minimal runtimes.

    class Response:
        def __init__(self, *, status_code: int, body: bytes, headers: dict[str, str] | None = None, url: str = "") -> None:
            self.status_code = status_code
            self._body = body
            self.headers = headers or {}
            self.url = url
            self.text = body.decode("utf-8", errors="replace")

        def json(self) -> Any:
            return json_lib.loads(self.text or "null")

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code} ao consultar {self.url}: {self.text[:300]}")

    def _request(method: str, url: str, *, params: dict[str, Any] | None = None, json: Any = None, timeout: int | float | None = None, headers: dict[str, str] | None = None) -> Response:
        final_url = url
        if params:
            sep = "&" if "?" in final_url else "?"
            final_url = f"{final_url}{sep}{urlencode(params, doseq=True)}"

        data = None
        req_headers = dict(headers or {})
        if json is not None:
            data = json_lib.dumps(json).encode("utf-8")
            req_headers.setdefault("content-type", "application/json")
        req_headers.setdefault("user-agent", "multichain-wallet-portfolio/1.1")

        request = Request(final_url, data=data, headers=req_headers, method=method.upper())
        try:
            with urlopen(request, timeout=timeout or 30) as response:
                return Response(
                    status_code=getattr(response, "status", 200),
                    body=response.read(),
                    headers=dict(response.headers.items()),
                    url=final_url,
                )
        except HTTPError as exc:
            return Response(status_code=exc.code, body=exc.read(), headers=dict(exc.headers.items()), url=final_url)
        except URLError as exc:
            raise RuntimeError(f"Falha HTTP ao consultar {final_url}: {exc}") from exc

    def get(url: str, **kwargs: Any) -> Response:
        return _request("GET", url, **kwargs)

    def post(url: str, **kwargs: Any) -> Response:
        return _request("POST", url, **kwargs)

    requests = SimpleNamespace(get=get, post=post, Response=Response)
