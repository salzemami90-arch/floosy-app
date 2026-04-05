from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from config_floosy import arabic_months, english_months
from services.expense_tax_service import ExpenseTaxService


DEFAULT_PROJECT_TYPES = ["خدمي", "تجاري", "محتوى", "تعليمي", "أخرى"]
PROJECT_TYPE_AR_TO_EN = {
    "خدمي": "Service",
    "تجاري": "Commercial",
    "محتوى": "Content",
    "تعليمي": "Educational",
    "أخرى": "Other",
}
PROJECT_TYPE_EN_TO_AR = {v: k for k, v in PROJECT_TYPE_AR_TO_EN.items()}


def _project_type_label(value: str, is_en: bool) -> str:
    clean_value = str(value or "").strip()
    if not is_en:
        if clean_value in PROJECT_TYPE_EN_TO_AR:
            return PROJECT_TYPE_EN_TO_AR[clean_value]
        return clean_value or "أخرى"
    if clean_value in PROJECT_TYPE_AR_TO_EN:
        return PROJECT_TYPE_AR_TO_EN[clean_value]
    return clean_value or "Other"


def _normalize_project_type_value(value: str) -> str:
    clean_value = str(value or "").strip()
    if clean_value in PROJECT_TYPE_EN_TO_AR:
        clean_value = PROJECT_TYPE_EN_TO_AR[clean_value]
    if clean_value not in DEFAULT_PROJECT_TYPES:
        return "أخرى"
    return clean_value


def _ensure_project_defaults(project_obj: dict) -> None:
    project_obj["project_type"] = _normalize_project_type_value(project_obj.get("project_type", "أخرى"))
    project_obj.setdefault("expected_income", 0.0)
    project_obj.setdefault("expected_expense", 0.0)
    project_obj.setdefault("note", "")
    project_obj.setdefault("transactions", [])
    project_obj.setdefault("tax_override_enabled", False)
    project_obj.setdefault("tax_rate", 0.0)
    project_obj.setdefault("prices_include_tax", False)


def _ensure_multi_project_model(month_obj: dict) -> None:
    month_obj.setdefault("projects", {})
    month_obj.setdefault("selected_project", "")

    projects = month_obj["projects"]

    # Migrate legacy data only if it actually exists.
    if not projects:
        has_legacy = bool(month_obj.get("project_transactions")) or bool((month_obj.get("project_name") or "").strip())
        has_legacy = has_legacy or float(month_obj.get("budget_expected_income", 0.0) or 0.0) > 0
        has_legacy = has_legacy or float(month_obj.get("budget_expected_operating", 0.0) or 0.0) > 0
        has_legacy = has_legacy or bool((month_obj.get("budget_note") or "").strip())

        if has_legacy:
            legacy_name = (month_obj.get("project_name") or "").strip() or "مشروعي"
            projects[legacy_name] = {
                "project_type": "أخرى",
                "expected_income": float(month_obj.get("budget_expected_income", 0.0)),
                "expected_expense": float(month_obj.get("budget_expected_operating", 0.0)),
                "note": month_obj.get("budget_note", ""),
                "transactions": list(month_obj.get("project_transactions", [])),
            }

    for p in projects.values():
        _ensure_project_defaults(p)

    if projects:
        if not month_obj["selected_project"] or month_obj["selected_project"] not in projects:
            month_obj["selected_project"] = next(iter(projects.keys()))
    else:
        month_obj["selected_project"] = ""


def _sync_legacy_fields(month_obj: dict) -> None:
    projects = month_obj.get("projects", {})
    selected_name = month_obj.get("selected_project", "")
    selected = projects.get(selected_name, {})

    all_txs = []
    for name, obj in projects.items():
        for tx in obj.get("transactions", []):
            tx_copy = dict(tx)
            tx_copy.setdefault("project_name", name)
            tx_copy.setdefault("project_type", obj.get("project_type", "أخرى"))
            all_txs.append(tx_copy)

    month_obj["project_name"] = selected_name
    month_obj["budget_expected_income"] = float(selected.get("expected_income", 0.0))
    month_obj["budget_expected_operating"] = float(selected.get("expected_expense", 0.0))
    month_obj["budget_note"] = selected.get("note", "")
    month_obj["project_transactions"] = all_txs


