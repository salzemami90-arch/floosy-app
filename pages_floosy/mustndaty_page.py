import streamlit as st
from datetime import date
from html import escape
import pandas as pd

from services.currency_localization import currency_short_label
from services.i18n import format_i18n, make_t, get_lang_code


def render():
    _lc = get_lang_code()
    is_en = _lc == "en"
    is_ltr = _lc != "ar"
    t = make_t()
    currency = st.session_state.get("settings", {}).get("default_currency", "د.ك")
    currency_view = currency_short_label(currency, _lc)
    text_align = "left" if is_ltr else "right"

    st.title(t("مستنداتي", "Documents"))
    st.caption(t("إدارة المستندات وتنبيهات التجديد", "Document management and renewal reminders"))
    st.markdown(
        """
        <style>
        section[data-testid="stMain"] .stMainBlockContainer.block-container,
        section[data-testid="stMain"] .block-container {
            max-width: min(1180px, 100%) !important;
            padding-top: 0.25rem !important;
            padding-left: clamp(0.95rem, 2vw, 1.9rem) !important;
            padding-right: clamp(0.95rem, 2vw, 1.9rem) !important;
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlock"] {
            gap: 0.72rem;
        }
        section[data-testid="stMain"] h1 {
            margin-bottom: 0.1rem !important;
            font-size: 2.05rem !important;
            line-height: 1.08 !important;
            letter-spacing: 0 !important;
        }
        section[data-testid="stMain"] h4 {
            margin-top: 0.3rem !important;
            margin-bottom: 0.28rem !important;
            line-height: 1.24 !important;
            letter-spacing: 0 !important;
        }
        section[data-testid="stMain"] p,
        section[data-testid="stMain"] .stCaption,
        section[data-testid="stMain"] [data-testid="stCaptionContainer"] {
            line-height: 1.48;
        }
        section[data-testid="stMain"] hr {
            margin: 0.75rem 0 0.55rem 0 !important;
            border-color: rgba(15, 23, 42, 0.08) !important;
        }
        .flossy-doc-summary {
            border-radius: 16px;
            padding: 13px 15px;
            min-height: 102px;
            border: 1px solid transparent;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
            position: relative;
        }
        .flossy-doc-summary::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.68), rgba(255,255,255,0.16));
            pointer-events: none;
        }
        .flossy-doc-summary > * {
            position: relative;
            z-index: 1;
        }
        .flossy-doc-summary__label {
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 6px;
            line-height: 1.28;
        }
        .flossy-doc-summary__value {
            font-size: 1.5rem;
            font-weight: 850;
            line-height: 1.1;
        }
        .flossy-doc-summary__meta {
            font-size: 0.78rem;
            color: #64748b;
            margin-top: 6px;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }
        .flossy-doc-summary--expired {
            background: linear-gradient(180deg, #fff8f6 0%, #fffdfc 100%);
            border-color: #f1d1c4;
        }
        .flossy-doc-summary--expired .flossy-doc-summary__label,
        .flossy-doc-summary--expired .flossy-doc-summary__value {
            color: #8a4a3c;
        }
        .flossy-doc-summary--soon {
            background: linear-gradient(180deg, #fffdf5 0%, #fffefa 100%);
            border-color: #f9e7a7;
        }
        .flossy-doc-summary--soon .flossy-doc-summary__label,
        .flossy-doc-summary--soon .flossy-doc-summary__value {
            color: #b45309;
        }
        .flossy-doc-summary--valid {
            background: linear-gradient(180deg, #ecfdf5 0%, #f8fffb 100%);
            border-color: #bbf7d0;
        }
        .flossy-doc-summary--valid .flossy-doc-summary__label,
        .flossy-doc-summary--valid .flossy-doc-summary__value {
            color: #047857;
        }
        .flossy-doc-empty-card {
            border: 1px solid rgba(15, 95, 140, 0.12);
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(15, 95, 140, 0.055), rgba(18, 149, 107, 0.05));
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
            padding: 18px 18px;
            margin-top: 0.55rem;
            text-align: __TEXT_ALIGN__;
        }
        .flossy-doc-empty-card__title {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.28;
            margin-bottom: 0.35rem;
        }
        .flossy-doc-empty-card__text {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.5;
        }
        .flossy-doc-search-note {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.4;
            margin-top: -0.15rem;
        }
        .flossy-doc-action-summary {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.72);
            padding: 11px 13px;
            margin: 0.1rem 0 0.45rem 0;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
        }
        .flossy-doc-action-summary__name {
            color: #0f172a;
            font-size: 0.92rem;
            font-weight: 850;
            line-height: 1.32;
            overflow-wrap: anywhere;
        }
        .flossy-doc-action-summary__meta {
            color: #64748b;
            font-size: 0.76rem;
            line-height: 1.35;
            margin-top: 0.15rem;
        }
        .flossy-doc-status-pill {
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 0.74rem;
            font-weight: 850;
            line-height: 1.1;
            white-space: nowrap;
            border: 1px solid rgba(15, 23, 42, 0.08);
        }
        .flossy-doc-status-pill--expired {
            color: #8a4a3c;
            background: #fff8f6;
            border-color: #f1d1c4;
        }
        .flossy-doc-status-pill--soon {
            color: #92400e;
            background: #fffdf5;
            border-color: #f9e7a7;
        }
        .flossy-doc-status-pill--valid {
            color: #047857;
            background: #ecfdf5;
            border-color: #bbf7d0;
        }
        .flossy-doc-status-pill--neutral {
            color: #475569;
            background: #f8fafc;
            border-color: #e2e8f0;
        }
        section[data-testid="stMain"] div[data-testid="stTextInput"] input,
        section[data-testid="stMain"] div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[role="dialog"] div[data-testid="stTextInput"] input,
        div[role="dialog"] div[data-testid="stNumberInput"] input,
        div[role="dialog"] div[data-testid="stDateInput"] input {
            min-height: 40px !important;
        }
        section[data-testid="stMain"] label[data-testid="stWidgetLabel"] p,
        div[role="dialog"] label[data-testid="stWidgetLabel"] p {
            font-size: 0.8rem !important;
            line-height: 1.22 !important;
            margin-bottom: 0.12rem !important;
            color: #475569 !important;
        }
        section[data-testid="stMain"] div[data-testid="stDataFrame"] {
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
        }
        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(15, 23, 42, 0.09) !important;
            border-radius: 15px !important;
            background: rgba(255, 255, 255, 0.64) !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035) !important;
        }
        div[role="dialog"],
        div[data-testid="stDialog"] div[role="dialog"] {
            border-radius: 18px !important;
            background: #ffffff !important;
            border: 1px solid rgba(15, 23, 42, 0.10) !important;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.26) !important;
        }
        div[data-testid="stDialog"] div[role="dialog"] > div {
            background: #ffffff !important;
        }
        div[role="dialog"] div[data-testid="stVerticalBlock"] {
            gap: 0.64rem;
        }
        div[role="dialog"] h2,
        div[role="dialog"] h3,
        div[role="dialog"] h4 {
            letter-spacing: 0 !important;
            line-height: 1.22 !important;
        }
        div[role="dialog"] div[data-testid="stFileUploader"] section,
        div[role="dialog"] section[data-testid="stFileUploaderDropzone"] {
            border: 1px dashed rgba(15, 95, 140, 0.28) !important;
            border-radius: 16px !important;
            background: linear-gradient(135deg, rgba(15, 95, 140, 0.055), rgba(18, 149, 107, 0.045)) !important;
            min-height: 104px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
        }
        div[role="dialog"] div[data-testid="stFileUploader"] small {
            color: #64748b !important;
        }
        div[role="dialog"] .stButton button,
        section[data-testid="stMain"] .stButton button,
        section[data-testid="stMain"] .stDownloadButton button {
            min-height: 40px;
            font-weight: 750;
        }
        @media (max-width: 760px) {
            section[data-testid="stMain"] .stMainBlockContainer.block-container,
            section[data-testid="stMain"] .block-container {
                padding-left: 0.72rem !important;
                padding-right: 0.72rem !important;
            }
            section[data-testid="stMain"] h1 {
                font-size: 1.55rem !important;
            }
            .flossy-doc-summary {
                min-height: 94px;
                padding: 12px 13px;
            }
            .flossy-doc-action-summary {
                align-items: flex-start;
                flex-direction: column;
                gap: 8px;
            }
            section[data-testid="stMain"] div[data-testid="column"],
            div[role="dialog"] div[data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 100% !important;
            }
            div[role="dialog"] {
                width: calc(100vw - 24px) !important;
                max-width: calc(100vw - 24px) !important;
                max-height: calc(100vh - 24px) !important;
                overflow-y: auto !important;
            }
        }
        </style>
        """.replace("__TEXT_ALIGN__", text_align),
        unsafe_allow_html=True,
    )

    # =============================
    # Storage (DON'T reset on rerun)
    # =============================
    docs = st.session_state.setdefault("documents", [])
    st.session_state["mustndaty_documents"] = docs

    # Dialog open state (no URL params -> no jumping to dashboard)
    st.session_state.setdefault("mustndaty_add_open", False)

    def _open_add_modal():
        st.session_state["mustndaty_add_open"] = True

    def _close_add_modal():
        st.session_state["mustndaty_add_open"] = False

    def _clear_form_state():
        # Clear widget keys after save so next add starts clean
        for key in [
            "doc_name",
            "doc_issue",
            "doc_end",
            "doc_remind",
            "doc_cycle",
            "doc_fee",
            "doc_file",
        ]:
            st.session_state.pop(key, None)

    # =============================
    # Add (+) button (match dashboard FAB)
    # =============================
    fab_side_css = "left: 22px; right: auto;" if not is_ltr else "right: 22px; left: auto;"

    fab_css = """
        <style>
        div.st-key-mustndaty_add_btn {
            position: fixed;
            __FAB_SIDE__
            bottom: calc(24px + env(safe-area-inset-bottom, 0px));
            z-index: 999999;
        }

        div.st-key-mustndaty_add_btn button {
            width: 56px;
            height: 56px;
            border-radius: 18px !important;
            background: linear-gradient(135deg, #2c5f87, #3fa37a) !important;
            border: 0 !important;
            box-shadow: 0 16px 34px rgba(15, 95, 140, 0.24), 0 6px 16px rgba(15, 23, 42, 0.16) !important;
            position: relative;
            padding: 0 !important;
            display: block;
            color: #ffffff !important;
            transition: transform 120ms ease, filter 120ms ease;
        }

        /* Draw the + using CSS so Streamlit can't hide button text */
        div.st-key-mustndaty_add_btn button::before {
            content: "+";
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            font-weight: 900;
            color: #ffffff;
            pointer-events: none;
        }

        div.st-key-mustndaty_add_btn button:hover {
            filter: brightness(1.05);
            transform: translateY(-1px);
        }

        @media (max-width: 760px) {
            div.st-key-mustndaty_add_btn {
                bottom: calc(18px + env(safe-area-inset-bottom, 0px));
            }

            div.st-key-mustndaty_add_btn button {
                width: 52px;
                height: 52px;
                border-radius: 17px !important;
            }
        }
        </style>
    """.replace("__FAB_SIDE__", fab_side_css)
    st.markdown(fab_css, unsafe_allow_html=True)

    add_clicked = st.button("", key="mustndaty_add_btn", help=t("إضافة مستند", "Add document"))
    if add_clicked:
        _open_add_modal()

    # =============================
    # Add document form
    # =============================
    def _add_doc_form():
        name = st.text_input(t("اسم المستند", "Document Name"), key="doc_name")

        col_a, col_b = st.columns(2)
        with col_a:
            issue_date = st.date_input(t("تاريخ الإصدار", "Issue Date"), value=date.today(), key="doc_issue")
        with col_b:
            end_date = st.date_input(t("تاريخ الانتهاء", "End Date"), value=date.today(), key="doc_end")

        st.markdown(f"#### {t('التنبيهات', 'Reminders')}")
        col_c, col_d = st.columns(2)
        with col_c:
            remind_before_months = st.number_input(
                t("نبهني قبل الانتهاء (بالأشهر)", "Remind me before end date (months)"),
                min_value=0,
                max_value=120,
                value=1,
                step=1,
                key="doc_remind",
            )
        with col_d:
            renewal_cycle_months = st.number_input(
                t("دورية التجديد (بالأشهر)", "Renewal cycle (months)"),
                min_value=0,
                max_value=120,
                value=12,
                step=1,
                key="doc_cycle",
            )

        fee = st.number_input(
            f"{t('الرسوم', 'Fee')} ({currency_view})",
            min_value=0.0,
            step=1.0,
            value=0.0,
            key="doc_fee",
        )

        uploaded = st.file_uploader(
            t("مرفق (اختياري)", "Attachment (Optional)"),
            type=["png", "jpg", "jpeg", "pdf"],
            key="doc_file",
        )

        col1, col2 = st.columns(2)
        with col1:
            save = st.button(t("حفظ", "Save"), key="doc_save")
        with col2:
            cancel = st.button(t("إلغاء", "Cancel"), key="doc_cancel")

        if cancel:
            _close_add_modal()
            st.rerun()

        if save:
            if not name.strip():
                st.warning(t("يرجى إدخال اسم المستند.", "Please enter document name."))
                return

            attachment_name = None
            attachment_bytes = None
            if uploaded is not None:
                attachment_name = uploaded.name
                attachment_bytes = uploaded.getvalue()

            # APPEND ONLY (no reassignment)
            docs.append(
                {
                    "name": name.strip(),
                    "issue_date": str(issue_date),
                    "end_date": str(end_date),
                    "remind_before_months": int(remind_before_months),
                    "renewal_cycle_months": int(renewal_cycle_months),
                    "fee": float(fee),
                    "attachment_name": attachment_name,
                    "attachment_bytes": attachment_bytes,
                }
            )

            _close_add_modal()
            _clear_form_state()
            st.toast(t("تم الحفظ.", "Saved."))
            st.rerun()

    # Show dialog if supported, else inline form
    if st.session_state.get("mustndaty_add_open"):
        if hasattr(st, "dialog"):
            @st.dialog(t("إضافة مستند", "Add Document"))
            def _show_add_doc_dialog():
                _add_doc_form()

            _show_add_doc_dialog()
        else:
            st.info(t("إصدار Streamlit الحالي لا يدعم dialog، لذلك سيظهر نموذج بديل داخل الصفحة.", "This Streamlit version does not support dialog, so an inline form is shown instead."))
            _add_doc_form()

    st.markdown("---")

    if not docs:
        st.markdown(
            f"""
            <div class="flossy-doc-empty-card">
                <div class="flossy-doc-empty-card__title">{t("لا توجد مستندات حاليًا.", "No documents yet.")}</div>
                <div class="flossy-doc-empty-card__text">{t("أضف أول مستند من زر الإضافة للبدء بتنظيم التواريخ والتنبيهات.", "Add your first document from the add button to start organizing dates and reminders.")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(docs)

    # Dates
    df["issue_date"] = pd.to_datetime(df.get("issue_date"), errors="coerce")
    df["end_date"] = pd.to_datetime(df.get("end_date"), errors="coerce")

    today = pd.to_datetime(date.today())
    df["days_to_end"] = (df["end_date"] - today).dt.days

    def _status(days):
        if pd.isna(days):
            return t("غير محدد", "Unknown")
        if days < 0:
            return t("منتهي", "Expired")
        if days <= 30:
            return t("قريب ينتهي", "Expiring Soon")
        return t("ساري", "Valid")

    status_col = t("الحالة", "Status")
    df[status_col] = df["days_to_end"].apply(_status)

    # Sort by end date
    df = df.sort_values(by=["end_date"], ascending=True, na_position="last")

    expired_label = t("منتهي", "Expired")
    soon_label = t("قريب ينتهي", "Expiring Soon")
    valid_label = t("ساري", "Valid")

    expired_count = int((df[status_col] == expired_label).sum())
    soon_count = int((df[status_col] == soon_label).sum())
    valid_count = int((df[status_col] == valid_label).sum())

    fee_series = pd.to_numeric(df.get("fee"), errors="coerce").fillna(0.0)
    expired_fee_total = float(fee_series[df[status_col] == expired_label].sum())
    soon_fee_total = float(fee_series[df[status_col] == soon_label].sum())
    valid_fee_total = float(fee_series[df[status_col] == valid_label].sum())

    summary_specs = [
        {
            "modifier": "expired",
            "label": t("منتهية", "Expired"),
            "count": expired_count,
            "fee": expired_fee_total,
        },
        {
            "modifier": "soon",
            "label": t("قريبة للتجديد", "Renew Soon"),
            "count": soon_count,
            "fee": soon_fee_total,
        },
        {
            "modifier": "valid",
            "label": t("سارية", "Valid"),
            "count": valid_count,
            "fee": valid_fee_total,
        },
    ]

    st.markdown(f"#### {t('الإحصائيات', 'Statistics')}")
    summary_cols = st.columns(3)
    for col, spec in zip(summary_cols, summary_specs):
        count_label = format_i18n("document_count", count=spec["count"])
        col.markdown(
            f"""
            <div class="flossy-doc-summary flossy-doc-summary--{spec["modifier"]}">
                <div>
                    <div class="flossy-doc-summary__label">{spec["label"]}</div>
                    <div class="flossy-doc-summary__value">{spec["count"]}</div>
                </div>
                <div class="flossy-doc-summary__meta">
                    {count_label} • {spec["fee"]:,.0f} {currency_view}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    view = df[[
        "name",
        "issue_date",
        "end_date",
        "fee",
        "remind_before_months",
        "renewal_cycle_months",
        status_col,
        "attachment_name",
    ]].rename(
        columns={
            "name": "اسم المستند",
            "issue_date": t("تاريخ الإصدار", "Issue Date"),
            "end_date": t("تاريخ الانتهاء", "End Date"),
            "fee": f"{t('الرسوم', 'Fee')} ({currency_view})",
            "remind_before_months": t("نبهني قبل (شهر)", "Remind Before (Months)"),
            "renewal_cycle_months": t("دورية التجديد (شهر)", "Renewal Cycle (Months)"),
            status_col: t("الحالة", "Status"),
            "attachment_name": t("مرفق", "Attachment"),
            "name": t("اسم المستند", "Document Name"),
        }
    )

    date_columns = [t("تاريخ الإصدار", "Issue Date"), t("تاريخ الانتهاء", "End Date")]
    fee_column = f"{t('الرسوم', 'Fee')} ({currency_view})"
    status_display_col = t("الحالة", "Status")

    view_display = view.copy()
    for date_column in date_columns:
        if date_column in view_display.columns:
            view_display[date_column] = pd.to_datetime(view_display[date_column], errors="coerce").dt.strftime("%Y-%m-%d").fillna("-")
    if fee_column in view_display.columns:
        view_display[fee_column] = pd.to_numeric(view_display[fee_column], errors="coerce").fillna(0.0).map(
            lambda value: f"{value:,.2f}"
        )
    attachment_column = t("مرفق", "Attachment")
    if attachment_column in view_display.columns:
        empty_attachment_label = t("لا يوجد", "None")
        view_display[attachment_column] = (
            view_display[attachment_column]
            .fillna("")
            .astype(str)
            .replace({"": empty_attachment_label, "None": empty_attachment_label, "nan": empty_attachment_label})
        )

    def _status_style(value: str) -> str:
        if value == expired_label:
            return "background-color: #fff1f2; color: #b42318; font-weight: 800;"
        if value == soon_label:
            return "background-color: #fffbeb; color: #b45309; font-weight: 800;"
        if value == valid_label:
            return "background-color: #ecfdf5; color: #047857; font-weight: 800;"
        return "background-color: #f8fafc; color: #475569; font-weight: 700;"

    styled_view = view_display.style.map(_status_style, subset=[status_display_col])
    table_height = min(560, max(92, 38 * (len(view_display) + 1)))
    st.dataframe(styled_view, use_container_width=True, hide_index=True, height=table_height)

    all_label = t("الكل", "All")
    st.markdown(f"#### {t('بحث المستندات', 'Search Documents')}")
    with st.container(border=True):
        search_col, status_filter_col = st.columns([2, 1])
        with search_col:
            docs_search = st.text_input(
                t("بحث المستندات", "Search Documents"),
                placeholder=t(
                    "ابحث باسم المستند أو المرفق أو التاريخ",
                    "Search by document name, attachment, or date",
                ),
                key="mustndaty_search",
            ).strip()
        with status_filter_col:
            selected_status = st.selectbox(
                t("تصفية الحالة", "Filter Status"),
                options=[all_label, expired_label, soon_label, valid_label],
                key="mustndaty_status_filter",
            )

    filtered_df = df.copy()
    if selected_status != all_label:
        filtered_df = filtered_df[filtered_df[status_col] == selected_status]

    if docs_search:
        search_query = docs_search.lower()
        issue_text = filtered_df["issue_date"].dt.strftime("%Y-%m-%d").fillna("")
        end_text = filtered_df["end_date"].dt.strftime("%Y-%m-%d").fillna("")
        attachment_text = filtered_df.get("attachment_name", pd.Series(index=filtered_df.index, dtype="object")).fillna("").astype(str)
        name_text = filtered_df.get("name", pd.Series(index=filtered_df.index, dtype="object")).fillna("").astype(str)
        status_text = filtered_df[status_col].fillna("").astype(str)
        search_mask = (
            name_text.str.lower().str.contains(search_query, na=False)
            | attachment_text.str.lower().str.contains(search_query, na=False)
            | issue_text.str.lower().str.contains(search_query, na=False)
            | end_text.str.lower().str.contains(search_query, na=False)
            | status_text.str.lower().str.contains(search_query, na=False)
        )
        filtered_df = filtered_df[search_mask]

    search_is_active = bool(docs_search) or selected_status != all_label
    if not search_is_active:
        return

    st.caption(
        format_i18n("document_results", shown=len(filtered_df), total=len(df))
    )

    if filtered_df.empty:
        st.markdown(
            f"""
            <div class="flossy-doc-empty-card">
                <div class="flossy-doc-empty-card__title">{t("لا توجد مستندات مطابقة.", "No matching documents.")}</div>
                <div class="flossy-doc-empty-card__text">{t("جرّب تخفيف البحث أو اختيار حالة مختلفة.", "Try a broader search or choose a different status.")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"#### {t('إجراءات المستند', 'Document Actions')}")
    selectable_indices = filtered_df.index.tolist()

    def _document_option_label(idx: int) -> str:
        row = filtered_df.loc[idx]
        doc_name = str(row.get("name") or t("مستند بدون اسم", "Untitled Document"))
        end_value = row.get("end_date")
        end_label = end_value.strftime("%Y-%m-%d") if not pd.isna(end_value) else "-"
        status_value = str(row.get(status_col) or "-")
        return f"{doc_name} | {end_label} | {status_value}"

    with st.container(border=True):
        if len(selectable_indices) == 1:
            selected_doc_idx = selectable_indices[0]
        else:
            selected_doc_idx = st.selectbox(
                t("اختيار مستند", "Select Document"),
                options=selectable_indices,
                format_func=_document_option_label,
                index=0,
            )
        selected_doc = docs[int(selected_doc_idx)]
        selected_row = filtered_df.loc[selected_doc_idx]
        selected_status_value = str(selected_row.get(status_col) or "-")
        selected_end = selected_row.get("end_date")
        selected_end_label = selected_end.strftime("%Y-%m-%d") if not pd.isna(selected_end) else "-"
        selected_modifier = (
            "expired" if selected_status_value == expired_label
            else "soon" if selected_status_value == soon_label
            else "valid" if selected_status_value == valid_label
            else "neutral"
        )
        selected_name = str(selected_row.get("name") or t("مستند بدون اسم", "Untitled Document"))
        st.markdown(
            f"""
            <div class="flossy-doc-action-summary">
                <div>
                    <div class="flossy-doc-action-summary__name">{escape(selected_name)}</div>
                    <div class="flossy-doc-action-summary__meta">{t("تاريخ الانتهاء", "End Date")}: {escape(selected_end_label)}</div>
                </div>
                <div class="flossy-doc-status-pill flossy-doc-status-pill--{selected_modifier}">{escape(selected_status_value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if selected_doc.get("attachment_bytes"):
                st.download_button(
                    t("تنزيل المرفق", "Download Attachment"),
                    data=selected_doc["attachment_bytes"],
                    file_name=selected_doc.get("attachment_name") or "attachment",
                    use_container_width=True,
                )
            else:
                st.caption(t("لا يوجد مرفق لهذا المستند.", "No attachment is available for this document."))

        with action_col2:
            delete_confirm = st.checkbox(
                t("تأكيد حذف المستند", "Confirm Document Deletion"),
                key=f"doc_delete_confirm_{int(selected_doc_idx)}",
            )
            if st.button(
                t("حذف المستند", "Delete Document"),
                key=f"doc_delete_btn_{int(selected_doc_idx)}",
                use_container_width=True,
                disabled=not delete_confirm,
            ):
                docs.pop(int(selected_doc_idx))
                st.session_state["mustndaty_documents"] = docs
                st.toast(t("تم حذف المستند.", "Document deleted."))
                st.rerun()
