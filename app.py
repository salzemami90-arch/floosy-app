import json
import traceback
from datetime import datetime

import streamlit as st

from config_floosy import (
    _hosted_data_warning_state,
    ensure_month_keys,
    export_app_state_payload,
    get_month_selection,
    import_app_state_payload,
    init_session_state,
    save_persistent_state,
)
from services.cloud_auth_cookie import (
    bootstrap_cloud_auth_from_storage,
    clear_cloud_auth_cookie,
    read_cloud_auth_cookie,
    remember_cloud_auth,
    sync_cloud_auth_browser_storage,
)
from services.cloud_sync_guard import (
    clear_cloud_sync_guard,
    cloud_sync_ready_for_user,
    mark_cloud_sync_ready,
    payload_snapshot,
    pause_cloud_auto_sync,
    should_keep_local_data_before_auto_import,
)
from services.supabase_sync import SupabaseSyncClient


def _set_cloud_auth(logged_in: bool, email: str = "", user_id: str = "", access_token: str = "", refresh_token: str = "") -> None:
    st.session_state["cloud_auth"] = {
        "logged_in": bool(logged_in),
        "email": email,
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def _set_scope_owner(user_id: str = "", email: str = "") -> None:
    scope = st.session_state.get("app_scope")
    if not isinstance(scope, dict):
        scope = {}
    scope["owner_user_id"] = str(user_id or "")
    scope["owner_email"] = str(email or "")
    st.session_state["app_scope"] = scope


def _clear_scoped_finance_state() -> None:
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
    clear_cloud_sync_guard(st.session_state)


def _set_cloud_snapshot_now(user_id: str = "") -> None:
    try:
        snapshot = json.dumps(export_app_state_payload(), ensure_ascii=False, sort_keys=True)
    except Exception:
        snapshot = ""
    st.session_state["_cloud_last_snapshot"] = snapshot
    st.session_state["_cloud_last_pull_user"] = str(user_id or "")


def _sync_cloud_auth_browser_bridge() -> tuple[dict, bool]:
    clear_requested = bool(st.session_state.pop("_cloud_browser_storage_clear_requested", False))
    cloud_auth = st.session_state.get("cloud_auth", {})
    remember_login = st.session_state.get("_cloud_remember_login")

    payload = None
    if (
        not clear_requested
        and isinstance(cloud_auth, dict)
        and cloud_auth.get("logged_in")
        and cloud_auth.get("refresh_token")
        and remember_login is not False
    ):
        payload = {
            "email": str(cloud_auth.get("email") or ""),
            "user_id": str(cloud_auth.get("user_id") or ""),
            "refresh_token": str(cloud_auth.get("refresh_token") or ""),
        }

    return sync_cloud_auth_browser_storage(payload, clear=clear_requested)


def _restore_cloud_auth_from_cookie(browser_storage_auth: dict | None = None, browser_storage_ready: bool = True) -> None:
    if st.session_state.get("_cloud_cookie_restore_checked", False):
        return

    cloud_auth = st.session_state.get("cloud_auth", {})
    if isinstance(cloud_auth, dict) and cloud_auth.get("logged_in") and cloud_auth.get("access_token"):
        st.session_state["_cloud_cookie_restore_checked"] = True
        return

    remembered_auth = read_cloud_auth_cookie()
    if not remembered_auth:
        if not browser_storage_ready:
            return
        remembered_auth = browser_storage_auth or {}

    refresh_token = str(remembered_auth.get("refresh_token") or "").strip()
    if not refresh_token:
        st.session_state["_cloud_cookie_restore_checked"] = True
        return

    client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))
    if not client.is_configured:
        st.session_state["_cloud_cookie_restore_checked"] = True
        return

    st.session_state["_cloud_cookie_restore_checked"] = True
    refreshed = client.refresh_session(refresh_token)
    if not refreshed.get("ok"):
        clear_cloud_auth_cookie()
        st.session_state["_cloud_browser_storage_clear_requested"] = True
        return

    access_token = str(refreshed.get("access_token") or "")
    new_refresh_token = str(refreshed.get("refresh_token") or refresh_token)
    user_obj = refreshed.get("user") if isinstance(refreshed.get("user"), dict) else {}
    user_id = str(user_obj.get("id") or remembered_auth.get("user_id") or "")
    email = str(user_obj.get("email") or remembered_auth.get("email") or "")

    if not access_token or not user_id:
        clear_cloud_auth_cookie()
        st.session_state["_cloud_browser_storage_clear_requested"] = True
        return

    previous_owner = ""
    scope = st.session_state.get("app_scope", {})
    if isinstance(scope, dict):
        previous_owner = str(scope.get("owner_user_id") or "")
    if previous_owner and previous_owner != user_id:
        _clear_scoped_finance_state()

    _set_cloud_auth(True, email=email, user_id=user_id, access_token=access_token, refresh_token=new_refresh_token)
    _set_scope_owner(user_id, email)
    if isinstance(st.session_state.get("settings"), dict):
        st.session_state.settings["cloud_sync_enabled"] = True
    remember_cloud_auth(email, user_id, new_refresh_token)

    local_payload = export_app_state_payload()
    pull = client.fetch_user_data(user_id, access_token)
    remote_payload = pull.get("data") if isinstance(pull.get("data"), dict) else None

    if pull.get("ok") and remote_payload is not None:
        if should_keep_local_data_before_auto_import(local_payload, remote_payload):
            st.session_state["_cloud_last_snapshot"] = payload_snapshot(remote_payload)
            st.session_state["_cloud_last_pull_user"] = user_id
            pause_cloud_auto_sync(st.session_state, user_id, reason="local_cloud_conflict_after_cookie_restore")
            save_persistent_state()
            return

        import_app_state_payload(remote_payload)
        _set_scope_owner(user_id, email)
        _set_cloud_auth(True, email=email, user_id=user_id, access_token=access_token, refresh_token=new_refresh_token)
        _set_cloud_snapshot_now(user_id)
        mark_cloud_sync_ready(st.session_state, user_id)
        if isinstance(st.session_state.get("settings"), dict):
            st.session_state.settings["cloud_sync_enabled"] = True
            st.session_state.settings["cloud_last_sync_at"] = datetime.now().isoformat(timespec="seconds")
        save_persistent_state()
    elif pull.get("ok") and pull.get("data") is None:
        st.session_state["_cloud_last_snapshot"] = ""
        st.session_state["_cloud_last_pull_user"] = user_id
        pause_cloud_auto_sync(st.session_state, user_id, reason="cloud_empty_after_cookie_restore")
        save_persistent_state()
    else:
        _set_cloud_snapshot_now(user_id)
        pause_cloud_auto_sync(st.session_state, user_id, reason="pull_failed_after_cookie_restore")
        save_persistent_state()