def _project_net(project_obj: dict) -> float:
    txs = project_obj.get("transactions", [])
    income = sum(float(x.get("amount", 0.0)) for x in txs if x.get("type") == "دخل")
    expense = sum(float(x.get("amount", 0.0)) for x in txs if x.get("type") == "مصروف")
    return float(income - expense)


def _render_add_project_form(month_obj: dict, t, is_en: bool):
    with st.form("project_add_form", clear_on_submit=True):
        name = st.text_input(t("اسم المشروع", "Project Name"))
        p_type = st.selectbox(
            t("نوع المشروع", "Project Type"),
            DEFAULT_PROJECT_TYPES,
            format_func=lambda x: _project_type_label(x, is_en),
        )
        c1, c2 = st.columns(2)
        with c1:
            save = st.form_submit_button(t("حفظ", "Save"), use_container_width=True)
        with c2:
            cancel = st.form_submit_button(t("إلغاء", "Cancel"), use_container_width=True)

    if cancel:
        st.session_state["project_add_open"] = False
        st.rerun()

    if save:
        clean_name = name.strip()
        if not clean_name:
            st.warning(t("يرجى إدخال اسم المشروع أولًا.", "Please enter the project name first."))
            return
        if clean_name in month_obj["projects"]:
            st.warning(t("اسم المشروع موجود مسبقاً.", "Project name already exists."))
            return

        month_obj["projects"][clean_name] = {
            "project_type": p_type,
            "expected_income": 0.0,
            "expected_expense": 0.0,
            "note": "",
            "transactions": [],
        }
        month_obj["selected_project"] = clean_name
        _sync_legacy_fields(month_obj)
        st.session_state["project_add_open"] = False
        st.success(t("تمت إضافة المشروع.", "Project added."))
        st.rerun()


def _rename_project(month_obj: dict, old_name: str, new_name: str) -> tuple[bool, str]:
    clean_name = new_name.strip()
    if not clean_name:
        return False, "empty"
    if clean_name == old_name:
        return False, "same"
    if clean_name in month_obj["projects"]:
        return False, "exists"

    month_obj["projects"][clean_name] = month_obj["projects"].pop(old_name)
    month_obj["selected_project"] = clean_name
    _sync_legacy_fields(month_obj)
    return True, "ok"


def _delete_project(month_obj: dict, name: str) -> None:
    month_obj["projects"].pop(name, None)
    if month_obj["projects"]:
        month_obj["selected_project"] = next(iter(month_obj["projects"].keys()))
    else:
        month_obj["selected_project"] = ""
    _sync_legacy_fields(month_obj)


