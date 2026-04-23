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
          const maxAge = {cookie_max_age};
          const expiry = maxAge === 0 ? "; expires=Thu, 01 Jan 1970 00:00:00 GMT" : "";

          function safeHostname(win) {{
            try {{
              return String((win && win.location && win.location.hostname) || "").trim();
            }} catch (error) {{
              return "";
            }}
          }}

          function safeProtocol(win) {{
            try {{
              return String((win && win.location && win.location.protocol) || "").trim().toLowerCase();
            }} catch (error) {{
              return "";
            }}
          }}

          function writeCookie(targetDoc, cookieString) {{
            if (!targetDoc) return;
            try {{
              targetDoc.cookie = cookieString;
            }} catch (error) {{}}
          }}

          const parentWin = (() => {{
            try {{
              return window.parent && window.parent !== window ? window.parent : null;
            }} catch (error) {{
              return null;
            }}
          }})();

          const hostnames = Array.from(new Set([
            safeHostname(window),
            safeHostname(parentWin),
          ].filter(Boolean)));

          const protocol = safeProtocol(parentWin) || safeProtocol(window);
          const isHttps = protocol === "https:";
          const baseAttrs = `path=/; max-age=${{maxAge}}${{expiry}}`;
          const variants = [
            `${{name}}=${{value}}; ${{baseAttrs}}; SameSite=Lax${{isHttps ? "; Secure" : ""}}`,
          ];

          if (isHttps) {{
            variants.push(
              `${{name}}=${{value}}; ${{baseAttrs}}; SameSite=None; Secure`,
              `${{name}}=${{value}}; ${{baseAttrs}}; SameSite=None; Secure; Partitioned`,
            );
          }}

          const targets = [document];
          try {{
            if (parentWin && parentWin.document) {{
              targets.push(parentWin.document);
            }}
          }} catch (error) {{}}

          for (const targetDoc of targets) {{
            for (const variant of variants) {{
              writeCookie(targetDoc, variant);
              for (const hostname of hostnames) {{
                if (hostname.includes(".")) {{
                  writeCookie(targetDoc, `${{variant}}; domain=${{hostname}}`);
                }}
              }}
            }}
          }}
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