def _sync_cloud_auth_cookie_preference() -> None:
    cloud_auth = st.session_state.get("cloud_auth", {})
    if not isinstance(cloud_auth, dict):
        return
    if not cloud_auth.get("logged_in") or not cloud_auth.get("refresh_token"):
        return
    if st.session_state.get("_cloud_remember_login") is False:
        return
    remember_cloud_auth(
        str(cloud_auth.get("email") or ""),
        str(cloud_auth.get("user_id") or ""),
        str(cloud_auth.get("refresh_token") or ""),
    )


def _sync_cloud_if_logged_in() -> None:
    cloud_auth = st.session_state.get("cloud_auth", {})
    if not isinstance(cloud_auth, dict):
        return

    settings = st.session_state.get("settings", {})
    if not isinstance(settings, dict):
        return

    if not bool(settings.get("cloud_sync_enabled", False)):
        return

    if not cloud_auth.get("logged_in"):
        return

    user_id = str(cloud_auth.get("user_id") or "")
    access_token = str(cloud_auth.get("access_token") or "")
    if not user_id or not access_token:
        return

    if not cloud_sync_ready_for_user(st.session_state, user_id):
        return

    app_scope = st.session_state.get("app_scope", {})
    owner_user_id = ""
    if isinstance(app_scope, dict):
        owner_user_id = str(app_scope.get("owner_user_id") or "")

    # Safety: never auto-push local data into a different signed-in user.
    if owner_user_id and owner_user_id != user_id:
        return

    client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))
    if not client.is_configured:
        return

    payload = export_app_state_payload()
    try:
        snapshot = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except Exception:
        return

    if (
        st.session_state.get("_cloud_last_snapshot") == snapshot
        and st.session_state.get("_cloud_last_pull_user") == user_id
    ):
        return

    push = client.upsert_user_data(user_id, access_token, payload)
    if push.get("ok"):
        st.session_state["_cloud_last_snapshot"] = snapshot
        st.session_state["_cloud_last_pull_user"] = user_id
        mark_cloud_sync_ready(st.session_state, user_id)
        if isinstance(settings, dict):
            settings["cloud_last_sync_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state["settings"] = settings


def _runtime_url_for_warning() -> str:
    try:
        context = getattr(st, "context", None)
    except Exception:
        context = None

    if context is None:
        return ""

    try:
        runtime_url = str(getattr(context, "url", "") or "")
    except Exception:
        runtime_url = ""

    if runtime_url:
        return runtime_url

    try:
        headers = getattr(context, "headers", {})
        runtime_host = str(headers.get("host", "") or "")
        if runtime_host:
            return f"https://{runtime_host}"
    except Exception:
        return ""
    return ""


def _show_hosted_data_warning(t) -> None:
    cloud_auth = st.session_state.get("cloud_auth", {})
    cloud_logged_in = bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token"))
    cloud_client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))
    warning_state = _hosted_data_warning_state(_runtime_url_for_warning(), cloud_client.is_configured, cloud_logged_in)

    if warning_state == "cloud_login_required":
        st.warning(
            t(
                "تنبيه مهم: هذه النسخة المستضافة لا تحفظ بياناتك محليًا بشكل مضمون. قبل إدخال أي بيانات مهمة، سجلي دخول السحابة من الإعدادات > السحابة.",
                "Important: this hosted beta does not keep local data reliably. Before entering important data, sign in to Cloud from Settings > Cloud.",
            )
        )
    elif warning_state == "cloud_setup_required":
        st.info(
            t(
                "هذه النسخة المستضافة لا تحفظ البيانات محليًا بشكل مضمون، وخدمة السحابة غير مفعلة بعد في بيئة التشغيل الحالية.",
                "This hosted beta does not keep local data reliably, and Cloud is not configured yet in the current deployment environment.",
            )
        )