def render(month_key: str, month: str, year: int):
    is_en = st.session_state.settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month

    st.title(f"{t('المشاريع', 'Projects')} - {month_display} {year}")

    month_obj = st.session_state.project_data[month_key]
    _ensure_multi_project_model(month_obj)

    currency = st.session_state.settings["default_currency"]
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol

    tax_profile_raw = st.session_state.get("tax_profile", {})
    default_tax_rate = float(tax_profile_raw.get("default_tax_rate", 0.0) or 0.0) if isinstance(tax_profile_raw, dict) else 0.0
    default_prices_include_tax = bool(tax_profile_raw.get("prices_include_tax", False)) if isinstance(tax_profile_raw, dict) else False
    tax_options = ExpenseTaxService.expense_options(st.session_state, is_en=is_en)
    tax_codes = [opt["code"] for opt in tax_options]
    tax_label_by_code = {opt["code"]: opt["label"] for opt in tax_options}
    default_expense_tax_code = next((opt["code"] for opt in tax_options if opt.get("deductible")), tax_codes[0] if tax_codes else "")

    st.session_state.setdefault("project_add_open", False)

    st.markdown(
        """
        <style>
        div.st-key-project_add_btn button {
            border-radius: 12px;
            font-weight: 700;
        }
        div[class*="st-key-project_card_"] button {
            background: linear-gradient(135deg, #0f5f8c, #12956b) !important;
            color: #ffffff !important;
            border: 0 !important;
            border-radius: 14px !important;
            min-height: 94px !important;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.14) !important;
            font-weight: 700 !important;
            white-space: pre-line !important;
            line-height: 1.4 !important;
            text-align: right !important;
            padding: 10px 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button(t("＋ إضافة مشروع", "＋ Add Project"), key="project_add_btn"):
        st.session_state["project_add_open"] = True
        st.rerun()

    if st.session_state.get("project_add_open"):
        if hasattr(st, "dialog"):
            @st.dialog(t("إضافة مشروع", "Add Project"))
            def _show_add_project_dialog():
                _render_add_project_form(month_obj, t, is_en)

            _show_add_project_dialog()
        else:
            with st.expander(t("إضافة مشروع", "Add Project"), expanded=True):
                _render_add_project_form(month_obj, t, is_en)

    st.markdown(f"### {t('قائمة المشاريع', 'Projects List')}")
    names = list(month_obj["projects"].keys())
    if not names:
        st.info(t("لا توجد مشاريع حاليًا. يمكن إضافة مشروع جديد من زر إضافة مشروع.", "No projects yet. Use Add Project to create one."))
        return

    cols = st.columns(3)
    for idx, name in enumerate(names):
        proj = month_obj["projects"][name]
        net = _project_net(proj)
        label = (
            f"{name}\n"
            f"{t('النوع', 'Type')}: {_project_type_label(proj.get('project_type', 'أخرى'), is_en)}\n"
            f"{t('الصافي', 'Net')}: {net:,.0f} {currency_view}"
        )
        with cols[idx % 3]:
            if st.button(label, key=f"project_card_{idx}", use_container_width=True):
                month_obj["selected_project"] = name
                _sync_legacy_fields(month_obj)
                st.rerun()

    selected_name = month_obj.get("selected_project", "")
    if selected_name not in month_obj["projects"]:
        selected_name = names[0]
        month_obj["selected_project"] = selected_name

    selected_project = month_obj["projects"][selected_name]
    _ensure_project_defaults(selected_project)

    st.markdown("---")
    st.subheader(t(f"تفاصيل المشروع: {selected_name}", f"Project Details: {selected_name}"))
    type_label = _project_type_label(selected_project.get("project_type", "أخرى"), is_en)
    st.caption(t(f"نوع المشروع: {type_label}", f"Project type: {type_label}"))

    with st.expander(t("إدارة المشروع", "Manage Project"), expanded=False):
        rename_value = st.text_input(
            t("تعديل اسم المشروع", "Rename Project"),
            value=selected_name,
            key=f"rename_{selected_name}",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("حفظ الاسم", "Save Name"), key=f"save_name_{selected_name}", use_container_width=True):
                ok, reason = _rename_project(month_obj, selected_name, rename_value)
                if ok:
                    st.success(t("تم تعديل اسم المشروع.", "Project name updated."))
                    st.rerun()
                if reason == "exists":
                    st.warning(t("هذا الاسم موجود مسبقاً.", "This name already exists."))
                elif reason == "empty":
                    st.warning(t("الاسم لا يمكن أن يكون فارغاً.", "Name cannot be empty."))

        with c2:
            confirm_delete = st.checkbox(t("تأكيد حذف المشروع", "Confirm project deletion"), key=f"confirm_del_{selected_name}")
            if st.button(t("حذف المشروع", "Delete Project"), key=f"delete_proj_{selected_name}", use_container_width=True):
                if not confirm_delete:
                    st.warning(t("يرجى تفعيل تأكيد الحذف أولًا.", "Enable delete confirmation first."))
                else:
                    _delete_project(month_obj, selected_name)
                    st.success(t("تم حذف المشروع.", "Project deleted."))
                    st.rerun()

    with st.expander(t("بيانات المشروع", "Project Details"), expanded=False):
        selected_project["project_type"] = st.selectbox(
            t("نوع المشروع", "Project Type"),
            DEFAULT_PROJECT_TYPES,
            index=DEFAULT_PROJECT_TYPES.index(selected_project.get("project_type", "أخرى"))
            if selected_project.get("project_type", "أخرى") in DEFAULT_PROJECT_TYPES
            else len(DEFAULT_PROJECT_TYPES) - 1,
            format_func=lambda x: _project_type_label(x, is_en),
            key=f"project_type_{selected_name}",
        )

        d1, d2 = st.columns(2)
        with d1:
            selected_project["expected_income"] = st.number_input(
                t("الدخل المتوقع", "Expected Income"),
                min_value=0.0,
                step=10.0,
                value=float(selected_project.get("expected_income", 0.0)),
            )
        with d2:
            selected_project["expected_expense"] = st.number_input(
                t("المصاريف المتوقعة", "Expected Expenses"),
                min_value=0.0,
                step=10.0,
                value=float(selected_project.get("expected_expense", 0.0)),
            )
        selected_project["note"] = st.text_area(t("ملاحظات المشروع", "Project Notes"), value=selected_project.get("note", ""))

        st.markdown("---")
        st.markdown(f"**{t('إعداد ضريبة المشروع', 'Project Tax Settings')}**")
        selected_project["tax_override_enabled"] = st.checkbox(
            t("تفعيل إعداد ضريبي خاص لهذا المشروع", "Use project-specific tax settings"),
            value=bool(selected_project.get("tax_override_enabled", False)),
            key=f"project_tax_override_{selected_name}",
        )

        if selected_project["tax_override_enabled"]:
            tx1, tx2 = st.columns(2)
            with tx1:
                selected_project["tax_rate"] = st.number_input(
                    t("نسبة الضريبة للمشروع %", "Project Tax Rate %"),
                    min_value=0.0,
                    max_value=100.0,
                    step=0.5,
                    format="%.3f",
                    value=float(selected_project.get("tax_rate", default_tax_rate)),
                    key=f"project_tax_rate_{selected_name}",
                )
            with tx2:
                selected_project["prices_include_tax"] = st.checkbox(
                    t("أسعار المشروع تشمل الضريبة", "Prices include tax"),
                    value=bool(selected_project.get("prices_include_tax", default_prices_include_tax)),
                    key=f"project_include_tax_{selected_name}",
                )
            st.caption(t("فواتير هذا المشروع تستخدم هذه القيم افتراضياً.", "Project invoices use these values by default."))
        else:
            st.caption(
                t(
                    f"هذا المشروع يستخدم الإعداد العام: {default_tax_rate:.3f}% | شامل الضريبة: {'نعم' if default_prices_include_tax else 'لا'}",
                    f"This project uses global settings: {default_tax_rate:.3f}% | includes tax: {'yes' if default_prices_include_tax else 'no'}",
                )
            )

    with st.expander(t("إضافة معاملة مشروع", "Add Project Transaction"), expanded=False):
        with st.form("add_project_tx"):
            t1, t2 = st.columns(2)
            with t1:
                p_date = st.date_input(t("التاريخ", "Date"), value=datetime.today())
                p_type_lbl = st.selectbox(t("النوع", "Type"), [t("دخل", "Income"), t("مصروف", "Expense")])
            with t2:
                p_amount = st.number_input(t("المبلغ", "Amount"), min_value=0.0, step=5.0)
                p_category = st.text_input(t("التصنيف", "Category"), value=t("عام", "General"))
    
            p_type_value = "دخل" if p_type_lbl == t("دخل", "Income") else "مصروف"
            p_tax_code = ""
            if p_type_value == "مصروف" and tax_codes:
                p_tax_code = st.selectbox(
                    t("التصنيف الضريبي", "Tax Classification"),
                    tax_codes,
                    index=tax_codes.index(default_expense_tax_code) if default_expense_tax_code in tax_codes else 0,
                    format_func=lambda code: tax_label_by_code.get(code, code),
                )
    
            funded_from_personal = st.checkbox(
                t("هذا المصروف مدفوع من الحساب الشخصي", "This expense is funded from personal account"),
                value=False,
            )
            p_note = st.text_input(t("ملاحظة", "Note"), value="")
            save_btn = st.form_submit_button(t("حفظ المعاملة", "Save Transaction"), use_container_width=True)

    if save_btn and p_amount > 0:
        tx_type = p_type_value
        tx_payload = {
            "date": p_date.strftime("%Y-%m-%d"),
            "type": tx_type,
            "amount": float(p_amount),
            "category": p_category or t("عام", "General"),
            "note": p_note,
            "project_name": selected_name,
            "project_type": selected_project.get("project_type", "أخرى"),
            "funded_from_personal": bool(funded_from_personal) if tx_type == "مصروف" else False,
        }
        if tx_type == "مصروف" and p_tax_code:
            tx_payload["tax_tag_code"] = p_tax_code
        selected_project["transactions"].append(tx_payload)
        _sync_legacy_fields(month_obj)
        st.success(t("تمت إضافة معاملة المشروع.", "Project transaction saved."))
        st.rerun()

    selected_txs = selected_project["transactions"]
    actual_income = sum(float(x.get("amount", 0.0)) for x in selected_txs if x.get("type") == "دخل")
    actual_expense = sum(float(x.get("amount", 0.0)) for x in selected_txs if x.get("type") == "مصروف")
    actual_net = actual_income - actual_expense
    expected_net = float(selected_project.get("expected_income", 0.0)) - float(selected_project.get("expected_expense", 0.0))

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(t("صافي المشروع الحالي", "Selected Project Net"), f"{actual_net:,.0f} {currency_view}")
    with m2:
        st.metric(t("الصافي المتوقع", "Expected Net"), f"{expected_net:,.0f} {currency_view}")
    with m3:
        st.metric(t("عدد المعاملات", "Transactions Count"), f"{len(selected_txs)}")

    _sync_legacy_fields(month_obj)
    all_txs = month_obj.get("project_transactions", [])
    all_income = sum(float(x.get("amount", 0.0)) for x in all_txs if x.get("type") == "دخل")
    all_expense = sum(float(x.get("amount", 0.0)) for x in all_txs if x.get("type") == "مصروف")
    all_net = all_income - all_expense
    personal_support = sum(
        float(x.get("amount", 0.0))
        for x in all_txs
        if x.get("type") == "مصروف" and x.get("funded_from_personal")
    )
    active_projects_count = sum(1 for proj in month_obj.get("projects", {}).values() if proj.get("transactions"))

    st.markdown(f"### {t('ملخص هذا الشهر', 'This Month Summary')}")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.metric(t("صافي كل المشاريع", "All Projects Net"), f"{all_net:,.0f} {currency_view}")
    with a2:
        st.metric(t("دعم من الحساب الشخصي", "Funded From Personal"), f"{personal_support:,.0f} {currency_view}", delta_color="inverse")
    with a3:
        st.metric(t("المشاريع النشطة", "Active Projects"), f"{active_projects_count}")

    st.markdown(f"### {t('سجل معاملات المشروع', 'Project Transactions')}")
    if not selected_txs:
        st.info(t("لا توجد حركات لهذا المشروع في هذا الشهر.", "No transactions for this project this month."))
    else:
        df_p = pd.DataFrame(selected_txs).copy()
        if is_en and "project_type" in df_p.columns:
            df_p["project_type"] = df_p["project_type"].apply(lambda x: _project_type_label(x, True))
        df_p.insert(0, "رقم", range(1, len(df_p) + 1))
        df_p["حذف"] = False

        edited = st.data_editor(
            df_p.rename(
                columns={
                    "date": t("التاريخ", "Date"),
                    "type": t("النوع", "Type"),
                    "amount": t("المبلغ", "Amount"),
                    "category": t("التصنيف", "Category"),
                    "note": t("ملاحظة", "Note"),
                    "project_name": t("المشروع", "Project"),
                    "project_type": t("نوع المشروع", "Project Type"),
                    "funded_from_personal": t("من الحساب الشخصي", "From Personal"),
                }
            ),
            use_container_width=True,
            hide_index=True,
            disabled=[
                "رقم",
                t("التاريخ", "Date"),
                t("النوع", "Type"),
                t("المبلغ", "Amount"),
                t("التصنيف", "Category"),
                t("ملاحظة", "Note"),
                t("المشروع", "Project"),
                t("نوع المشروع", "Project Type"),
                t("من الحساب الشخصي", "From Personal"),
            ],
            key="project_tx_editor",
        )

        selected_rows = edited[edited["حذف"]]["رقم"].tolist()
        if st.button(t("حذف المحدد", "Delete Selected"), use_container_width=True):
            if not selected_rows:
                st.warning(t("يرجى اختيار معاملة واحدة على الأقل.", "Select at least one transaction."))
            else:
                for row_num in sorted(selected_rows, reverse=True):
                    tx_index = int(row_num) - 1
                    if 0 <= tx_index < len(selected_txs):
                        selected_txs.pop(tx_index)
                _sync_legacy_fields(month_obj)
                st.success(t(f"تم حذف {len(selected_rows)} معاملة.", f"Deleted {len(selected_rows)} transaction(s)."))
                st.rerun()

    with st.expander(t("مقارنة المشاريع", "Projects Comparison"), expanded=False):
        rank_rows = []
        for name, proj in month_obj.get("projects", {}).items():
            txs = proj.get("transactions", [])
            rank_rows.append(
                {
                    t("المشروع", "Project"): name,
                    t("النوع", "Type"): _project_type_label(proj.get("project_type", "أخرى"), is_en),
                    t("عدد المعاملات", "Transactions"): len(txs),
                    t("الصافي", "Net"): _project_net(proj),
                }
            )

        df_rank = pd.DataFrame(rank_rows)
        df_rank = df_rank.sort_values(by=t("الصافي", "Net"), ascending=False).reset_index(drop=True)
        df_rank.insert(0, t("الترتيب", "Rank"), range(1, len(df_rank) + 1))

        strongest = df_rank.iloc[0]
        weakest = df_rank.iloc[-1]

        r1, r2 = st.columns(2)
        with r1:
            st.metric(
                t("أقوى مشروع", "Strongest Project"),
                f"{strongest[t('المشروع', 'Project')]} ({strongest[t('النوع', 'Type')]})",
                delta=f"{float(strongest[t('الصافي', 'Net')]):,.0f} {currency_view}",
            )
        with r2:
            st.metric(
                t("أضعف مشروع", "Weakest Project"),
                f"{weakest[t('المشروع', 'Project')]} ({weakest[t('النوع', 'Type')]})",
                delta=f"{float(weakest[t('الصافي', 'Net')]):,.0f} {currency_view}",
                delta_color="inverse",
            )

        selected_rank = df_rank[df_rank[t("المشروع", "Project")] == selected_name]
        if not selected_rank.empty:
            row = selected_rank.iloc[0]
            st.caption(
                t(
                    f"ترتيب المشروع الحالي: {int(row[t('الترتيب', 'Rank')])} من {len(df_rank)}.",
                    f"Current project rank: {int(row[t('الترتيب', 'Rank')])} of {len(df_rank)}.",
                )
            )

        st.dataframe(df_rank, use_container_width=True, hide_index=True)
