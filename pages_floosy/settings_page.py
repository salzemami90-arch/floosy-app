import json
from datetime import datetime

import streamlit as st

from config_floosy import (
    CURRENCY_OPTIONS,
    PLAN_DEFINITIONS,
    export_app_state_payload,
    get_logo_bytes,
    get_plan_info,
    import_app_state_payload,
    reset_local_app_data,
    save_persistent_state,
    sync_browser_preferences_state,
)
from services.supabase_sync import SupabaseSyncClient


CURRENCY_OPTION_AR_TO_EN = {
    "د.ك - دينار كويتي": "KWD - Kuwaiti Dinar",
    "ر.س - ريال سعودي": "SAR - Saudi Riyal",
    "د.إ - درهم إماراتي": "AED - UAE Dirham",
    "$ - دولار أمريكي": "USD - US Dollar",
    "€ - يورو": "EUR - Euro",
}


def _currency_option_label(value: str, is_en: bool) -> str:
    clean_value = str(value or "").strip()
    if not is_en:
        return clean_value
    return CURRENCY_OPTION_AR_TO_EN.get(clean_value, clean_value)


def _set_cloud_auth(logged_in: bool, email: str = "", user_id: str = "", access_token: str = "", refresh_token: str = "") -> None:
    st.session_state["cloud_auth"] = {
        "logged_in": bool(logged_in),
        "email": email,
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def _sync_snapshot_from_state() -> None:
    try:
        st.session_state["_cloud_last_snapshot"] = json.dumps(
            export_app_state_payload(), ensure_ascii=False, sort_keys=True
        )
    except Exception:
        st.session_state["_cloud_last_snapshot"] = ""


def _mark_cloud_sync_now() -> None:
    settings = st.session_state.get("settings")
    if not isinstance(settings, dict):
        return
    settings["cloud_last_sync_at"] = datetime.now().isoformat(timespec="seconds")
    st.session_state["settings"] = settings


def _build_backup_file() -> tuple[str, bytes]:
    backup_payload = export_app_state_payload()
    backup_now = datetime.now()
    backup_payload["_meta"] = {
        "saved_at": backup_now.isoformat(timespec="seconds"),
        "source": "floosy_settings_backup",
        "version": 1,
    }
    timestamp_for_file = backup_now.strftime("%Y%m%d_%H%M%S")
    backup_name = f"floosy_backup_{timestamp_for_file}.json"
    backup_bytes = json.dumps(backup_payload, ensure_ascii=False, indent=2).encode("utf-8")
    return backup_name, backup_bytes


def _get_app_scope() -> dict:
    scope = st.session_state.get("app_scope")
    if not isinstance(scope, dict):
        scope = {}
    scope.setdefault("owner_user_id", "")
    scope.setdefault("owner_email", "")
    st.session_state["app_scope"] = scope
    return scope


def _set_scope_owner(user_id: str = "", email: str = "") -> None:
    scope = _get_app_scope()
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


def _render_cloud_sql_setup(t):
    with st.expander(t("إعداد جدول البيانات (مرة واحدة)", "Data Table Setup (one-time)"), expanded=False):
        st.code(
            """
create table if not exists public.user_app_data (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.user_app_data enable row level security;

drop policy if exists "Users can select own data" on public.user_app_data;

create policy "Users can select own data"
on public.user_app_data for select
using (auth.uid() = user_id);

drop policy if exists "Users can insert own data" on public.user_app_data;

create policy "Users can insert own data"
on public.user_app_data for insert
with check (auth.uid() = user_id);

drop policy if exists "Users can update own data" on public.user_app_data;

create policy "Users can update own data"
on public.user_app_data for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own data" on public.user_app_data;

create policy "Users can delete own data"
on public.user_app_data for delete
using (auth.uid() = user_id);
            """.strip(),
            language="sql",
        )


def render():
    settings = st.session_state.settings
    is_en = settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)

    st.title(t("إعدادات فلوسي", "Floosy Settings"))
    st.caption(
        t(
            "كل الإعدادات هنا مرتبة: عام، خصوصية، وسحابة.",
            "All settings are organized here: General, Privacy, and Cloud.",
        )
    )

    cloud_sync_enabled = bool(settings.get("cloud_sync_enabled", False))
    last_sync_raw = str(settings.get("cloud_last_sync_at", "") or "").strip()
    if last_sync_raw:
        try:
            parsed_sync = datetime.fromisoformat(last_sync_raw.replace("Z", ""))
            last_sync_label = parsed_sync.strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_sync_label = last_sync_raw
    else:
        last_sync_label = t("غير متوفر", "Not available")

    backup_name_top, backup_bytes_top = _build_backup_file()

    st.markdown("---")
    status_value = t("مفعلة", "Enabled") if cloud_sync_enabled else t("غير مفعلة", "Disabled")
    if cloud_sync_enabled:
        status_bg = "#ecfdf5"
        status_border = "#10b981"
        status_text = "#065f46"
        status_hint = t("المزامنة السحابية تعمل بشكل طبيعي.", "Cloud sync is active and working.")
    else:
        status_bg = "#fffbeb"
        status_border = "#f59e0b"
        status_text = "#92400e"
        status_hint = t("السحابة متوقفة حاليًا. يمكنك تفعيلها أو تصدير بياناتك.", "Cloud is currently off. You can enable it or export your data.")

    st.markdown(
        f"""
        <div style="
            background:{status_bg};
            border:1px solid {status_border};
            border-right:6px solid {status_border};
            border-radius:12px;
            padding:10px 12px;
            margin:6px 0 10px 0;
            color:{status_text};
        ">
            <div style="font-weight:800;">{t("شريط حالة السحابة", "Cloud Status Bar")}: {status_value}</div>
            <div style="font-size:0.9rem; margin-top:4px;">{status_hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2 = st.columns(2)
    with s1:
        st.metric(
            t("حالة السحابة", "Cloud Status"),
            status_value,
        )
    with s2:
        st.metric(t("آخر مزامنة", "Last Sync"), last_sync_label)

    if not cloud_sync_enabled:
        st.warning(
            t(
                "السحابة غير مفعلة حاليًا. يمكنك تفعيلها أو تصدير بياناتك الآن.",
                "Cloud is currently disabled. You can enable it or export your data now.",
            )
        )
        a1, a2 = st.columns(2)
        with a1:
            if st.button(t("فعّل السحابة", "Enable Cloud"), key="settings_status_enable_cloud_btn", use_container_width=True):
                settings["cloud_sync_enabled"] = True
                st.session_state.settings = settings
                st.rerun()
        with a2:
            st.download_button(
                label=t("تصدير بياناتي", "Export My Data"),
                data=backup_bytes_top,
                file_name=backup_name_top,
                mime="application/json",
                use_container_width=True,
                key="settings_status_backup_download_btn",
            )

    st.markdown(
        """
        <style>
        div[data-testid="stTabs"] button[role="tab"] {
            font-weight: 700;
            border-radius: 10px;
            padding: 8px 14px;
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: rgba(18,149,107,0.12);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_general, tab_privacy, tab_cloud = st.tabs(
        [
            t("عام", "General"),
            t("الخصوصية", "Privacy"),
            t("السحابة", "Cloud"),
        ]
    )

    with tab_general:
        st.subheader(t("الملف العام", "General Profile"))
        col1, col2 = st.columns(2)

        with col1:
            settings["name"] = st.text_input(
                t("اسم المستخدم / المنشأة", "User / Business Name"),
                value=settings.get("name", ""),
            )
            settings["default_currency"] = st.selectbox(
                t("العملة الافتراضية", "Default Currency"),
                CURRENCY_OPTIONS,
                index=CURRENCY_OPTIONS.index(settings.get("default_currency", CURRENCY_OPTIONS[0]))
                if settings.get("default_currency", CURRENCY_OPTIONS[0]) in CURRENCY_OPTIONS
                else 0,
                format_func=lambda opt: _currency_option_label(opt, is_en),
            )

        with col2:
            current_language = settings.get("language", "العربية")
            selected_language = st.selectbox(
                t("اللغة", "Language"),
                ["العربية", "English"],
                index=0 if current_language == "العربية" else 1,
            )
            if selected_language != current_language:
                settings["language"] = selected_language
                settings["language_user_selected"] = True
                st.session_state.settings = settings
                sync_browser_preferences_state(
                    language=selected_language,
                    name=str(settings.get("name", "") or "").strip(),
                    welcome_done=True,
                )
                st.rerun()
            settings["language"] = selected_language
            uploaded_file = st.file_uploader(
                t("رفع شعار التطبيق", "Upload App Logo"),
                type=["png", "jpg", "jpeg"],
            )
            if uploaded_file is not None:
                settings["profile_image"] = uploaded_file.getvalue()

        st.session_state.settings = settings

        st.markdown("---")
        st.subheader(t("إظهار بطاقات الداشبورد", "Dashboard Card Visibility"))

        c1, c2, c3 = st.columns(3)
        with c1:
            settings["show_status_account"] = st.checkbox(
                t("بطاقة الحساب", "Account Card"),
                value=bool(settings.get("show_status_account", True)),
            )
        with c2:
            settings["show_status_saving"] = st.checkbox(
                t("بطاقة التوفير", "Savings Card"),
                value=bool(settings.get("show_status_saving", True)),
            )
        with c3:
            settings["show_status_project"] = st.checkbox(
                t("بطاقة المشاريع", "Projects Card"),
                value=bool(settings.get("show_status_project", True)),
            )

        st.session_state.settings = settings

        st.markdown("---")
        st.subheader(t("معاينة", "Preview"))
        col_a, col_b = st.columns([1, 2])
        with col_a:
            img = get_logo_bytes()
            if img:
                st.image(img, width=120)
            else:
                st.write(t("لا يوجد شعار مرفوع.", "No uploaded logo."))
        with col_b:
            st.write(f"{t('الاسم', 'Name')}: {settings.get('name', '') or '-'}")
            currency_label = _currency_option_label(settings.get("default_currency", CURRENCY_OPTIONS[0]), is_en)
            st.write(f"{t('العملة', 'Currency')}: {currency_label}")
            st.write(f"{t('اللغة', 'Language')}: {settings.get('language', 'العربية')}")

        st.caption(
            t(
                "إدارة الالتزامات والمدخول الشهري داخل صفحة الحساب من زر الإعدادات.",
                "Monthly items are managed inside the Account page from the settings button.",
            )
        )

        plan_info = get_plan_info()
        tier_key = str(plan_info.get("tier", "beta_free")).strip().lower()
        if tier_key not in PLAN_DEFINITIONS:
            tier_key = "beta_free"
        tier_meta = PLAN_DEFINITIONS[tier_key]
        tier_label = tier_meta["label_en"] if is_en else tier_meta["label_ar"]
        total_features = len(tier_meta.get("features", {}))
        enabled_count = sum(1 for enabled in tier_meta.get("features", {}).values() if enabled)

        st.markdown("---")
        st.subheader(t("خطة الاستخدام الحالية", "Current Plan"))
        st.info(
            t(
                f"الخطة الحالية: {tier_label} (بدون دفع حالياً).",
                f"Current plan: {tier_label} (no billing yet).",
            )
        )
        st.caption(
            t(
                f"ميزات مفعلة الآن: {enabled_count} / {total_features}. سنفعل الاشتراكات لاحقاً بعد مرحلة التجربة.",
                f"Enabled features now: {enabled_count} / {total_features}. Billing will be enabled later after beta.",
            )
        )

        st.markdown("---")
        st.info(
            t(
                "إعدادات الضريبة انتقلت إلى صفحة الفواتير والضرائب من زر الإعدادات هناك.",
                "Tax settings were moved to the Invoices and Tax page using the settings button there.",
            )
        )

    with tab_privacy:
        st.subheader(t("الخصوصية والمزامنة", "Privacy and Sync"))

        cloud_sync_enabled = st.checkbox(
            t("تفعيل المزامنة السحابية (اختياري)", "Enable Cloud Sync (Optional)"),
            value=bool(settings.get("cloud_sync_enabled", False)),
            help=t(
                "إذا كانت مغلقة، تبقى بياناتك محلية على هذا الجهاز فقط.",
                "When off, your data stays local on this device only.",
            ),
            key="settings_cloud_sync_enabled",
        )

        if cloud_sync_enabled != bool(settings.get("cloud_sync_enabled", False)):
            settings["cloud_sync_enabled"] = cloud_sync_enabled
            st.session_state.settings = settings
            if not cloud_sync_enabled:
                st.session_state["_cloud_last_snapshot"] = ""
            st.rerun()

        st.markdown("---")
        st.subheader(t("بيانات هذا الجهاز", "This Device Data"))
        st.caption(
            t(
                "هذا الخيار يمسح البيانات المحلية من هذا الجهاز فقط.",
                "This option deletes local data from this device only.",
            )
        )

        local_delete_confirm = st.checkbox(
            t("تأكيد حذف بيانات هذا الجهاز", "Confirm Delete Device Data"),
            key="local_delete_confirm",
        )

        if st.button(
            t("حذف بيانات هذا الجهاز", "Delete This Device Data"),
            use_container_width=True,
            key="local_delete_btn",
            disabled=not local_delete_confirm,
        ):
            reset_local_app_data()
            st.success(t("تم حذف بيانات هذا الجهاز.", "This device data was deleted."))
            st.info(
                t(
                    "لاستعادة البيانات من السحابة، يرجى تفعيل المزامنة ثم تسجيل الدخول واختيار تحميل بياناتي.",
                    "To restore data from the cloud, enable sync, sign in, then select Load My Data.",
                )
            )
            st.rerun()

        st.markdown("---")
        st.subheader(t("تصدير واسترجاع البيانات", "Export and Restore Data"))
        st.caption(
            t(
                "يمكنك تصدير ملف JSON من بياناتك واستعادته لاحقًا على هذا الجهاز أو جهاز آخر.",
                "You can export a JSON data file and restore it later on this device or another one.",
            )
        )
        backup_name, backup_bytes = _build_backup_file()

        st.download_button(
            label=t("تصدير بياناتي", "Export My Data"),
            data=backup_bytes,
            file_name=backup_name,
            mime="application/json",
            use_container_width=True,
            key="settings_backup_download_btn",
        )
        st.caption(
            t(
                "مكان الحفظ يعتمد على إعدادات المتصفح (غالباً مجلد Downloads).",
                "Save location depends on your browser settings (usually Downloads).",
            )
        )

        restore_file = st.file_uploader(
            t("اختيار ملف بيانات JSON", "Choose JSON Data File"),
            type=["json"],
            key="settings_restore_file",
            help=t(
                "تنبيه: الاسترجاع يستبدل البيانات الحالية على هذا الجهاز.",
                "Warning: restore replaces current data on this device.",
            ),
        )

        restore_confirm = st.checkbox(
            t("أفهم أن الاسترجاع يستبدل البيانات الحالية", "I understand restore replaces current data"),
            key="settings_restore_confirm",
        )

        if st.button(
            t("استرجاع النسخة الآن", "Restore Backup Now"),
            use_container_width=True,
            key="settings_restore_btn",
            disabled=(restore_file is None or not restore_confirm),
        ):
            raw_bytes = restore_file.getvalue() if restore_file is not None else b""
            try:
                loaded = json.loads(raw_bytes.decode("utf-8-sig"))
            except Exception:
                st.error(t("الملف غير صالح JSON.", "Invalid JSON file."))
            else:
                if not isinstance(loaded, dict):
                    st.error(t("محتوى النسخة غير صالح.", "Backup content is invalid."))
                else:
                    import_app_state_payload(loaded)
                    save_persistent_state()
                    _sync_snapshot_from_state()
                    st.success(t("تم استرجاع النسخة بنجاح.", "Backup restored successfully."))
                    st.rerun()

    with tab_cloud:
        st.subheader(t("حساب السحابة (Supabase)", "Cloud Account (Supabase)"))

        cloud_sync_enabled = bool(st.session_state.settings.get("cloud_sync_enabled", False))
        cloud_auth = st.session_state.get("cloud_auth", {})

        if not cloud_sync_enabled:
            st.info(
                t(
                    "المزامنة السحابية غير مفعلة. يرجى تفعيلها أولًا من تبويب الخصوصية.",
                    "Cloud sync is disabled. Please enable it first from the Privacy tab.",
                )
            )
            if bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token")):
                if st.button(t("تسجيل خروج من السحابة", "Sign Out from Cloud"), key="cloud_signout_disabled_btn"):
                    _set_cloud_auth(False)
                    st.session_state["_cloud_last_pull_user"] = ""
                    st.success(t("تم تسجيل الخروج.", "Signed out."))
                    st.rerun()
            return

        client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))

        if not client.is_configured:
            st.info(
                t(
                    "للتفعيل، يرجى إضافة SUPABASE_URL و SUPABASE_ANON_KEY في secrets أو متغيرات البيئة.",
                    "To enable cloud sync, add SUPABASE_URL and SUPABASE_ANON_KEY in secrets or environment variables.",
                )
            )
            _render_cloud_sql_setup(t)
            return

        logged_in = bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token"))

        if logged_in:
            st.success(
                t(
                    f"مسجل دخول: {cloud_auth.get('email', '')}",
                    f"Signed in: {cloud_auth.get('email', '')}",
                )
            )

            r1c1, r1c2 = st.columns(2)
            with r1c1:
                if st.button(t("تحميل بياناتي", "Load My Data"), use_container_width=True, key="cloud_load_btn"):
                    pull = client.fetch_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""))
                    if not pull.get("ok"):
                        st.error(t(f"تعذر تحميل البيانات: {pull.get('error', '')}", f"Load failed: {pull.get('error', '')}"))
                    elif pull.get("data") is None:
                        _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                        _mark_cloud_sync_now()
                        st.info(t("لا توجد بيانات محفوظة في السحابة حتى الآن.", "No cloud data found yet."))
                    else:
                        import_app_state_payload(pull.get("data"))
                        _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                        st.session_state["_cloud_last_pull_user"] = cloud_auth.get("user_id", "")
                        _mark_cloud_sync_now()
                        _sync_snapshot_from_state()
                        save_persistent_state()
                        st.success(t("تم تحميل بياناتك من السحابة.", "Your data was loaded from cloud."))
                        st.rerun()

            with r1c2:
                if st.button(t("حفظ بياناتي", "Save My Data"), use_container_width=True, key="cloud_save_btn"):
                    payload = export_app_state_payload()
                    push = client.upsert_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""), payload)
                    if push.get("ok"):
                        _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                        _mark_cloud_sync_now()
                        _sync_snapshot_from_state()
                        save_persistent_state()
                        st.success(t("تم حفظ بياناتك في السحابة.", "Your data was saved to cloud."))
                    else:
                        st.error(t(f"تعذر الحفظ: {push.get('error', '')}", f"Save failed: {push.get('error', '')}"))

            r2c1, r2c2 = st.columns(2)
            with r2c1:
                if st.button(t("تسجيل خروج", "Sign Out"), use_container_width=True, key="cloud_signout_btn"):
                    _set_cloud_auth(False)
                    st.session_state["_cloud_last_pull_user"] = ""
                    st.success(t("تم تسجيل الخروج.", "Signed out."))
                    st.rerun()

            with r2c2:
                delete_confirm = st.checkbox(
                    t("تأكيد حذف البيانات", "Confirm Delete"),
                    key="cloud_delete_confirm",
                )
                if st.button(
                    t("حذف بياناتي السحابية", "Delete My Cloud Data"),
                    use_container_width=True,
                    key="cloud_delete_btn",
                    disabled=not delete_confirm,
                ):
                    delete_res = client.delete_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""))
                    if delete_res.get("ok"):
                        st.session_state["_cloud_last_pull_user"] = cloud_auth.get("user_id", "")
                        _sync_snapshot_from_state()
                        st.success(t("تم حذف بياناتك السحابية بالكامل.", "Your cloud data was deleted."))
                        st.info(
                            t(
                                "لن يتم رفع البيانات تلقائيًا بعد الحذف. إذا رغبت في إنشاء نسخة سحابية جديدة، استخدم زر حفظ بياناتي.",
                                "Auto upload is paused after deletion. If you want to create a new cloud copy, use Save My Data.",
                            )
                        )
                        st.rerun()
                    else:
                        st.error(t(f'تعذر حذف البيانات: {delete_res.get("error", "")}', f'Delete failed: {delete_res.get("error", "")}'))

            st.caption(
                t(
                    "الحذف يشمل بيانات السحابة فقط. البيانات المحلية على هذا الجهاز لن تُحذف.",
                    "This deletes cloud data only. Local data on this device is not deleted.",
                )
            )

            with st.expander(t("منطقة حساسة", "Danger Zone"), expanded=False):
                st.warning(
                    t(
                        "حذف الحساب بالكامل نهائي ويشمل حساب السحابة وبياناته.",
                        "Permanent account deletion removes your cloud account and cloud data.",
                    )
                )

                delete_account_confirm = st.checkbox(
                    t("أفهم أن حذف الحساب نهائي", "I understand account deletion is permanent"),
                    key="cloud_delete_account_confirm",
                )

                if st.button(
                    t("حذف الحساب بالكامل", "Delete Account Permanently"),
                    use_container_width=True,
                    key="cloud_delete_account_btn",
                    disabled=not delete_account_confirm,
                ):
                    data_delete_res = client.delete_user_data(
                        cloud_auth.get("user_id", ""),
                        cloud_auth.get("access_token", ""),
                    )
                    account_delete_res = client.delete_current_user(cloud_auth.get("access_token", ""))

                    if account_delete_res.get("ok"):
                        _set_cloud_auth(False)
                        _set_scope_owner("", "")
                        st.session_state["_cloud_last_snapshot"] = ""
                        st.session_state["_cloud_last_pull_user"] = ""
                        st.success(
                            t(
                                "تم حذف الحساب السحابي بالكامل.",
                                "Cloud account deleted permanently.",
                            )
                        )
                        st.rerun()

                    account_error = str(account_delete_res.get("error", ""))
                    data_error = str(data_delete_res.get("error", ""))
                    if data_delete_res.get("ok"):
                        st.warning(
                            t(
                                f"تم حذف البيانات السحابية لكن حذف الحساب فشل: {account_error}",
                                f"Cloud data deleted, but account deletion failed: {account_error}",
                            )
                        )
                    else:
                        st.error(
                            t(
                                f"تعذر حذف الحساب: {account_error} | وتعذر حذف البيانات: {data_error}",
                                f"Account deletion failed: {account_error} | Data deletion failed: {data_error}",
                            )
                        )

        else:
            with st.form("cloud_auth_form", clear_on_submit=False):
                mode = st.selectbox(
                    t("العملية", "Action"),
                    [t("تسجيل دخول", "Sign In"), t("إنشاء حساب", "Sign Up")],
                )
                email = st.text_input(t("الإيميل", "Email"))
                password = st.text_input(t("كلمة المرور", "Password"), type="password")
                submit = st.form_submit_button(t("متابعة", "Continue"), use_container_width=True)

            if submit:
                clean_email = email.strip().lower()
                if not clean_email or not password:
                    st.warning(t("يرجى إدخال البريد الإلكتروني وكلمة المرور.", "Please enter email and password."))
                else:
                    if mode == t("إنشاء حساب", "Sign Up"):
                        auth_res = client.sign_up(clean_email, password)
                    else:
                        auth_res = client.sign_in(clean_email, password)

                    if not auth_res.get("ok"):
                        st.error(t(f"فشل العملية: {auth_res.get('error', '')}", f"Action failed: {auth_res.get('error', '')}"))
                    else:
                        access_token = str(auth_res.get("access_token") or "")
                        refresh_token = str(auth_res.get("refresh_token") or "")
                        user_obj = auth_res.get("user") if isinstance(auth_res.get("user"), dict) else {}

                        if not access_token:
                            st.info(
                                t(
                                    "تم إنشاء الحساب. إذا كان التحقق عبر البريد الإلكتروني مفعّلًا، يرجى مراجعة بريدك الإلكتروني ثم تسجيل الدخول.",
                                    "Account created. If email confirmation is enabled, please check your inbox and then sign in.",
                                )
                            )
                        else:
                            user_id = str(user_obj.get("id") or "")
                            if not user_id:
                                user_res = client.get_user(access_token)
                                if user_res.get("ok") and isinstance(user_res.get("user"), dict):
                                    user_id = str(user_res["user"].get("id") or "")

                            if not user_id:
                                st.error(t("تعذر تحديد معرف المستخدم من Supabase.", "Could not determine user id from Supabase."))
                            else:
                                scope = _get_app_scope()
                                previous_owner = str(scope.get("owner_user_id") or "")
                                if previous_owner and previous_owner != user_id:
                                    _clear_scoped_finance_state()
                                    st.info(
                                        t(
                                            "تم تبديل الحساب. تم فتح مساحة بيانات محلية مستقلة لهذا المستخدم.",
                                            "Account switched. A separate local data scope has been opened for this user.",
                                        )
                                    )

                                _set_cloud_auth(
                                    True,
                                    email=clean_email,
                                    user_id=user_id,
                                    access_token=access_token,
                                    refresh_token=refresh_token,
                                )
                                _set_scope_owner(user_id, clean_email)

                                pull = client.fetch_user_data(user_id, access_token)
                                if pull.get("ok") and pull.get("data") is not None:
                                    import_app_state_payload(pull.get("data"))
                                    _set_scope_owner(user_id, clean_email)
                                    st.session_state["_cloud_last_pull_user"] = user_id
                                    _mark_cloud_sync_now()
                                    _sync_snapshot_from_state()
                                    save_persistent_state()
                                    st.success(t("تم تسجيل الدخول وتحميل بياناتك.", "Signed in and data loaded."))
                                elif pull.get("ok") and pull.get("data") is None:
                                    _set_scope_owner(user_id, clean_email)
                                    st.session_state["_cloud_last_pull_user"] = user_id
                                    _mark_cloud_sync_now()
                                    _sync_snapshot_from_state()
                                    save_persistent_state()
                                    st.info(t("تم تسجيل الدخول. لا توجد بيانات محفوظة في السحابة حاليًا.", "Signed in. No cloud data exists yet."))
                                    st.caption(t("إذا رغبت في إنشاء نسخة سحابية جديدة، استخدم زر حفظ بياناتي.", "If you want to create a new cloud copy, use Save My Data."))
                                else:
                                    st.warning(t("تم تسجيل الدخول، لكن تعذر تحميل البيانات السحابية الآن.", "Signed in, but failed to load cloud data now."))

                                st.rerun()