def main():
    st.set_page_config(page_title="فلوسي | Floosy", layout="wide")

    # تهيئة عامة (session_state + css إن كانت داخل config_floosy)
    init_session_state()
    browser_storage_auth, browser_storage_ready = _sync_cloud_auth_browser_bridge()
    bootstrap_cloud_auth_from_storage()
    _restore_cloud_auth_from_cookie(browser_storage_auth, browser_storage_ready)
    _sync_cloud_auth_cookie_preference()

    # تحميل الصفحات بشكل آمن
    try:
        import pages_floosy.account_page as account_page
        import pages_floosy.assistant_page as assistant_page
        import pages_floosy.dashboard_page as dashboard_page
        import pages_floosy.mustndaty_page as mustndaty_page
        import pages_floosy.project_page as project_page
        import pages_floosy.savings_page as savings_page
        import pages_floosy.settings_page as settings_page
        import pages_floosy.tax_page as tax_page
    except Exception:
        st.error("في خطأ يمنع تشغيل التطبيق بسبب ImportError أو مشكلة في أحد الملفات.")
        st.code(traceback.format_exc())
        st.stop()

    lang = st.session_state.settings.get("language", "العربية")
    is_en = lang == "English"
    t = (lambda ar, en: en if is_en else ar)
    lang_code = "en" if is_en else "ar"
    lang_dir = "ltr" if is_en else "rtl"

    st.markdown(
        f"""
        <script>
        (function() {{
          const html = document.documentElement;
          const body = document.body;
          if (html) {{
            html.lang = "{lang_code}";
            html.dir = "{lang_dir}";
          }}
          if (body) {{
            body.setAttribute("data-floosy-language", "{lang_code}");
            body.setAttribute("dir", "{lang_dir}");
          }}
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title(t("فلوسي", "Floosy"))

    page_labels = {
        "home": t("الرئيسية", "Home"),
        "account": t("الحساب", "My Account"),
        "savings": t("التوفير", "Savings"),
        "assistant": t("المحلل المالي", "Financial Analyzer"),
        "documents": t("مستنداتي", "Documents"),
        "tax": t("الفواتير والضرائب", "Invoices & Tax"),
        "project": t("المشاريع", "Projects"),
        "settings": t("الإعدادات", "Settings"),
    }

    # --- حفظ الصفحة الحالية بالـ session_state (بدون query params) ---
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    legacy_map = {
        "الرئيسية": "home",
        "الحساب": "account",
        "التوفير": "savings",
        "المحلل المالي": "assistant",
        "المساعد الذكي": "assistant",
        "مستنداتي": "documents",
        "مشروع صغير": "project",
        "الإعدادات": "settings",
        "الالتزامات": "account",
        "Home": "home",
        "Account": "account",
        "My Account": "account",
        "Savings": "savings",
        "Financial Analyzer": "assistant",
        "Documents": "documents",
        "الفواتير والضرائب": "tax",
        "Invoices & Tax": "tax",
        "Projects": "project",
        "Settings": "settings",
    }
    st.session_state.current_page = legacy_map.get(st.session_state.current_page, st.session_state.current_page)

    requested_page = ""
    try:
        requested_page = str(st.query_params.get("page", "") or "").strip()
    except Exception:
        requested_page = ""
    requested_page = legacy_map.get(requested_page, requested_page)
    if requested_page in page_labels:
        st.session_state.current_page = requested_page

    if st.session_state.current_page not in page_labels:
        st.session_state.current_page = "home"

    page_keys = list(page_labels.keys())
    page_values = [page_labels[k] for k in page_keys]
    default_index = page_keys.index(st.session_state.current_page)
    sidebar_radio_key = "sidebar_section"

    if requested_page in page_labels:
        st.session_state[sidebar_radio_key] = page_labels[requested_page]
    elif st.session_state.get(sidebar_radio_key) not in page_values:
        st.session_state[sidebar_radio_key] = page_values[default_index]

    selected_label = st.sidebar.radio(
        t("القسم", "Section"),
        page_values,
        index=default_index,
        key=sidebar_radio_key,
    )
    selected_key = page_keys[page_values.index(selected_label)]

    # In app-shell / deep-link flows, the query param is the source of truth.
    # The hidden Streamlit sidebar radio can otherwise keep an older cached
    # selection and bounce mobile navigation back to the dashboard.
    if requested_page in page_labels and selected_key != requested_page:
        selected_key = requested_page
        st.session_state[sidebar_radio_key] = page_labels[requested_page]

    # تحديث الصفحة الحالية
    st.session_state.current_page = selected_key
    try:
        current_query_page = str(st.query_params.get("page", "") or "").strip()
    except Exception:
        current_query_page = ""
    if current_query_page != selected_key:
        try:
            st.query_params["page"] = selected_key
        except Exception:
            pass
    _show_hosted_data_warning(t)
    # اختيار الشهر/السنة (صفحات تحتاجها)
    month_key, month, year = get_month_selection(selected_key)

    # صفحات ما تحتاج شهر
    if selected_key == "settings":
        settings_page.render()
        save_persistent_state()
        _sync_cloud_if_logged_in()
        return

    if selected_key == "documents":
        mustndaty_page.render()
        save_persistent_state()
        _sync_cloud_if_logged_in()
        return

    # باقي الصفحات تحتاج month_key
    ensure_month_keys(month_key)

    if selected_key == "home":
        dashboard_page.render(month_key, month, year)
    elif selected_key == "account":
        account_page.render(month_key, month, year)
    elif selected_key == "savings":
        savings_page.render(month_key, month, year)
    elif selected_key == "assistant":
        assistant_page.render(month_key, month, year)
    elif selected_key == "tax":
        tax_page.render(month_key, month, year)
    elif selected_key == "project":
        project_page.render(month_key, month, year)

    save_persistent_state()
    _sync_cloud_if_logged_in()


# Streamlit runs top-to-bottom, so call main() directly.
main()
