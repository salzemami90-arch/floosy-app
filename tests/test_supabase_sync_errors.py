from services.supabase_sync import SupabaseSyncClient


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_cloudflare_html_error_is_sanitized():
    raw_html = "<!DOCTYPE html><html><title>521: Web server is down</title>Cloudflare</html>"

    message = SupabaseSyncClient._friendly_error(
        FakeResponse(521),
        raw_html,
        ("msg", "error_description", "error"),
    )

    assert "Supabase is temporarily unavailable" in message
    assert "<html" not in message.lower()
    assert "Cloudflare" not in message


def test_json_error_message_is_preserved():
    message = SupabaseSyncClient._friendly_error(
        FakeResponse(400),
        {"error_description": "Invalid login credentials"},
        ("msg", "error_description", "error"),
    )

    assert message == "Invalid login credentials"
