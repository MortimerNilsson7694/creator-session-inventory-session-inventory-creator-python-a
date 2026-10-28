"""A content-oriented boundary around session cleanup and delivery updates."""

from dataclasses import dataclass
from typing import Protocol

from session_inventory import InfraiSessionClient, sign_out_other_devices


@dataclass(frozen=True)
class ContentRelease:
    asset_id: str
    subscriber_id: str
    processed: bool
    delivery_ready: bool


class SessionClient(Protocol):
    def list_sessions(self, user_id: str) -> list[object]: ...

    def revoke_session(self, session_id: str) -> None: ...


def publish_creator_release(client: InfraiSessionClient, user_id: str, asset_id: str, subscriber_id: str) -> ContentRelease:
    revoked = sign_out_other_devices(client, user_id)
    return ContentRelease(
        asset_id=asset_id,
        subscriber_id=subscriber_id,
        processed=bool(asset_id),
        delivery_ready=bool(subscriber_id) and len(revoked) >= 0,
    )
