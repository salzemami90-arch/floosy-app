import json
from datetime import datetime, timedelta, timezone

import streamlit as st

from config_floosy import (
    CURRENCY_OPTIONS,
    PLAN_DEFINITIONS,
    _local_persistence_enabled,
    export_app_state_payload,
    get_builtin_logo_b64,
    get_plan_info,
    import_app_state_payload,
    reset_local_app_data,
    save_persistent_state,
    sync_browser_preferences_state,
)
from services.cloud_auth_cookie import clear_cloud_auth_cookie, remember_cloud_auth
from services.i18n import LANGUAGE_NAMES, LANGUAGES, make_t, is_rtl as _is_rtl
from services.cloud_sync_guard import (
    clear_cloud_sync_guard,
    cloud_sync_pause_reason,
    mark_cloud_sync_ready,
    payload_has_meaningful_data,
    payload_snapshot,
    pause_cloud_auto_sync,
    should_keep_local_data_before_auto_import,
)
from services.supabase_sync import SupabaseSyncClient


KUWAIT_TZ = timezone(timedelta(hours=3), name="Asia/Kuwait")


CURRENCY_OPTION_LABELS: dict[str, dict[str, str]] = {
    "د.ك - دينار كويتي": {"en": "KWD - Kuwaiti Dinar", "zh": "KWD - 科威特第纳尔", "ko": "KWD - 쿠웨이트 디나르", "ja": "KWD - クウェートディナール", "id": "KWD - Dinar Kuwait", "ms": "KWD - Dinar Kuwait"},
    "ر.س - ريال سعودي": {"en": "SAR - Saudi Riyal", "zh": "SAR - 沙特里亚尔", "ko": "SAR - 사우디 리얄", "ja": "SAR - サウジリヤル", "id": "SAR - Riyal Saudi", "ms": "SAR - Riyal Saudi"},
    "د.إ - درهم إماراتي": {"en": "AED - UAE Dirham", "zh": "AED - 阿联酋迪拉姆", "ko": "AED - UAE 디르함", "ja": "AED - UAEディルハム", "id": "AED - Dirham UEA", "ms": "AED - Dirham UEA"},
    "$ - دولار أمريكي": {"en": "USD - US Dollar", "zh": "USD - 美元", "ko": "USD - 미국 달러", "ja": "USD - 米ドル", "id": "USD - Dolar AS", "ms": "USD - Dolar AS"},
    "€ - يورو": {"en": "EUR - Euro", "zh": "EUR - 欧元", "ko": "EUR - 유로", "ja": "EUR - ユーロ", "id": "EUR - Euro", "ms": "EUR - Euro"},
    "¥ - 人民币": {"en": "CNY - Chinese Yuan", "zh": "CNY - 人民币", "ko": "CNY - 중국 위안", "ja": "CNY - 中国人民元", "id": "CNY - Yuan Tiongkok", "ms": "CNY - Yuan Tiongkok"},
    "₩ - 원": {"en": "KRW - Korean Won", "zh": "KRW - 韩元", "ko": "KRW - 대한민국 원", "ja": "KRW - 韓国ウォン", "id": "KRW - Won Korea", "ms": "KRW - Won Korea"},
    "¥ - 円": {"en": "JPY - Japanese Yen", "zh": "JPY - 日元", "ko": "JPY - 일본 엔", "ja": "JPY - 日本円", "id": "JPY - Yen Jepang", "ms": "JPY - Yen Jepang"},
    "Rp - Rupiah": {"en": "IDR - Indonesian Rupiah", "zh": "IDR - 印尼盾", "ko": "IDR - 인도네시아 루피아", "ja": "IDR - インドネシアルピア", "id": "IDR - Rupiah Indonesia", "ms": "IDR - Rupiah Indonesia"},
    "S$ - SGD": {"en": "SGD - Singapore Dollar", "zh": "SGD - 新加坡元", "ko": "SGD - 싱가포르 달러", "ja": "SGD - シンガポールドル", "id": "SGD - Dolar Singapura", "ms": "SGD - Dolar Singapura"},
}


def _currency_option_label(value: str, lang_code: str) -> str:
    clean_value = str(value or "").strip()
    if lang_code == "ar":
        return clean_value
    labels = CURRENCY_OPTION_LABELS.get(clean_value)
    if labels:
        return labels.get(lang_code, labels.get("en", clean_value))
    return clean_value


def _cloud_error_text(error, t) -> str:
    raw = str(error or "").strip()
    raw_lower = raw.lower()
    if (
        "temporarily unavailable or still setting up" in raw_lower
        or "web server is down" in raw_lower
        or "cloudflare" in raw_lower
        or "error code 521" in raw_lower
    ):
        return t(
            "السحابة غير متاحة مؤقتًا أو لا تزال قيد التجهيز. يرجى الانتظار دقائق ثم المحاولة مرة ثانية.",
            "Cloud is temporarily unavailable or still setting up. Wait a few minutes, then try again.",
        )
    return raw[:500]


