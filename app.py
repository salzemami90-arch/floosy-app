import json
import traceback
from datetime import datetime

import streamlit as st

from config_floosy import (
    ensure_month_keys,
    export_app_state_payload,
    get_month_selection,
    init_session_state,
    save_persistent_state,
    sync_browser_preferences_state,
)
from services.supabase_sync import SupabaseSyncClient


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
        if isinstance(settings, dict):
            settings["cloud_last_sync_at"] = datetime.now().isoformat(timespec="seconds")
            st.session_state["settings"] = settings


def _render_beta_notice() -> None:
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #fff7ed, #fffbeb);
            border: 1px solid #f59e0b;
            border-right: 6px solid #f59e0b;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 8px 0 14px 0;
            color: #78350f;
            line-height: 1.75;
        ">
            <div style="font-weight: 800; margin-bottom: 6px;">
                تنبيه تجريبي | Beta Notice
            </div>
            <div>
                هذا التطبيق ما زال في مرحلة تجريبية. إذا كانت البيانات مهمة، فيرجى تفعيل المزامنة السحابية أو تصدير نسخة احتياطية بشكل منتظم خلال مرحلة التجربة.
            </div>
            <div style="margin-top: 4px;">
                This app is currently in beta. If your data matters, enable cloud sync or export a backup regularly during beta.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _should_show_welcome_gate() -> bool:
    settings = st.session_state.get("settings", {})
    if not isinstance(settings, dict):
        return True
    if bool(st.session_state.get("_welcome_completed", False)):
        return False
    if bool(settings.get("language_user_selected", False)):
        st.session_state["_welcome_completed"] = True
        return False
    return True


def _render_welcome_gate() -> None:
    settings = st.session_state.get("settings", {})
    if not isinstance(settings, dict):
        settings = {}

    current_language = settings.get("language", "العربية")

    st.markdown(
        """
        <style>
        .floosy-welcome-card {
            margin-top: 8vh;
            background: #ffffff !important;
            border-radius: 18px !important;
            border: 1px solid #dbe3ea !important;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22) !important;
            padding: 18px 16px 14px 16px;
        }

        .floosy-welcome-title {
            font-size: 1.25rem;
            font-weight: 800;
            margin-bottom: 6px;
            color: #0f172a;
        }

        .floosy-welcome-copy {
            color: #475569;
            line-height: 1.7;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 4vh;'></div>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        st.markdown('<div class="floosy-welcome-card">', unsafe_allow_html=True)
        with st.form("welcome_gate_form", clear_on_submit=False):
            st.markdown('<div class="floosy-welcome-title">مرحبًا بك في فلوسي | Welcome to Floosy</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="floosy-welcome-copy">يرجى اختيار اللغة للبدء. الاسم اختياري، ويمكن تعديلهما لاحقًا من الإعدادات.<br/>Choose your language to get started. Name is optional, and you can change both later from Settings.</div>',
                unsafe_allow_html=True,
            )
            welcome_name = st.text_input(
                "اسمك (اختياري) | Your name (optional)",
                value=str(settings.get("name", "") or ""),
            )
            welcome_language = st.selectbox(
                "اللغة | Language",
                ["العربية", "English"],
                index=0 if current_language == "العربية" else 1,
            )
            submitted = st.form_submit_button("ابدأ | Start", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        settings["language"] = welcome_language
        settings["language_user_selected"] = True
        settings["name"] = welcome_name.strip()
        st.session_state["settings"] = settings
        st.session_state["_welcome_completed"] = True
        sync_browser_preferences_state(
            language=welcome_language,
            name=welcome_name.strip(),
            welcome_done=True,
        )
        st.rerun()


def main():
    st.set_page_config(page_title="فلوسي | Floosy", layout="wide")

    # تهيئة عامة (session_state + css إن كانت داخل config_floosy)
    init_session_state()

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

    if _should_show_welcome_gate():
        _render_welcome_gate()
        st.stop()

    lang = st.session_state.settings.get("language", "العربية")
    is_en = lang == "English"
    t = (lambda ar, en: en if is_en else ar)

    st.sidebar.title(t("فلوسي", "Floosy"))

    page_labels = {
        "home": t("الرئيسية", "Home"),
        "account": t("الحساب", "Account"),
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
        "Savings": "savings",
        "Financial Analyzer": "assistant",
        "Documents": "documents",
        "الفواتير والضرائب": "tax",
        "Invoices & Tax": "tax",
        "Projects": "project",
        "Settings": "settings",
    }
    st.session_state.current_page = legacy_map.get(st.session_state.current_page, st.session_state.current_page)
    if st.session_state.current_page not in page_labels:
        st.session_state.current_page = "home"

    page_keys = list(page_labels.keys())
    page_values = [page_labels[k] for k in page_keys]
    default_index = page_keys.index(st.session_state.current_page)
    selected_label = st.sidebar.radio(t("القسم", "Section"), page_values, index=default_index)
    selected_key = page_keys[page_values.index(selected_label)]

    # تحديث الصفحة الحالية
    st.session_state.current_page = selected_key
    _render_beta_notice()

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
