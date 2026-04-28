import streamlit as st
from datetime import date
import pandas as pd


def render():
    lang = st.session_state.get("settings", {}).get("language", "العربية")
    is_en = lang == "English"
    t = (lambda ar, en: en if is_en else ar)
    currency = st.session_state.get("settings", {}).get("default_currency", "د.ك")
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol

    st.title(t("مستنداتي", "Documents"))
    st.caption(t("إدارة المستندات وتنبيهات التجديد", "Document management and renewal reminders"))
    st.markdown(
        """
        <style>
        .flossy-doc-summary {
            border-radius: 16px;
            padding: 14px 16px;
            min-height: 108px;
            border: 1px solid transparent;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .flossy-doc-summary__label {
            font-size: 0.88rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .flossy-doc-summary__value {
            font-size: 1.45rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .flossy-doc-summary__meta {
            font-size: 0.84rem;
            color: #64748b;
            margin-top: 6px;
        }
        .flossy-doc-summary--expired {
            background: linear-gradient(180deg, #fff4f2 0%, #fffaf9 100%);
            border-color: #fecaca;
        }
        .flossy-doc-summary--expired .flossy-doc-summary__label,
        .flossy-doc-summary--expired .flossy-doc-summary__value {
            color: #b42318;
        }
        .flossy-doc-summary--soon {
            background: linear-gradient(180deg, #fffbeb 0%, #fffdf5 100%);
            border-color: #fde68a;
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
        </style>
        """,
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
    fab_side_css = "left: 22px; right: auto;" if not is_en else "right: 22px; left: auto;"

    fab_css = """
        <style>
        div.st-key-mustndaty_add_btn {
            position: fixed;
            __FAB_SIDE__
            bottom: 22px;
            z-index: 999999;
        }

        div.st-key-mustndaty_add_btn button {
            width: 56px;
            height: 56px;
            border-radius: 16px !important;
            background: linear-gradient(135deg, #2c5f87, #3fa37a) !important;
            border: 0 !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.18) !important;
            position: relative;
            padding: 0 !important;
            display: block;
            color: #ffffff !important;
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
            t(f"الرسوم ({currency_view})", f"Fee ({currency_view})"),
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
        st.info(t("لا توجد مستندات حاليًا.", "No documents yet."))
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

    summary_cols = st.columns(3)
    for col, spec in zip(summary_cols, summary_specs):
        count_unit = t("مستند", "document") if spec["count"] == 1 else t("مستندات", "documents")
        col.markdown(
            f"""
            <div class="flossy-doc-summary flossy-doc-summary--{spec["modifier"]}">
                <div>
                    <div class="flossy-doc-summary__label">{spec["label"]}</div>
                    <div class="flossy-doc-summary__value">{spec["count"]}</div>
                </div>
                <div class="flossy-doc-summary__meta">
                    {spec["count"]} {count_unit} • {spec["fee"]:,.0f} {currency_view}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            "fee": t(f"الرسوم ({currency_view})", f"Fee ({currency_view})"),
            "remind_before_months": t("نبهني قبل (شهر)", "Remind Before (Months)"),
            "renewal_cycle_months": t("دورية التجديد (شهر)", "Renewal Cycle (Months)"),
            status_col: t("الحالة", "Status"),
            "attachment_name": t("مرفق", "Attachment"),
            "name": t("اسم المستند", "Document Name"),
        }
    )

    date_columns = [t("تاريخ الإصدار", "Issue Date"), t("تاريخ الانتهاء", "End Date")]
    fee_column = t(f"الرسوم ({currency_view})", f"Fee ({currency_view})")
    status_display_col = t("الحالة", "Status")

    view_display = view.copy()
    for date_column in date_columns:
        if date_column in view_display.columns:
            view_display[date_column] = pd.to_datetime(view_display[date_column], errors="coerce").dt.strftime("%Y-%m-%d").fillna("-")
    if fee_column in view_display.columns:
        view_display[fee_column] = pd.to_numeric(view_display[fee_column], errors="coerce").fillna(0.0).map(
            lambda value: f"{value:,.2f}"
        )

    def _status_style(value: str) -> str:
        if value == expired_label:
            return "background-color: #fff1f2; color: #b42318; font-weight: 800;"
        if value == soon_label:
            return "background-color: #fffbeb; color: #b45309; font-weight: 800;"
        if value == valid_label:
            return "background-color: #ecfdf5; color: #047857; font-weight: 800;"
        return "background-color: #f8fafc; color: #475569; font-weight: 700;"

    styled_view = view_display.style.applymap(_status_style, subset=[status_display_col])
    st.dataframe(styled_view, use_container_width=True, hide_index=True)

    st.markdown(f"#### {t('إجراءات المستند', 'Document Actions')}")
    selectable_indices = df.index.tolist()

    def _document_option_label(idx: int) -> str:
        row = df.loc[idx]
        doc_name = str(row.get("name") or t("مستند بدون اسم", "Untitled Document"))
        end_value = row.get("end_date")
        end_label = end_value.strftime("%Y-%m-%d") if not pd.isna(end_value) else "-"
        status_value = str(row.get(status_col) or "-")
        return f"{doc_name} | {end_label} | {status_value}"

    selected_doc_idx = st.selectbox(
        t("اختيار مستند", "Select Document"),
        options=selectable_indices,
        format_func=_document_option_label,
        index=0,
    )
    selected_doc = docs[int(selected_doc_idx)]

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