from services.cloud_state_helpers import (
    clear_scoped_finance_state as _clear_scoped_finance_state,
    set_cloud_auth as _set_cloud_auth,
    set_scope_owner as _set_scope_owner,
)


def _refresh_cloud_auth_for_manual_action(client: SupabaseSyncClient) -> tuple[dict, str]:
    cloud_auth = st.session_state.get("cloud_auth", {})
    if not isinstance(cloud_auth, dict):
        return {}, "missing_cloud_auth"

    refresh_token = str(cloud_auth.get("refresh_token") or "").strip()
    if not refresh_token:
        return cloud_auth, ""

    refreshed = client.refresh_session(refresh_token)
    if not refreshed.get("ok"):
        st.session_state["_cloud_sync_last_error"] = "token_refresh_failed"
        pause_cloud_auto_sync(
            st.session_state,
            str(cloud_auth.get("user_id") or ""),
            reason="token_refresh_failed",
        )
        return cloud_auth, str(refreshed.get("error") or "token_refresh_failed")

    user_obj = refreshed.get("user") if isinstance(refreshed.get("user"), dict) else {}
    email = str(user_obj.get("email") or cloud_auth.get("email") or "")
    user_id = str(user_obj.get("id") or cloud_auth.get("user_id") or "")
    access_token = str(refreshed.get("access_token") or cloud_auth.get("access_token") or "")
    new_refresh_token = str(refreshed.get("refresh_token") or refresh_token)

    if not user_id or not access_token:
        return cloud_auth, "token_refresh_missing_auth"

    _set_cloud_auth(
        True,
        email=email,
        user_id=user_id,
        access_token=access_token,
        refresh_token=new_refresh_token,
    )
    if st.session_state.get("_cloud_remember_login") is not False:
        remember_cloud_auth(email, user_id, new_refresh_token)
    return st.session_state.get("cloud_auth", {}), ""


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
    settings["cloud_last_sync_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    st.session_state["settings"] = settings


def _format_cloud_sync_label(raw_value: str, empty_label: str) -> str:
    clean_value = str(raw_value or "").strip()
    if not clean_value:
        return empty_label
    try:
        parsed_sync = datetime.fromisoformat(clean_value.replace("Z", "+00:00"))
        if parsed_sync.tzinfo is None:
            parsed_sync = parsed_sync.replace(tzinfo=timezone.utc)
        return parsed_sync.astimezone(KUWAIT_TZ).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return clean_value


def _build_backup_file() -> tuple[str, bytes]:
    backup_payload = export_app_state_payload()
    backup_now = datetime.now()
    backup_payload["_meta"] = {
        "saved_at": backup_now.isoformat(timespec="seconds"),
        "source": "goushfi_settings_backup",
        "version": 1,
    }
    timestamp_for_file = backup_now.strftime("%Y%m%d_%H%M%S")
    backup_name = f"goushfi_backup_{timestamp_for_file}.json"
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





def _render_cloud_sync_pause_notice(t) -> None:
    reason = cloud_sync_pause_reason(st.session_state)

    if reason in {"local_cloud_conflict_after_sign_in", "local_cloud_conflict_after_cookie_restore"}:
        st.warning(
            t(
                "وجدنا بيانات محلية مختلفة عن البيانات السحابية، لذلك أبقينا بيانات هذا الجهاز كما هي مؤقتًا. إذا أردت استبدالها بنسخة السحابة استخدم استعادة من السحابة، وإذا أردت رفع الحالية استخدم رفع للسحابة.",
                "We found local data that differs from the cloud copy, so this device kept its current local data for now. Use Restore from Cloud to replace it with the cloud copy, or Upload to Cloud to upload the current local data.",
            )
        )
    elif reason in {"cloud_empty_after_sign_in", "cloud_empty_after_cookie_restore"}:
        st.info(
            t(
                "لا توجد نسخة سحابية محفوظة لهذا الحساب حتى الآن. بيانات هذا الجهاز بقيت كما هي، وإذا رغبت في إنشاء نسخة سحابية استخدم رفع للسحابة.",
                "No cloud copy exists for this account yet. This device kept its current local data. If you want to create a cloud copy, use Upload to Cloud.",
            )
        )
    elif reason in {"pull_failed_after_sign_in", "pull_failed_after_cookie_restore"}:
        st.warning(
            t(
                "تم تسجيل الدخول، لكن تعذر تحميل بيانات السحابة الآن. أبقينا بيانات هذا الجهاز كما هي، ويمكنك المحاولة لاحقًا من زر استعادة من السحابة.",
                "You are signed in, but cloud data could not be loaded right now. This device kept its current local data, and you can try again later with Restore from Cloud.",
            )
        )
    elif reason == "cloud_deleted_until_manual_save":
        st.info(
            t(
                "تم حذف النسخة السحابية، لذلك أوقفنا الرفع التلقائي مؤقتًا. إذا رغبت في إنشاء نسخة سحابية جديدة استخدم رفع للسحابة.",
                "The cloud copy was deleted, so auto upload is paused for now. If you want to create a new cloud copy, use Upload to Cloud.",
            )
        )
    elif reason == "token_refresh_failed":
        st.warning(
            t(
                "تعذر تجديد جلسة السحابة تلقائيًا. المزامنة التلقائية متوقفة مؤقتًا. يرجى تسجيل الخروج وإعادة تسجيل الدخول.",
                "Cloud session could not be refreshed automatically. Auto-sync is paused. Please sign out and sign in again.",
            )
        )

    sync_error = str(st.session_state.get("_cloud_sync_last_error") or "").strip()
    if sync_error and reason != "token_refresh_failed":
        st.caption(
            t(
                "آخر محاولة مزامنة تلقائية لم تنجح. بياناتك المحلية آمنة وستُحاول المزامنة مرة أخرى تلقائيًا.",
                "The last auto-sync attempt was not successful. Your local data is safe and sync will retry automatically.",
            )
        )


def _render_cloud_sql_setup(t):
    st.caption(t("SQL إعداد جدول البيانات مرة واحدة:", "One-time data table SQL:"))
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
    lang_code = LANGUAGES.get(settings.get("language", "العربية"), "ar")
    is_en = lang_code == "en"
    t = make_t()

    st.title(t("إعدادات GoushFi", "GoushFi Settings"))

    cloud_sync_enabled = bool(settings.get("cloud_sync_enabled", False))
    last_sync_raw = str(settings.get("cloud_last_sync_at", "") or "").strip()
    last_sync_label = _format_cloud_sync_label(
        last_sync_raw,
        t("لم تتم مزامنة بعد", "No sync yet"),
    )

    cloud_client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))
    cloud_auth = st.session_state.get("cloud_auth", {})
    cloud_logged_in = bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token"))

    # --- "Where is my data?" status card ---
    st.markdown("---")
    if not cloud_sync_enabled:
        device_line = t("الجهاز: محفوظة تلقائيًا على هذا المتصفح", "Device: Auto-saved on this browser")
        cloud_line = t("السحابة: غير مفعّلة", "Cloud: Not enabled")
        warning_line = t(
            "لو مسحت بيانات المتصفح أو غيّرت جهاز، بياناتك تضيع. فعّل السحابة عشان تحفظ نسخة آمنة.",
            "If you clear browser data or switch devices, your data will be lost. Enable cloud for a safe copy.",
        )
        status_bg = "#fffbeb"
        status_border = "#f59e0b"
        status_text = "#92400e"
    elif not cloud_client.is_configured:
        device_line = t("الجهاز: محفوظة تلقائيًا على هذا المتصفح", "Device: Auto-saved on this browser")
        cloud_line = t("السحابة: مفعّلة — غير متاحة في هذه البيئة", "Cloud: Enabled — not available in this environment")
        warning_line = t(
            "السحابة مفعلة، لكنها غير متاحة في هذه البيئة حاليًا.",
            "Cloud sync is enabled, but cloud is not available in this environment right now.",
        )
        status_bg = "#fff7ed"
        status_border = "#f97316"
        status_text = "#9a3412"
    elif cloud_logged_in:
        device_line = t("الجهاز: محفوظة تلقائيًا على هذا المتصفح", "Device: Auto-saved on this browser")
        cloud_line = t(
            f"السحابة: متصلة ({cloud_auth.get('email', '')})",
            f"Cloud: Connected ({cloud_auth.get('email', '')})",
        )
        warning_line = t("بياناتك بأمان — محفوظة على الجهاز والسحابة.", "Your data is safe — saved on device and cloud.")
        status_bg = "#ecfdf5"
        status_border = "#10b981"
        status_text = "#065f46"
    else:
        device_line = t("الجهاز: محفوظة تلقائيًا على هذا المتصفح", "Device: Auto-saved on this browser")
        cloud_line = t("السحابة: مفعّلة — لم يتم تسجيل الدخول بعد", "Cloud: Enabled — not signed in yet")
        warning_line = t(
            "سجّل دخول من تبويب السحابة عشان تبدأ المزامنة.",
            "Sign in from the Cloud tab to start syncing.",
        )
        status_bg = "#eff6ff"
        status_border = "#2563eb"
        status_text = "#1d4ed8"

    _sync_badge = ""
    if cloud_sync_enabled and cloud_logged_in:
        _sync_badge = f"""<div style="
            background:rgba(255,255,255,0.65);
            border:1px solid rgba(15,23,42,0.08);
            border-radius:999px;
            padding:6px 10px;
            font-size:0.84rem;
            font-weight:700;
            white-space:nowrap;
        ">{t("آخر مزامنة", "Last Sync")}: {last_sync_label}</div>"""

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
            <div style="display:flex;gap:10px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;">
                <div>
                    <div style="font-weight:800;font-size:1.05rem;margin-bottom:6px;">{t("أين بياناتي؟", "Where is my data?")}</div>
                    <div style="font-size:0.92rem;">💾 {device_line}</div>
                    <div style="font-size:0.92rem;margin-top:2px;">☁️ {cloud_line}</div>
                    <div style="font-size:0.85rem;margin-top:6px;opacity:0.85;">{warning_line}</div>
                </div>
                {_sync_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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

    tab_general, tab_cloud = st.tabs(
        [
            t("عام", "General"),
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
                format_func=lambda opt: _currency_option_label(opt, lang_code),
            )

        with col2:
            current_language = settings.get("language", "العربية")
            lang_index = LANGUAGE_NAMES.index(current_language) if current_language in LANGUAGE_NAMES else 0
            selected_language = st.selectbox(
                t("اللغة", "Language"),
                LANGUAGE_NAMES,
                index=lang_index,
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
            _builtin_logo = get_builtin_logo_b64()
            st.markdown(
                f'<img src="{_builtin_logo}" alt="GoushFi" style="width:132px;border-radius:14px;" />',
                unsafe_allow_html=True,
            )
        with col_b:
            st.write(f"{t('الاسم', 'Name')}: {settings.get('name', '') or '-'}")
            currency_label = _currency_option_label(settings.get("default_currency", CURRENCY_OPTIONS[0]), lang_code)
            st.write(f"{t('العملة', 'Currency')}: {currency_label}")
            st.write(f"{t('اللغة', 'Language')}: {settings.get('language', 'العربية')}")

        plan_info = get_plan_info()
        tier_key = str(plan_info.get("tier", "beta_free")).strip().lower()
        if tier_key not in PLAN_DEFINITIONS:
            tier_key = "beta_free"
        tier_meta = PLAN_DEFINITIONS[tier_key]
        tier_label = tier_meta["label_en"] if lang_code != "ar" else tier_meta["label_ar"]
        total_features = len(tier_meta.get("features", {}))
        enabled_count = sum(1 for enabled in tier_meta.get("features", {}).values() if enabled)

        st.markdown("---")
        st.subheader(t("خطة الاستخدام الحالية", "Current Plan"))
        st.info(
            t(
                f"الخطة الحالية: {tier_label}.",
                f"Current plan: {tier_label}.",
            )
        )
        st.caption(
            t(
                f"ميزات مفعلة الآن: {enabled_count} / {total_features}.",
                f"Enabled features now: {enabled_count} / {total_features}.",
            )
        )

    with tab_cloud:
        # --- Cloud sync toggle (moved here from old Privacy tab) ---
        st.subheader(t("السحابة", "Cloud"))

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

        cloud_auth = st.session_state.get("cloud_auth", {})

        if not cloud_sync_enabled:
            st.caption(
                t(
                    "السحابة غير مفعّلة. بياناتك محفوظة على هذا الجهاز فقط.",
                    "Cloud is not enabled. Your data is saved on this device only.",
                )
            )
            if bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token")):
                if st.button(t("تسجيل خروج من السحابة", "Sign Out from Cloud"), key="cloud_signout_disabled_btn"):
                    _set_cloud_auth(False)
                    st.session_state["_cloud_remember_login"] = False
                    clear_cloud_auth_cookie()
                    st.session_state["_cloud_browser_storage_clear_requested"] = True
                    st.session_state["_cloud_last_pull_user"] = ""
                    st.success(t("تم تسجيل الخروج.", "Signed out."))
                    st.rerun()
        else:
            client = SupabaseSyncClient.from_runtime(getattr(st, "secrets", None))

            if not client.is_configured:
                st.info(
                    t(
                        "السحابة غير متاحة في هذه البيئة حاليًا.",
                        "Cloud is not available in this environment right now.",
                    )
                )
                with st.expander(t("إعداد متقدم للمطورين", "Advanced setup for developers"), expanded=False):
                    st.caption(
                        t(
                            "لبيئة النشر فقط: أضف مفاتيح ربط السحابة في secrets أو متغيرات البيئة.",
                            "Deployment only: add cloud connection keys in secrets or environment variables.",
                        )
                    )
                    st.caption("Required keys: SUPABASE_URL and SUPABASE_ANON_KEY")
                    _render_cloud_sql_setup(t)
            else:
                logged_in = bool(cloud_auth.get("logged_in")) and bool(cloud_auth.get("access_token"))

                if logged_in:
                    st.success(
                        t(
                            f"مسجل دخول: {cloud_auth.get('email', '')}",
                            f"Signed in: {cloud_auth.get('email', '')}",
                        )
                    )
                    _render_cloud_sync_pause_notice(t)

                    r1c1, r1c2 = st.columns(2)
                    with r1c1:
                        cloud_restore_confirm = st.checkbox(
                            t(
                                "أفهم أن الاستعادة تستبدل بيانات الجهاز",
                                "I understand restore replaces device data",
                            ),
                            key="cloud_restore_confirm",
                        )
                        if st.button(
                            t("استعادة من السحابة", "Restore from Cloud"),
                            use_container_width=True,
                            key="cloud_load_btn",
                            disabled=not cloud_restore_confirm,
                        ):
                            cloud_auth, refresh_error = _refresh_cloud_auth_for_manual_action(client)
                            if refresh_error:
                                cloud_error = _cloud_error_text(refresh_error, t)
                                st.error(t(f"تعذر تحديث الجلسة: {cloud_error}", f"Could not refresh session: {cloud_error}"))
                                st.stop()
                            pull = client.fetch_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""))
                            if not pull.get("ok"):
                                cloud_error = _cloud_error_text(pull.get("error", ""), t)
                                pause_cloud_auto_sync(
                                    st.session_state,
                                    cloud_auth.get("user_id", ""),
                                    reason="pull_failed_after_sign_in",
                                )
                                st.error(t(f"تعذر تحميل البيانات: {cloud_error}", f"Load failed: {cloud_error}"))
                            elif pull.get("data") is None:
                                _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                                pause_cloud_auto_sync(
                                    st.session_state,
                                    cloud_auth.get("user_id", ""),
                                    reason="cloud_empty_after_sign_in",
                                )
                                st.session_state["_cloud_last_snapshot"] = ""
                                st.session_state["_cloud_last_pull_user"] = cloud_auth.get("user_id", "")
                                save_persistent_state()
                                st.info(
                                    t(
                                        "لا توجد بيانات محفوظة في السحابة حتى الآن. بيانات هذا الجهاز بقيت كما هي.",
                                        "No cloud data was found yet. This device kept its current local data.",
                                    )
                                )
                            else:
                                import_app_state_payload(pull.get("data"))
                                _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                                st.session_state["_cloud_last_pull_user"] = cloud_auth.get("user_id", "")
                                st.session_state["_cloud_sync_last_error"] = ""
                                mark_cloud_sync_ready(st.session_state, cloud_auth.get("user_id", ""))
                                _mark_cloud_sync_now()
                                _sync_snapshot_from_state()
                                save_persistent_state()
                                st.success(t("تم استعادة بياناتك من السحابة.", "Your data was restored from cloud."))
                                st.rerun()

                    with r1c2:
                        if st.button(t("رفع للسحابة", "Upload to Cloud"), use_container_width=True, key="cloud_save_btn"):
                            payload = export_app_state_payload()
                            if not payload_has_meaningful_data(payload):
                                st.warning(
                                    t(
                                        "لا توجد بيانات كافية لرفعها. تأكد من وجود معاملات أو التزامات قبل رفعها إلى السحابة.",
                                        "No meaningful data to upload. Make sure you have transactions or items before uploading to cloud.",
                                    )
                                )
                            else:
                                cloud_auth, refresh_error = _refresh_cloud_auth_for_manual_action(client)
                                if refresh_error:
                                    cloud_error = _cloud_error_text(refresh_error, t)
                                    st.error(t(f"تعذر تحديث الجلسة: {cloud_error}", f"Could not refresh session: {cloud_error}"))
                                    st.stop()
                                push = client.upsert_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""), payload)
                                if push.get("ok"):
                                    _set_scope_owner(cloud_auth.get("user_id", ""), cloud_auth.get("email", ""))
                                    st.session_state["_cloud_sync_last_error"] = ""
                                    mark_cloud_sync_ready(st.session_state, cloud_auth.get("user_id", ""))
                                    _mark_cloud_sync_now()
                                    _sync_snapshot_from_state()
                                    save_persistent_state()
                                    st.success(t("تم رفع بياناتك للسحابة.", "Your data was uploaded to cloud."))
                                else:
                                    cloud_error = _cloud_error_text(push.get("error", ""), t)
                                    st.error(t(f"تعذر الرفع: {cloud_error}", f"Upload failed: {cloud_error}"))

                    r2c1, r2c2 = st.columns(2)
                    with r2c1:
                        if st.button(t("تسجيل خروج من السحابة", "Sign Out from Cloud"), use_container_width=True, key="cloud_signout_btn"):
                            _set_cloud_auth(False)
                            st.session_state["_cloud_remember_login"] = False
                            clear_cloud_auth_cookie()
                            st.session_state["_cloud_browser_storage_clear_requested"] = True
                            st.session_state["_cloud_last_pull_user"] = ""
                            clear_cloud_sync_guard(st.session_state)
                            st.success(t("تم تسجيل الخروج.", "Signed out."))
                            st.rerun()

                    with r2c2:
                        delete_confirm = st.checkbox(
                            t("تأكيد حذف النسخة السحابية", "Confirm Delete Cloud Copy"),
                            key="cloud_delete_confirm",
                        )
                        if st.button(
                            t("حذف النسخة السحابية", "Delete Cloud Copy"),
                            use_container_width=True,
                            key="cloud_delete_btn",
                            disabled=not delete_confirm,
                        ):
                            cloud_auth, refresh_error = _refresh_cloud_auth_for_manual_action(client)
                            if refresh_error:
                                cloud_error = _cloud_error_text(refresh_error, t)
                                st.error(t(f"تعذر تحديث الجلسة: {cloud_error}", f"Could not refresh session: {cloud_error}"))
                                st.stop()
                            delete_res = client.delete_user_data(cloud_auth.get("user_id", ""), cloud_auth.get("access_token", ""))
                            if delete_res.get("ok"):
                                st.session_state["_cloud_last_pull_user"] = cloud_auth.get("user_id", "")
                                st.session_state["_cloud_last_snapshot"] = ""
                                pause_cloud_auto_sync(
                                    st.session_state,
                                    cloud_auth.get("user_id", ""),
                                    reason="cloud_deleted_until_manual_save",
                                )
                                _sync_snapshot_from_state()
                                st.success(t("تم حذف النسخة السحابية بالكامل.", "Cloud copy was deleted."))
                                st.info(
                                    t(
                                        "لن يتم رفع البيانات تلقائيًا بعد الحذف. إذا رغبت في إنشاء نسخة سحابية جديدة، استخدم زر رفع للسحابة.",
                                        "Auto upload is paused after deletion. If you want to create a new cloud copy, use Upload to Cloud.",
                                    )
                                )
                                st.rerun()
                            else:
                                cloud_error = _cloud_error_text(delete_res.get("error", ""), t)
                                st.error(t(f"تعذر حذف البيانات: {cloud_error}", f"Delete failed: {cloud_error}"))

                    st.caption(
                        t(
                            "الحذف يشمل النسخة السحابية فقط. بيانات هذا الجهاز لن تتأثر.",
                            "This deletes the cloud copy only. Data on this device is not affected.",
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
                            cloud_auth, refresh_error = _refresh_cloud_auth_for_manual_action(client)
                            if refresh_error:
                                cloud_error = _cloud_error_text(refresh_error, t)
                                st.error(t(f"تعذر تحديث الجلسة: {cloud_error}", f"Could not refresh session: {cloud_error}"))
                                st.stop()
                            data_delete_res = client.delete_user_data(
                                cloud_auth.get("user_id", ""),
                                cloud_auth.get("access_token", ""),
                            )
                            account_delete_res = client.delete_current_user(cloud_auth.get("access_token", ""))

                            if account_delete_res.get("ok"):
                                _set_cloud_auth(False)
                                st.session_state["_cloud_remember_login"] = False
                                clear_cloud_auth_cookie()
                                st.session_state["_cloud_browser_storage_clear_requested"] = True
                                _set_scope_owner("", "")
                                st.session_state["_cloud_last_snapshot"] = ""
                                st.session_state["_cloud_last_pull_user"] = ""
                                clear_cloud_sync_guard(st.session_state)
                                st.success(
                                    t(
                                        "تم حذف الحساب السحابي بالكامل.",
                                        "Cloud account deleted permanently.",
                                    )
                                )
                                st.rerun()

                            account_error = str(account_delete_res.get("error", ""))
                            data_error = str(data_delete_res.get("error", ""))
                            account_error_display = _cloud_error_text(account_error, t)
                            data_error_display = _cloud_error_text(data_error, t)
                            if data_delete_res.get("ok"):
                                st.warning(
                                    t(
                                        f"تم حذف البيانات السحابية لكن حذف الحساب فشل: {account_error_display}",
                                        f"Cloud data deleted, but account deletion failed: {account_error_display}",
                                    )
                                )
                            else:
                                st.error(
                                    t(
                                        f"تعذر حذف الحساب: {account_error_display} | وتعذر حذف البيانات: {data_error_display}",
                                        f"Account deletion failed: {account_error_display} | Data deletion failed: {data_error_display}",
                                    )
                                )

                else:
                    mode = st.selectbox(
                        t("العملية", "Action"),
                        [
                            t("تسجيل دخول", "Sign In"),
                            t("إنشاء حساب", "Sign Up"),
                            t("نسيت كلمة المرور", "Forgot Password"),
                        ],
                        key="cloud_auth_mode",
                    )
                    is_sign_up_mode = mode == t("إنشاء حساب", "Sign Up")
                    is_reset_mode = mode == t("نسيت كلمة المرور", "Forgot Password")

                    email = st.text_input(t("الإيميل", "Email"), type="default", key="cloud_auth_email")
                    password = ""
                    confirm_password = ""
                    if not is_reset_mode:
                        password = st.text_input(t("كلمة المرور", "Password"), type="password", key="cloud_auth_password")
                    if is_sign_up_mode:
                        confirm_password = st.text_input(t("تأكيد كلمة المرور", "Confirm Password"), type="password", key="cloud_auth_confirm_password")
                    remember_login = False
                    if not is_reset_mode:
                        remember_login = st.checkbox(
                            t("تذكر تسجيل الدخول على هذا الجهاز", "Remember sign-in on this device"),
                            value=True,
                            key="cloud_remember_login",
                        )
                        st.caption(
                            t(
                                "عند التفعيل، يبقى تسجيل الدخول محفوظًا على هذا المتصفح. استخدم تسجيل الخروج لإزالته.",
                                "When enabled, sign-in stays saved on this browser. Use Sign Out to remove it.",
                            )
                        )
                    submit_label = t("إرسال رابط الاستعادة", "Send Reset Link") if is_reset_mode else t("متابعة", "Continue")
                    submit = st.button(submit_label, use_container_width=True, key="cloud_auth_submit")

                    if submit:
                        clean_email = email.strip().lower()
                        if not clean_email:
                            st.warning(t("يرجى إدخال البريد الإلكتروني.", "Please enter your email."))
                        elif is_reset_mode:
                            reset_res = client.request_password_reset(clean_email)
                            if reset_res.get("ok"):
                                st.success(
                                    t(
                                        "إذا كان الإيميل مسجلًا، سيتم إرسال رابط استعادة كلمة المرور. يرجى مراجعة البريد والـ Spam.",
                                        "If the email is registered, a password reset link will be sent. Check your inbox and spam folder.",
                                    )
                                )
                                st.caption(
                                    t(
                                        "إذا لم يصل الإيميل، حاول مرة أخرى أو تواصل مع الدعم.",
                                        "If the email does not arrive, try again or contact support.",
                                    )
                                )
                            else:
                                cloud_error = _cloud_error_text(reset_res.get("error", ""), t)
                                st.error(t(f"تعذر إرسال رابط الاستعادة: {cloud_error}", f"Could not send reset link: {cloud_error}"))
                        elif not password:
                            st.warning(t("يرجى إدخال البريد الإلكتروني وكلمة المرور.", "Please enter email and password."))
                        elif is_sign_up_mode and password != confirm_password:
                            st.warning(t("كلمتا المرور غير متطابقتين.", "Passwords do not match."))
                        elif is_sign_up_mode and len(password) < 6:
                            st.warning(t("كلمة المرور يجب أن تكون 6 أحرف على الأقل.", "Password must be at least 6 characters."))
                        else:
                            if mode == t("إنشاء حساب", "Sign Up"):
                                auth_res = client.sign_up(clean_email, password)
                            else:
                                auth_res = client.sign_in(clean_email, password)

                            if not auth_res.get("ok"):
                                cloud_error = _cloud_error_text(auth_res.get("error", ""), t)
                                st.error(t(f"فشل العملية: {cloud_error}", f"Action failed: {cloud_error}"))
                            else:
                                access_token = str(auth_res.get("access_token") or "")
                                refresh_token = str(auth_res.get("refresh_token") or "")
                                user_obj = auth_res.get("user") if isinstance(auth_res.get("user"), dict) else {}

                                if not access_token:
                                    st.info(
                                        t(
                                            "تم إنشاء الحساب. إذا كان التحقق عبر البريد الإلكتروني مفعّلًا، يرجى مراجعة البريد والـ Spam ثم تسجيل الدخول.",
                                            "Account created. If email confirmation is enabled, check your inbox and spam folder, then sign in.",
                                        )
                                    )
                                else:
                                    user_id = str(user_obj.get("id") or "")
                                    if not user_id:
                                        user_res = client.get_user(access_token)
                                        if user_res.get("ok") and isinstance(user_res.get("user"), dict):
                                            user_id = str(user_res["user"].get("id") or "")

                                    if not user_id:
                                        st.error(t("تعذر التحقق من الحساب. يرجى المحاولة مرة أخرى.", "Could not verify your account. Please try again."))
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
                                        st.session_state["_cloud_remember_login"] = bool(remember_login)
                                        if not remember_login:
                                            clear_cloud_auth_cookie()
                                            st.session_state["_cloud_browser_storage_clear_requested"] = True
                                        _set_scope_owner(user_id, clean_email)

                                        local_payload = export_app_state_payload()
                                        pull = client.fetch_user_data(user_id, access_token)
                                        remote_payload = pull.get("data") if isinstance(pull.get("data"), dict) else None
                                        post_login_message = ""
                                        post_login_caption = ""
                                        post_login_message_type = "info"
                                        if pull.get("ok") and remote_payload is not None:
                                            if should_keep_local_data_before_auto_import(local_payload, remote_payload):
                                                pause_cloud_auto_sync(
                                                    st.session_state,
                                                    user_id,
                                                    reason="local_cloud_conflict_after_sign_in",
                                                )
                                                st.session_state["_cloud_last_snapshot"] = payload_snapshot(remote_payload)
                                                st.session_state["_cloud_last_pull_user"] = user_id
                                                save_persistent_state()
                                                post_login_message_type = "warning"
                                                post_login_message = t(
                                                    "تم تسجيل الدخول، لكن وجدنا بيانات محلية مختلفة عن نسخة السحابة. أبقينا بيانات هذا الجهاز كما هي. استخدم استعادة من السحابة إذا أردت استبدالها بنسخة السحابة، أو رفع للسحابة إذا أردت رفع الحالية.",
                                                    "Signed in, but we found local data that differs from the cloud copy. This device kept its current local data. Use Restore from Cloud to replace it with the cloud copy, or Upload to Cloud to upload the current local data.",
                                                )
                                            else:
                                                import_app_state_payload(remote_payload)
                                                _set_scope_owner(user_id, clean_email)
                                                st.session_state["_cloud_last_pull_user"] = user_id
                                                mark_cloud_sync_ready(st.session_state, user_id)
                                                _mark_cloud_sync_now()
                                                _sync_snapshot_from_state()
                                                save_persistent_state()
                                                post_login_message_type = "success"
                                                post_login_message = t("تم تسجيل الدخول وتحميل بياناتك.", "Signed in and data loaded.")

                                        elif pull.get("ok") and pull.get("data") is None:
                                            _set_scope_owner(user_id, clean_email)
                                            st.session_state["_cloud_last_pull_user"] = user_id
                                            st.session_state["_cloud_last_snapshot"] = ""
                                            pause_cloud_auto_sync(
                                                st.session_state,
                                                user_id,
                                                reason="cloud_empty_after_sign_in",
                                            )
                                            save_persistent_state()
                                            post_login_message_type = "info"
                                            post_login_message = t(
                                                "تم تسجيل الدخول. لا توجد بيانات محفوظة في السحابة حاليًا، وبيانات هذا الجهاز بقيت كما هي.",
                                                "Signed in. No cloud data exists yet, and this device kept its current local data.",
                                            )
                                            post_login_caption = t(
                                                "إذا رغبت في إنشاء نسخة سحابية جديدة، استخدم زر رفع للسحابة.",
                                                "If you want to create a new cloud copy, use Upload to Cloud.",
                                            )
                                        else:
                                            pause_cloud_auto_sync(
                                                st.session_state,
                                                user_id,
                                                reason="pull_failed_after_sign_in",
                                            )
                                            save_persistent_state()
                                            post_login_message_type = "warning"
                                            post_login_message = t(
                                                "تم تسجيل الدخول، لكن تعذر تحميل البيانات السحابية الآن. أبقينا بيانات هذا الجهاز كما هي.",
                                                "Signed in, but failed to load cloud data now. This device kept its current local data.",
                                            )

                                        if post_login_message:
                                            if post_login_message_type == "success":
                                                st.success(post_login_message)
                                            elif post_login_message_type == "warning":
                                                st.warning(post_login_message)
                                            else:
                                                st.info(post_login_message)
                                        if post_login_caption:
                                            st.caption(post_login_caption)

                                        if remember_login:
                                            st.session_state["_cloud_cookie_restore_checked"] = False
                                            reload_after_write = not bool(_local_persistence_enabled())
                                            remember_cloud_auth(
                                                clean_email,
                                                user_id,
                                                refresh_token,
                                                reload_after_write=reload_after_write,
                                            )
                                            if reload_after_write:
                                                st.stop()

                                        st.rerun()

        # --- Device Data section (below cloud, always visible) ---
        st.markdown("---")
        st.subheader(t("بيانات هذا الجهاز", "This Device Data"))
        st.caption(
            t(
                "يمسح كل البيانات من هذا المتصفح فقط. النسخة السحابية (إن وجدت) لن تتأثر.",
                "Clears all data from this browser only. Cloud copy (if any) will not be affected.",
            )
        )

        local_delete_confirm = st.checkbox(
            t("تأكيد مسح بيانات الجهاز", "Confirm Clear Device Data"),
            key="local_delete_confirm",
        )

        if st.button(
            t("مسح بيانات هذا الجهاز", "Clear This Device Data"),
            use_container_width=True,
            key="local_delete_btn",
            disabled=not local_delete_confirm,
        ):
            reset_local_app_data()
            st.success(t("تم مسح بيانات هذا الجهاز.", "This device data was cleared."))
            st.info(
                t(
                    "لاستعادة البيانات، استخدم النسخة السحابية أو ملف النسخة الاحتياطية (JSON).",
                    "To restore data, use the cloud copy or a backup file (JSON).",
                )
            )
            st.rerun()

        # --- Backup section ---
        st.markdown("---")
        st.subheader(t("نسخ احتياطي (JSON)", "Backup (JSON)"))
        st.caption(
            t(
                "ملف JSON يحتوي كل بياناتك. يمكنك استخدامه لنقل البيانات لجهاز آخر أو كنسخة أمان.",
                "A JSON file containing all your data. Use it to transfer data to another device or as a safety backup.",
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
                "مكان الحفظ يعتمد على إعدادات المتصفح (غالبًا مجلد Downloads).",
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
