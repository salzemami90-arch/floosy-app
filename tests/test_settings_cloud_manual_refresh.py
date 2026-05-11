from services import cloud_state_helpers
from pages_floosy import settings_page


class _FakeSt:
    def __init__(self):
        self.session_state = {
            "cloud_auth": {
                "logged_in": True,
                "email": "old@example.com",
                "user_id": "user-old",
                "access_token": "old-access",
                "refresh_token": "old-refresh",
            },
            "_cloud_remember_login": True,
        }


class _RefreshClient:
    def __init__(self, result):
        self.result = result
        self.seen_refresh_token = ""

    def refresh_session(self, refresh_token):
        self.seen_refresh_token = refresh_token
        return self.result


def test_manual_cloud_action_refreshes_expired_access_token(monkeypatch):
    fake_st = _FakeSt()
    remembered = {}
    monkeypatch.setattr(settings_page, "st", fake_st)
    monkeypatch.setattr(cloud_state_helpers, "st", fake_st)
    monkeypatch.setattr(
        settings_page,
        "remember_cloud_auth",
        lambda email, user_id, refresh_token: remembered.update(
            {"email": email, "user_id": user_id, "refresh_token": refresh_token}
        ),
    )
    client = _RefreshClient(
        {
            "ok": True,
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "user": {"id": "user-new", "email": "new@example.com"},
        }
    )

    cloud_auth, error = settings_page._refresh_cloud_auth_for_manual_action(client)

    assert error == ""
    assert client.seen_refresh_token == "old-refresh"
    assert cloud_auth["access_token"] == "new-access"
    assert cloud_auth["refresh_token"] == "new-refresh"
    assert cloud_auth["user_id"] == "user-new"
    assert fake_st.session_state["_cloud_auth_issued_at"]
    assert remembered == {
        "email": "new@example.com",
        "user_id": "user-new",
        "refresh_token": "new-refresh",
    }


def test_manual_cloud_action_reports_refresh_failure(monkeypatch):
    fake_st = _FakeSt()
    monkeypatch.setattr(settings_page, "st", fake_st)
    monkeypatch.setattr(cloud_state_helpers, "st", fake_st)
    client = _RefreshClient({"ok": False, "error": "JWT expired"})

    cloud_auth, error = settings_page._refresh_cloud_auth_for_manual_action(client)

    assert cloud_auth["access_token"] == "old-access"
    assert error == "JWT expired"
    assert fake_st.session_state["_cloud_sync_last_error"] == "token_refresh_failed"
