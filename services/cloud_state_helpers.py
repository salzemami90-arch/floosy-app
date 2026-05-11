"""Shared cloud auth and scoped-state helpers.

Used by both app.py and settings_page.py to avoid duplicated definitions.
"""

from datetime import datetime

import streamlit as st

from services.cloud_sync_guard import clear_cloud_sync_guard


def set_cloud_auth(
    logged_in: bool,
    email: str = "",
    user_id: str = "",
    access_token: str = "",
    refresh_token: str = "",
) -> None:
    st.session_state["cloud_auth"] = {
        "logged_in": bool(logged_in),
        "email": email,
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    if bool(logged_in) and access_token:
        st.session_state["_cloud_auth_issued_at"] = datetime.now().isoformat(timespec="seconds")
    elif not bool(logged_in):
        st.session_state["_cloud_auth_issued_at"] = ""


def set_scope_owner(user_id: str = "", email: str = "") -> None:
    scope = st.session_state.get("app_scope")
    if not isinstance(scope, dict):
        scope = {}
    scope.setdefault("owner_user_id", "")
    scope.setdefault("owner_email", "")
    scope["owner_user_id"] = str(user_id or "")
    scope["owner_email"] = str(email or "")
    st.session_state["app_scope"] = scope


def clear_scoped_finance_state() -> None:
    st.session_state["transactions"] = {}
    st.session_state["savings"] = {}
    st.session_state["project_data"] = {}
    st.session_state["recurring"] = {"items": []}
    st.session_state["documents"] = []
    st.session_state["mustndaty_documents"] = st.session_state["documents"]
    st.session_state["invoices"] = []
    st.session_state["tax_profile"] = {}
    st.session_state["tax_tags"] = []
    st.session_state["_persist_last_snapshot"] = ""
    st.session_state["_cloud_last_snapshot"] = ""
    st.session_state["_cloud_last_pull_user"] = ""
    st.session_state["_cloud_sync_last_error"] = ""
    clear_cloud_sync_guard(st.session_state)
