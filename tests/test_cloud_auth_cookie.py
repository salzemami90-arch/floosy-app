from types import SimpleNamespace

from services.cloud_auth_cookie import (
    bootstrap_cloud_auth_from_storage,
    clear_cloud_auth_cookie,
    read_cloud_auth_cookie,
    remember_cloud_auth,
    sync_cloud_auth_browser_storage,
)


def test_remember_cloud_auth_renders_hosted_cookie_variants(monkeypatch):
    captured = {}

    def fake_html(html, height=0, width=0):
        captured["html"] = html
        captured["height"] = height
        captured["width"] = width

    monkeypatch.setattr("services.cloud_auth_cookie.components.html", fake_html)

    remember_cloud_auth("user@example.com", "user-123", "refresh-token-xyz")

    html = captured["html"]
    assert "SameSite=Lax" in html
    assert "SameSite=None; Secure" in html
    assert "Partitioned" in html
    assert "localStorage" in html
    assert "floosy_cloud_auth_storage" in html
    assert "window.top" in html
    assert "collectWindows" in html
    assert "current.parent && current.parent !== current" in html
    assert "domain=${hostname}" in html
    assert captured["height"] == 0
    assert captured["width"] == 0


def test_clear_cloud_auth_cookie_uses_zero_max_age(monkeypatch):
    captured = {}

    def fake_html(html, height=0, width=0):
        captured["html"] = html

    monkeypatch.setattr("services.cloud_auth_cookie.components.html", fake_html)

    clear_cloud_auth_cookie()

    html = captured["html"]
    assert "const maxAge = 0;" in html
    assert "max-age=${maxAge}" in html
    assert "Thu, 01 Jan 1970 00:00:00 GMT" in html


def test_read_cloud_auth_cookie_decodes_payload(monkeypatch):
    service = __import__("services.cloud_auth_cookie", fromlist=["dummy"])
    encoded = service._encode_payload(
        {
            "email": "user@example.com",
            "user_id": "user-123",
            "refresh_token": "refresh-token-xyz",
        }
    )

    fake_st = SimpleNamespace(context=SimpleNamespace(cookies={service.COOKIE_NAME: encoded}))
    monkeypatch.setattr("services.cloud_auth_cookie.st", fake_st)

    assert read_cloud_auth_cookie() == {
        "email": "user@example.com",
        "user_id": "user-123",
        "refresh_token": "refresh-token-xyz",
    }


def test_read_cloud_auth_cookie_returns_empty_when_missing_refresh_token(monkeypatch):
    service = __import__("services.cloud_auth_cookie", fromlist=["dummy"])
    encoded = service._encode_payload(
        {
            "email": "user@example.com",
            "user_id": "user-123",
        }
    )

    fake_st = SimpleNamespace(context=SimpleNamespace(cookies={service.COOKIE_NAME: encoded}))
    monkeypatch.setattr("services.cloud_auth_cookie.st", fake_st)

    assert read_cloud_auth_cookie() == {}


def test_read_cloud_auth_cookie_falls_back_to_cookie_header(monkeypatch):
    service = __import__("services.cloud_auth_cookie", fromlist=["dummy"])
    encoded = service._encode_payload(
        {
            "email": "user@example.com",
            "user_id": "user-123",
            "refresh_token": "refresh-token-xyz",
        }
    )

    fake_st = SimpleNamespace(
        context=SimpleNamespace(
            cookies={},
            headers={"cookie": f"another=value; {service.COOKIE_NAME}={encoded}; theme=dark"},
        )
    )
    monkeypatch.setattr("services.cloud_auth_cookie.st", fake_st)

    assert read_cloud_auth_cookie() == {
        "email": "user@example.com",
        "user_id": "user-123",
        "refresh_token": "refresh-token-xyz",
    }


def test_bootstrap_cloud_auth_from_storage_renders_reload_bridge(monkeypatch):
    captured = {}

    def fake_html(html, height=0, width=0):
        captured["html"] = html
        captured["height"] = height
        captured["width"] = width

    monkeypatch.setattr("services.cloud_auth_cookie.components.html", fake_html)

    bootstrap_cloud_auth_from_storage()

    html = captured["html"]
    assert "floosy_cloud_auth_storage" in html
    assert "sessionStorage" in html
    assert "location.replace" in html
    assert "bootFlag" in html
    assert "collectWindows" in html
    assert "window.top" in html
    assert captured["height"] == 0
    assert captured["width"] == 0


def test_sync_cloud_auth_browser_storage_returns_pending_until_frontend_replies(monkeypatch):
    monkeypatch.setattr(
        "services.cloud_auth_cookie._BROWSER_STORAGE_BRIDGE",
        lambda **kwargs: "__PENDING__",
    )

    payload, ready = sync_cloud_auth_browser_storage()

    assert payload == {}
    assert ready is False


def test_sync_cloud_auth_browser_storage_decodes_returned_payload(monkeypatch):
    service = __import__("services.cloud_auth_cookie", fromlist=["dummy"])
    encoded = service._encode_payload(
        {
            "email": "user@example.com",
            "user_id": "user-123",
            "refresh_token": "refresh-token-xyz",
        }
    )

    captured = {}

    def fake_component(**kwargs):
        captured.update(kwargs)
        return encoded

    monkeypatch.setattr("services.cloud_auth_cookie._BROWSER_STORAGE_BRIDGE", fake_component)

    payload, ready = sync_cloud_auth_browser_storage(
        {
            "email": "user@example.com",
            "user_id": "user-123",
            "refresh_token": "refresh-token-xyz",
        }
    )

    assert ready is True
    assert payload == {
        "email": "user@example.com",
        "user_id": "user-123",
        "refresh_token": "refresh-token-xyz",
    }
    assert captured["action"] == "sync"
    assert captured["storageName"] == "floosy_cloud_auth_storage"


def test_sync_cloud_auth_browser_storage_can_clear_saved_value(monkeypatch):
    captured = {}

    def fake_component(**kwargs):
        captured.update(kwargs)
        return ""

    monkeypatch.setattr("services.cloud_auth_cookie._BROWSER_STORAGE_BRIDGE", fake_component)

    payload, ready = sync_cloud_auth_browser_storage(clear=True)

    assert ready is True
    assert payload == {}
    assert captured["action"] == "clear"
    assert captured["value"] == ""
