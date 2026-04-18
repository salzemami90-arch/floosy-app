from __future__ import annotations

import base64
import json
from urllib.parse import unquote

import streamlit as st
import streamlit.components.v1 as components


COOKIE_NAME = "floosy_cloud_auth"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


def _encode_payload(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_payload(raw_value: str) -> dict:
    clean_value = unquote(str(raw_value or "").strip())
    if not clean_value:
        return {}
    padding = "=" * (-len(clean_value) % 4)
    try:
        decoded = base64.urlsafe_b64decode((clean_value + padding).encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_cloud_auth_cookie() -> dict:
    try:
        cookies = getattr(st.context, "cookies", {})
        raw_value = cookies.get(COOKIE_NAME, "") if cookies is not None else ""
    except Exception:
        raw_value = ""
    payload = _decode_payload(raw_value)
    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not refresh_token:
        return {}
    return {
        "email": str(payload.get("email") or "").strip(),
        "user_id": str(payload.get("user_id") or "").strip(),
        "refresh_token": refresh_token,
    }


def _render_cookie_script(value: str, max_age: int) -> None:
    cookie_name = json.dumps(COOKIE_NAME)
    cookie_value = json.dumps(value)
    cookie_max_age = int(max_age)
    components.html(
        f"""
        <script>
        (function() {{
          const name = {cookie_name};
          const value = encodeURIComponent({cookie_value});
          const cookie = `${{name}}=${{value}}; path=/; max-age={cookie_max_age}; SameSite=Lax`;
          document.cookie = cookie;
          try {{
            window.parent.document.cookie = cookie;
          }} catch (error) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def remember_cloud_auth(email: str, user_id: str, refresh_token: str) -> None:
    clean_refresh_token = str(refresh_token or "").strip()
    if not clean_refresh_token:
        return
    value = _encode_payload(
        {
            "email": str(email or "").strip(),
            "user_id": str(user_id or "").strip(),
            "refresh_token": clean_refresh_token,
        }
    )
    _render_cookie_script(value, COOKIE_MAX_AGE_SECONDS)


def clear_cloud_auth_cookie() -> None:
    _render_cookie_script("", 0)
