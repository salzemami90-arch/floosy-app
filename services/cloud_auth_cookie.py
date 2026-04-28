from __future__ import annotations

import base64
import json
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import unquote

import streamlit as st
import streamlit.components.v1 as components


COOKIE_NAME = "floosy_cloud_auth"
STORAGE_NAME = "floosy_cloud_auth_storage"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30
_BROWSER_STORAGE_PENDING = "__PENDING__"
_BROWSER_STORAGE_BRIDGE = components.declare_component(
    "cloud_auth_browser_bridge",
    path=str(Path(__file__).resolve().parent.parent / "components" / "cloud_auth_browser_bridge"),
)


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


def _extract_auth_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not refresh_token:
        return {}
    return {
        "email": str(payload.get("email") or "").strip(),
        "user_id": str(payload.get("user_id") or "").strip(),
        "refresh_token": refresh_token,
    }


def read_cloud_auth_cookie() -> dict:
    raw_value = ""
    try:
        cookies = getattr(st.context, "cookies", {})
        raw_value = cookies.get(COOKIE_NAME, "") if cookies is not None else ""
    except Exception:
        raw_value = ""

    if not raw_value:
        try:
            headers = getattr(st.context, "headers", {}) or {}
        except Exception:
            headers = {}

        raw_cookie_header = ""
        if hasattr(headers, "get"):
            raw_cookie_header = str(headers.get("cookie") or headers.get("Cookie") or "").strip()
        elif isinstance(headers, dict):
            normalized_headers = {str(k).lower(): v for k, v in headers.items()}
            raw_cookie_header = str(normalized_headers.get("cookie") or "").strip()

        if raw_cookie_header:
            parsed = SimpleCookie()
            try:
                parsed.load(raw_cookie_header)
            except Exception:
                parsed = SimpleCookie()
            morsel = parsed.get(COOKIE_NAME)
            if morsel is not None:
                raw_value = morsel.value

    return _extract_auth_payload(_decode_payload(raw_value))


def sync_cloud_auth_browser_storage(payload: dict | None = None, *, clear: bool = False) -> tuple[dict, bool]:
    encoded_value = ""
    if not clear and isinstance(payload, dict):
        normalized_payload = _extract_auth_payload(payload)
        if normalized_payload:
            encoded_value = _encode_payload(normalized_payload)

    raw_value = _BROWSER_STORAGE_BRIDGE(
        storageName=STORAGE_NAME,
        value=encoded_value,
        action="clear" if clear else "sync",
        default=_BROWSER_STORAGE_PENDING,
        key="cloud_auth_browser_bridge",
    )
    if raw_value == _BROWSER_STORAGE_PENDING:
        return {}, False

    return _extract_auth_payload(_decode_payload(str(raw_value or ""))), True


