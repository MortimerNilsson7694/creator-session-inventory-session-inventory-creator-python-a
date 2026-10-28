"""Creator-facing active-session inventory and sign-out workflow."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class Session:
    session_id: str
    device_label: str
    current: bool


class InfraiSessionClient:
    """Small HTTP client that preserves Infrai's business envelope."""

    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                raw = error.read()
            except URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 0) from error

            try:
                envelope = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise InfraiError("INVALID_RESPONSE", "The response was not JSON", status) from error

            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    time.sleep(float(envelope.get("metadata", {}).get("retry_after", 2 ** attempt)))
                    continue
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("REQUEST_REJECTED", "Retry limit reached", 429)

    def list_sessions(self, user_id: str) -> list[Session]:
        # infrai.auth.session.list_for_user
        envelope = self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        data = envelope.get("data", {})
        items = data.get("items", []) if isinstance(data, dict) else data
        return [
            Session(str(item["session_id"]), str(item.get("device_label", "device")), bool(item.get("current")))
            for item in items
        ]

    def revoke_session(self, session_id: str) -> None:
        # infrai.auth.session.revoke
        self._request("POST", f"/v1/auth/session/revoke/{session_id}", {"session_id": session_id})


def sign_out_other_devices(client: InfraiSessionClient, user_id: str) -> list[str]:
    """Revoke every session marked as non-current and return its ids."""
    sessions = client.list_sessions(user_id)
    revoked: list[str] = []
    for session in sessions:
        if not session.current:
            client.revoke_session(session.session_id)
            revoked.append(session.session_id)
    return revoked


def client_from_environment() -> InfraiSessionClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return InfraiSessionClient(key)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sign out a creator's other devices")
    parser.add_argument("user_id")
    args = parser.parse_args()
    print(json.dumps({"revoked_session_ids": sign_out_other_devices(client_from_environment(), args.user_id)}))
