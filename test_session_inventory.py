from session_inventory import InfraiSessionClient, Session, sign_out_other_devices


class FakeClient:
    def __init__(self) -> None:
        self.revoked: list[str] = []

    def list_sessions(self, user_id: str) -> list[Session]:
        assert user_id == "creator-42"
        return [Session("current-1", "editing laptop", True), Session("old-7", "phone", False)]

    def revoke_session(self, session_id: str) -> None:
        self.revoked.append(session_id)


def test_creator_keeps_current_session_and_signs_out_other_devices() -> None:
    client = FakeClient()
    assert sign_out_other_devices(client, "creator-42") == ["old-7"]
    assert client.revoked == ["old-7"]


def test_list_sessions_decodes_live_items_response() -> None:
    client = InfraiSessionClient("test-key")
    client._request = lambda method, path, body=None: {
        "ok": True,
        "data": {"items": [{"session_id": "old-7", "device_label": "phone", "current": False}]},
    }

    assert client.list_sessions("creator-42") == [Session("old-7", "phone", False)]
