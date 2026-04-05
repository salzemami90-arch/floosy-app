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
    st.markdown(
        """
        <style>
        div.st-key-mustndaty_add_btn {
            position: fixed;
            right: 22px;
            bottom: 22px;
            z-index: 999999;
        }

        div.st-key-mustndaty_add_btn button {
            width: 56px;
            height: 56px;
            border-radius: 18px !important;
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
        """,
        unsafe_allow_html=True,
    )

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
    st.subheader(t("المستندات", "Documents"))

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

    st.dataframe(view, use_container_width=True, hide_index=True)

    # Optional: download attachment for a selected document
    st.markdown(f"#### {t('تنزيل المرفق', 'Download Attachment')}")
    names = [d.get("name") for d in docs]
    sel = st.selectbox(t("اختر مستند", "Select Document"), options=["-"] + names, index=0)
    if sel != "-":
        doc = next((d for d in docs if d.get("name") == sel), None)
        if doc and doc.get("attachment_bytes"):
            st.download_button(
                t("تنزيل المرفق", "Download Attachment"),
                data=doc["attachment_bytes"],
                file_name=doc.get("attachment_name") or "attachment",
            )
        else:
            st.caption(t("لا توجد مرفق لهالمستند", "No attachment for this document"))