def _render_cookie_script(value: str, max_age: int, *, reload_after_write: bool = False) -> None:
    cookie_name = json.dumps(COOKIE_NAME)
    storage_name = json.dumps(STORAGE_NAME)
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
          const shouldReloadAfterWrite = {"true" if reload_after_write else "false"};

          function collectWindows() {{
            const wins = [];
            let current = window;
            while (current) {{
              if (!wins.includes(current)) {{
                wins.push(current);
              }}
              let nextWin = null;
              try {{
                nextWin = current.parent && current.parent !== current ? current.parent : null;
              }} catch (error) {{
                nextWin = null;
              }}
              if (!nextWin) break;
              current = nextWin;
            }}
            try {{
              if (window.top && !wins.includes(window.top)) {{
                wins.push(window.top);
              }}
            }} catch (error) {{}}
            return wins;
          }}

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

          function getStorage(targetWin) {{
            try {{
              return targetWin && targetWin.localStorage ? targetWin.localStorage : null;
            }} catch (error) {{
              return null;
            }}
          }}

          const wins = collectWindows();
          const hostnames = Array.from(new Set(wins.map((win) => safeHostname(win)).filter(Boolean)));

          const protocol = wins.map((win) => safeProtocol(win)).find(Boolean) || safeProtocol(window);
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

          const targets = Array.from(new Set(wins.map((win) => {{
            try {{
              return win && win.document ? win.document : null;
            }} catch (error) {{
              return null;
            }}
          }}).filter(Boolean)));

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

          const storages = Array.from(new Set(wins.map((win) => getStorage(win)).filter(Boolean)));

          for (const storage of storages) {{
            try {{
              if ({cookie_max_age} > 0 && {cookie_value}) {{
                storage.setItem({storage_name}, {cookie_value});
              }} else {{
                storage.removeItem({storage_name});
              }}
            }} catch (error) {{}}
          }}

          if (shouldReloadAfterWrite) {{
            window.setTimeout(() => {{
              try {{
                window.location.replace(String(window.location.href || ""));
                return;
              }} catch (error) {{}}
              try {{
                window.location.reload();
              }} catch (error) {{}}
            }}, 40);
          }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def remember_cloud_auth(email: str, user_id: str, refresh_token: str, *, reload_after_write: bool = False) -> None:
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
    _render_cookie_script(value, COOKIE_MAX_AGE_SECONDS, reload_after_write=reload_after_write)


def clear_cloud_auth_cookie() -> None:
    _render_cookie_script("", 0)


def bootstrap_cloud_auth_from_storage() -> None:
    cookie_name = json.dumps(COOKIE_NAME)
    storage_name = json.dumps(STORAGE_NAME)
    cookie_max_age = int(COOKIE_MAX_AGE_SECONDS)
    components.html(
        f"""
        <script>
        (function() {{
          const cookieName = {cookie_name};
          const storageName = {storage_name};
          const maxAge = {cookie_max_age};
          const bootFlag = `${{storageName}}_bootstrap_done`;

          function collectWindows() {{
            const wins = [];
            let current = window;
            while (current) {{
              if (!wins.includes(current)) {{
                wins.push(current);
              }}
              let nextWin = null;
              try {{
                nextWin = current.parent && current.parent !== current ? current.parent : null;
              }} catch (error) {{
                nextWin = null;
              }}
              if (!nextWin) break;
              current = nextWin;
            }}
            try {{
              if (window.top && !wins.includes(window.top)) {{
                wins.push(window.top);
              }}
            }} catch (error) {{}}
            return wins;
          }}

          function getStorage(targetWin) {{
            try {{
              return targetWin && targetWin.localStorage ? targetWin.localStorage : null;
            }} catch (error) {{
              return null;
            }}
          }}

          function getSessionStorage(targetWin) {{
            try {{
              return targetWin && targetWin.sessionStorage ? targetWin.sessionStorage : null;
            }} catch (error) {{
              return null;
            }}
          }}

          function readCookie(targetDoc, name) {{
            if (!targetDoc || !targetDoc.cookie) return "";
            const prefix = `${{name}}=`;
            const parts = String(targetDoc.cookie).split(";").map((part) => part.trim());
            for (const part of parts) {{
              if (part.startsWith(prefix)) {{
                return part.slice(prefix.length);
              }}
            }}
            return "";
          }}

          function writeCookie(targetDoc, cookieString) {{
            if (!targetDoc) return;
            try {{
              targetDoc.cookie = cookieString;
            }} catch (error) {{}}
          }}

          function safeHostname(targetWin) {{
            try {{
              return String((targetWin && targetWin.location && targetWin.location.hostname) || "").trim();
            }} catch (error) {{
              return "";
            }}
          }}

          function safeProtocol(targetWin) {{
            try {{
              return String((targetWin && targetWin.location && targetWin.location.protocol) || "").trim().toLowerCase();
            }} catch (error) {{
              return "";
            }}
          }}
          const wins = collectWindows();
          const storages = Array.from(new Set(wins.map((win) => getStorage(win)).filter(Boolean)));
          const sessionStores = Array.from(new Set(wins.map((win) => getSessionStorage(win)).filter(Boolean)));
          const docs = Array.from(new Set(wins.map((win) => {{
            try {{
              return win && win.document ? win.document : null;
            }} catch (error) {{
              return null;
            }}
          }}).filter(Boolean)));

          const cookieExists = docs.some((targetDoc) => !!readCookie(targetDoc, cookieName));
          if (cookieExists) {{
            for (const store of sessionStores) {{
              try {{
                store.removeItem(bootFlag);
              }} catch (error) {{}}
            }}
            return;
          }}

          let storedValue = "";
          for (const storage of storages) {{
            try {{
              storedValue = String(storage.getItem(storageName) || "").trim();
            }} catch (error) {{
              storedValue = "";
            }}
            if (storedValue) break;
          }}

          if (!storedValue) {{
            for (const store of sessionStores) {{
              try {{
                store.removeItem(bootFlag);
              }} catch (error) {{}}
            }}
            return;
          }}

          const alreadyBootstrapped = sessionStores.some((store) => {{
            try {{
              return store.getItem(bootFlag) === storedValue;
            }} catch (error) {{
              return false;
            }}
          }});
          if (alreadyBootstrapped) {{
            return;
          }}

          const protocol = wins.map((win) => safeProtocol(win)).find(Boolean) || safeProtocol(window);
          const isHttps = protocol === "https:";
          const expiry = "";
          const baseAttrs = `path=/; max-age=${{maxAge}}${{expiry}}`;
          const variants = [
            `${{cookieName}}=${{encodeURIComponent(storedValue)}}; ${{baseAttrs}}; SameSite=Lax${{isHttps ? "; Secure" : ""}}`,
          ];

          if (isHttps) {{
            variants.push(
              `${{cookieName}}=${{encodeURIComponent(storedValue)}}; ${{baseAttrs}}; SameSite=None; Secure`,
              `${{cookieName}}=${{encodeURIComponent(storedValue)}}; ${{baseAttrs}}; SameSite=None; Secure; Partitioned`,
            );
          }}

          const hostnames = Array.from(new Set(wins.map((win) => safeHostname(win)).filter(Boolean)));

          for (const targetDoc of docs) {{
            for (const variant of variants) {{
              writeCookie(targetDoc, variant);
              for (const hostname of hostnames) {{
                if (hostname.includes(".")) {{
                  writeCookie(targetDoc, `${{variant}}; domain=${{hostname}}`);
                }}
              }}
            }}
          }}

          for (const store of sessionStores) {{
            try {{
              store.setItem(bootFlag, storedValue);
            }} catch (error) {{}}
          }}

          const reloadTargets = wins.slice().reverse();
          for (const targetWin of reloadTargets) {{
            try {{
              if (targetWin && targetWin.location) {{
                targetWin.location.replace(String(targetWin.location.href || ""));
                return;
              }}
            }} catch (error) {{}}
          }}

          try {{
            window.location.reload();
          }} catch (error) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
