from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

import requests


class SupabaseSyncClient:
    def __init__(self, supabase_url: str, anon_key: str, table_name: str = "user_app_data", timeout_sec: int = 15):
        self.supabase_url = (supabase_url or "").strip().rstrip("/")
        self.anon_key = (anon_key or "").strip()
        self.table_name = table_name
        self.timeout_sec = timeout_sec

    @classmethod
    def from_runtime(cls, secrets: Any = None) -> "SupabaseSyncClient":
        secret_url = ""
        secret_key = ""
        secret_table_name = ""

        if secrets is not None:
            try:
                secret_url = str(secrets.get("SUPABASE_URL", "") or "")
                secret_key = str(secrets.get("SUPABASE_ANON_KEY", "") or "")
                secret_table_name = str(secrets.get("SUPABASE_DATA_TABLE", "") or "")
            except Exception:
                secret_url = ""
                secret_key = ""
                secret_table_name = ""

        url = secret_url or os.getenv("SUPABASE_URL", "")
        key = secret_key or os.getenv("SUPABASE_ANON_KEY", "")
        table_name = secret_table_name or os.getenv("SUPABASE_DATA_TABLE", "user_app_data")
        return cls(url, key, table_name=table_name)

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.anon_key)

    def _headers(self, access_token: str | None = None, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if prefer:
            headers["Prefer"] = prefer
        return headers

    @staticmethod
    def _json_or_text(resp: requests.Response) -> Any:
        try:
            return resp.json()
        except Exception:
            return resp.text

    def sign_up(self, email: str, password: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        url = f"{self.supabase_url}/auth/v1/signup"
        payload = {"email": email.strip(), "password": password}

        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("msg") or data.get("error_description") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {
            "ok": True,
            "user": data.get("user") if isinstance(data, dict) else None,
            "access_token": data.get("access_token") if isinstance(data, dict) else None,
            "refresh_token": data.get("refresh_token") if isinstance(data, dict) else None,
            "raw": data,
        }

    def sign_in(self, email: str, password: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
        payload = {"email": email.strip(), "password": password}

        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=self.timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("msg") or data.get("error_description") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {
            "ok": True,
            "user": data.get("user") if isinstance(data, dict) else None,
            "access_token": data.get("access_token") if isinstance(data, dict) else None,
            "refresh_token": data.get("refresh_token") if isinstance(data, dict) else None,
            "raw": data,
        }

    def get_user(self, access_token: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        url = f"{self.supabase_url}/auth/v1/user"
        try:
            resp = requests.get(url, headers=self._headers(access_token=access_token), timeout=self.timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("msg") or data.get("error_description") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {"ok": True, "user": data if isinstance(data, dict) else None}

    def upsert_user_data(self, user_id: str, access_token: str, data_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        if not user_id:
            return {"ok": False, "error": "Missing user_id."}

        url = f"{self.supabase_url}/rest/v1/{self.table_name}"
        payload = [
            {
                "user_id": user_id,
                "data": data_payload,
                "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
        ]

        headers = self._headers(
            access_token=access_token,
            prefer="resolution=merge-duplicates,return=representation",
        )

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("message") or data.get("hint") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {"ok": True, "raw": data}

    def fetch_user_data(self, user_id: str, access_token: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        if not user_id:
            return {"ok": False, "error": "Missing user_id."}

        user_filter = quote(user_id, safe="")
        url = (
            f"{self.supabase_url}/rest/v1/{self.table_name}"
            f"?select=data,updated_at&user_id=eq.{user_filter}&limit=1"
        )

        try:
            resp = requests.get(url, headers=self._headers(access_token=access_token), timeout=self.timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("message") or data.get("hint") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        if isinstance(data, list) and data:
            row = data[0]
            return {
                "ok": True,
                "data": row.get("data") if isinstance(row, dict) else None,
                "updated_at": row.get("updated_at") if isinstance(row, dict) else None,
            }

        return {"ok": True, "data": None, "updated_at": None}

    def delete_user_data(self, user_id: str, access_token: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        if not user_id:
            return {"ok": False, "error": "Missing user_id."}

        user_filter = quote(user_id, safe="")
        url = f"{self.supabase_url}/rest/v1/{self.table_name}?user_id=eq.{user_filter}"

        try:
            resp = requests.delete(
                url,
                headers=self._headers(
                    access_token=access_token,
                    prefer="return=representation",
                ),
                timeout=self.timeout_sec,
            )
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("message") or data.get("hint") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {"ok": True, "raw": data}


    def delete_current_user(self, access_token: str) -> dict[str, Any]:
        if not self.is_configured:
            return {"ok": False, "error": "Supabase config is missing."}

        if not access_token:
            return {"ok": False, "error": "Missing access token."}

        url = f"{self.supabase_url}/auth/v1/user"

        try:
            resp = requests.delete(
                url,
                headers=self._headers(access_token=access_token),
                timeout=self.timeout_sec,
            )
        except Exception as exc:
            return {"ok": False, "error": f"Network error: {exc}"}

        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            if isinstance(data, dict):
                message = str(data.get("msg") or data.get("error_description") or data.get("error") or data)
            else:
                message = str(data)
            return {"ok": False, "error": message}

        return {"ok": True, "raw": data}
