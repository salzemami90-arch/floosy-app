from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config_floosy import arabic_months, english_months
from models.tax_profile import TaxProfile
from repositories.session_repo import SessionStateRepository
from services.tax_export_service import TaxExportService
from services.invoice_tax_service import InvoiceTaxService
from services.tax_readiness import ensure_tax_state
from services.tax_strategy_service import TaxStrategyService


STATUS_ORDER = ["draft", "sent", "paid", "cancelled"]


def _status_label(status: str, is_en: bool) -> str:
    labels = {
        "draft": ("مسودة", "Draft"),
        "sent": ("مرسلة", "Sent"),
        "paid": ("مدفوعة", "Paid"),
        "cancelled": ("ملغاة", "Cancelled"),
    }
    ar, en = labels.get(status, labels["draft"])
    return en if is_en else ar


def _currency_view(symbol: str, is_en: bool) -> str:
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    return currency_map_en.get(symbol, symbol) if is_en else symbol


def _safe_float(raw_value, fallback=0.0) -> float:
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return float(fallback)


def _parse_month_key(month_key: str) -> tuple[int, int] | None:
    if not month_key or "-" not in month_key:
        return None
    year_txt, month_name = month_key.split("-", 1)
    if month_name not in arabic_months:
        return None
    try:
        year_value = int(year_txt)
    except ValueError:
        return None
    return year_value, arabic_months.index(month_name) + 1


def _find_project_obj(project_name: str, month_key: str) -> dict | None:
    if not project_name:
        return None

    project_data = st.session_state.get("project_data", {})
    if not isinstance(project_data, dict):
        return None

    current_month_obj = project_data.get(month_key, {})
    if isinstance(current_month_obj, dict):
        projects = current_month_obj.get("projects", {})
        if isinstance(projects, dict) and isinstance(projects.get(project_name), dict):
            return projects[project_name]

    ranked_months = []
    for mk, mobj in project_data.items():
        if not isinstance(mobj, dict):
            continue
        parsed = _parse_month_key(mk)
        if not parsed:
            continue
        ranked_months.append((parsed[0], parsed[1], mk))
    ranked_months.sort(reverse=True)

    for _, _, mk in ranked_months:
        mobj = project_data.get(mk, {})
        projects = mobj.get("projects", {}) if isinstance(mobj, dict) else {}
        if isinstance(projects, dict) and isinstance(projects.get(project_name), dict):
            return projects[project_name]

    return None


def _resolve_tax_defaults(profile, month_key: str, project_name: str) -> dict:
    default_rate = max(0.0, _safe_float(getattr(profile, "default_tax_rate", 0.0), 0.0))
    default_include = bool(getattr(profile, "prices_include_tax", False))

    project_obj = _find_project_obj(project_name, month_key)
    if not project_obj:
        return {
            "tax_rate": default_rate,
            "prices_include_tax": default_include,
            "source": "default",
            "project_found": False,
        }

    if bool(project_obj.get("tax_override_enabled", False)):
        return {
            "tax_rate": max(0.0, _safe_float(project_obj.get("tax_rate", default_rate), default_rate)),
            "prices_include_tax": bool(project_obj.get("prices_include_tax", default_include)),
            "source": "project",
            "project_found": True,
        }

    return {
        "tax_rate": default_rate,
        "prices_include_tax": default_include,
        "source": "default",
        "project_found": True,
    }


def _inherited_source_caption(t, inherited: dict) -> str:
    if inherited.get("source") == "project":
        return t("المصدر: إعداد ضريبي خاص بالمشروع.", "Source: Project-level tax override.")
    return t("المصدر: الإعداد العام.", "Source: Global default settings.")


def _amount_label(t, prices_include_tax: bool) -> str:
    if prices_include_tax:
        return t("المبلغ شامل الضريبة", "Amount (Tax Included)")
    return t("المبلغ قبل الضريبة", "Amount Before Tax")


def _tax_source_label(source: str, t) -> str:
    key = str(source or "global").strip().lower()
    if key == "manual":
        return t("يدوي", "Manual")
    if key == "project":
        return t("من المشروع", "From Project")
    return t("عام", "Global")


def _render_tax_settings_panel(t, repo: SessionStateRepository, settings: dict, is_en: bool) -> None:
    ensure_tax_state(st.session_state)
    tax_profile = dict(st.session_state.get("tax_profile", {}))
    tax_profile["regime"] = str(tax_profile.get("regime", "standard") or "standard")
    tax_profile["tax_name"] = str(tax_profile.get("tax_name", "VAT") or "VAT").strip() or "VAT"
    tax_profile["tax_basis_mode"] = TaxStrategyService.normalize_basis_mode(tax_profile.get("tax_basis_mode", "invoice"))

    basis_options = [("cash", t("نقدي", "Cash")), ("accrual", t("استحقاق", "Accrual"))]
    frequency_options = [
        ("monthly", t("شهري", "Monthly")),
        ("quarterly", t("ربع سنوي", "Quarterly")),
        ("yearly", t("سنوي", "Yearly")),
    ]
    tax_basis_options = [
        ("invoice", TaxStrategyService.basis_label("invoice", is_en=is_en)),
        ("net_profit", TaxStrategyService.basis_label("net_profit", is_en=is_en)),
    ]

    st.markdown("---")
    header_col, close_col = st.columns([6, 1])
    with header_col:
        st.subheader(t("إعدادات الضريبة", "Tax Settings"))
    with close_col:
        if st.button("✕", key="tax_settings_close", help=t("إغلاق", "Close")):
            st.session_state["tax_settings_open"] = False
            st.rerun()

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(44,95,135,0.10), rgba(63,163,122,0.12));
            border: 1px solid rgba(44,95,135,0.14);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 6px 0 14px 0;
        ">
            <div style="font-size:0.82rem;font-weight:700;color:#2c5f87;margin-bottom:4px;">
                {t("لوحة داخلية", "Inline Panel")}
            </div>
            <div style="font-size:1.08rem;font-weight:800;color:#163247;margin-bottom:6px;">
                {t("إعدادات الضريبة داخل صفحة الفواتير", "Tax settings inside the invoice page")}
            </div>
            <div style="font-size:0.92rem;color:#445160;line-height:1.65;">
                {t(
                    "حددي الضريبة بالطريقة اللي تناسبك: النسبة، طريقة الحساب، وبيانات النشاط.",
                    "Set tax your way: rate, calculation method, and business details.",
                )}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric(
            t("الحالة", "Status"),
            t("مفعل", "Enabled") if bool(tax_profile.get("tax_mode_enabled", False)) else t("غير مفعل", "Disabled"),
        )
    with s2:
        st.metric(t("اسم الضريبة", "Tax Name"), tax_profile["tax_name"])
    with s3:
        st.metric(
            t("الأساس العام", "General Basis"),
            TaxStrategyService.basis_label(tax_profile["tax_basis_mode"], is_en=is_en),
        )
    with s4:
        st.metric(t("النسبة العامة", "Default Rate"), f"{float(tax_profile.get('default_tax_rate', 0.0) or 0.0):.3f}%")

    with st.form("tax_settings_form", clear_on_submit=False):
        st.markdown(f"#### {t('منطق الضريبة', 'Tax Logic')}")
        st.caption(
            t(
                "يرجى تحديد الاسم والنسبة وطريقة الحساب.",
                "Set the name, rate, and calculation method.",
            )
        )
        logic_left, logic_right = st.columns(2)
        with logic_left:
            tax_mode_enabled = st.checkbox(
                t("تفعيل الوضع الضريبي", "Enable Tax Mode"),
                value=bool(tax_profile.get("tax_mode_enabled", False)),
                key="tax_mode_enabled_page",
            )
            tax_name = st.text_input(
                t("اسم الضريبة", "Tax Name"),
                value=tax_profile["tax_name"],
                key="tax_name_page",
            ).strip() or "VAT"
            default_tax_rate = float(
                st.number_input(
                    t("نسبة الضريبة الافتراضية (%)", "Default Tax Rate (%)"),
                    min_value=0.0,
                    max_value=100.0,
                    value=float(tax_profile.get("default_tax_rate", 0.0) or 0.0),
                    step=0.5,
                    format="%.3f",
                    key="tax_default_rate_page",
                )
            )
        with logic_right:
            current_tax_basis = TaxStrategyService.normalize_basis_mode(tax_profile.get("tax_basis_mode", "invoice"))
            tax_basis_keys = [item[0] for item in tax_basis_options]
            tax_basis_labels = [item[1] for item in tax_basis_options]
            tax_basis_index = tax_basis_keys.index(current_tax_basis) if current_tax_basis in tax_basis_keys else 0
            selected_tax_basis_label = st.selectbox(
                t("طريقة حساب الضريبة", "Tax Calculation Method"),
                tax_basis_labels,
                index=tax_basis_index,
                key="tax_basis_mode_page",
            )
            tax_basis_mode = tax_basis_keys[tax_basis_labels.index(selected_tax_basis_label)]
            prices_include_tax = st.checkbox(
                t("المبالغ المدخلة في الفاتورة تشمل الضريبة", "Invoice Entry Amount Includes Tax"),
                value=bool(tax_profile.get("prices_include_tax", False)),
                key="tax_prices_include_page",
            )

        if tax_basis_mode == "net_profit":
            st.info(
                t(
                    "الحساب هنا يكون من صافي الربح الشهري (إذا كان موجب).",
                    "Calculation uses monthly net profit (when positive).",
                )
            )
        else:
            st.info(
                t(
                    "الحساب هنا يكون من الفواتير/المبيعات. وإذا المبلغ شامل ضريبة، النظام يستخرجها من داخله.",
                    "Calculation uses invoices/sales. If amount includes tax, it is extracted from within.",
                )
            )

        st.markdown("---")
        st.markdown(f"#### {t('التقرير والهوية', 'Reporting and Identity')}")
        st.caption(
            t(
                "حددي نوع التقرير وبيانات النشاط.",
                "Set reporting type and business details.",
            )
        )
        report_left, report_right = st.columns(2)
        with report_left:
            current_basis = str(tax_profile.get("reporting_basis", "cash") or "cash")
            basis_keys = [item[0] for item in basis_options]
            basis_labels = [item[1] for item in basis_options]
            basis_index = basis_keys.index(current_basis) if current_basis in basis_keys else 0
            selected_basis_label = st.selectbox(
                t("نوع التقرير", "Report Type"),
                basis_labels,
                index=basis_index,
                key="tax_reporting_basis_page",
            )
            reporting_basis = basis_keys[basis_labels.index(selected_basis_label)]

            current_freq = str(tax_profile.get("filing_frequency", "monthly") or "monthly")
            freq_keys = [item[0] for item in frequency_options]
            freq_labels = [item[1] for item in frequency_options]
            freq_index = freq_keys.index(current_freq) if current_freq in freq_keys else 0
            selected_freq_label = st.selectbox(
                t("وتيرة مراجعة التقرير", "Review Frequency"),
                freq_labels,
                index=freq_index,
                key="tax_filing_frequency_page",
            )
            filing_frequency = freq_keys[freq_labels.index(selected_freq_label)]

            country_code = (
                st.text_input(
                    t("رمز الدولة الضريبي", "Tax Country Code"),
                    value=str(tax_profile.get("country_code", "KW") or "KW"),
                    key="tax_country_code_page",
                )
                .strip()
                .upper()
            )

        with report_right:
            registration_number = st.text_input(
                t("الرقم الضريبي", "Tax Registration Number"),
                value=str(tax_profile.get("registration_number", "") or ""),
                key="tax_registration_number_page",
            )
            business_name = st.text_input(
                t("الاسم التجاري الضريبي", "Tax Business Name"),
                value=str(tax_profile.get("business_name", settings.get("name", "")) or ""),
                key="tax_business_name_page",
            )
            contact_email = st.text_input(
                t("إيميل الفوترة/الضريبة", "Billing/Tax Email"),
                value=str(tax_profile.get("contact_email", "") or ""),
                key="tax_contact_email_page",
            )

        notes = st.text_area(
            t("ملاحظات ضريبية", "Tax Notes"),
            value=str(tax_profile.get("notes", "") or ""),
            key="tax_notes_page",
        )

        save_settings = st.form_submit_button(
            t("حفظ الإعدادات الضريبية", "Save Tax Settings"),
            use_container_width=True,
        )

    if save_settings:
        updated_profile = {
            **tax_profile,
            "tax_mode_enabled": bool(tax_mode_enabled),
            "tax_name": tax_name,
            "default_tax_rate": float(default_tax_rate),
            "tax_basis_mode": tax_basis_mode,
            "prices_include_tax": bool(prices_include_tax),
            "reporting_basis": reporting_basis,
            "filing_frequency": filing_frequency,
            "country_code": country_code,
            "registration_number": registration_number,
            "business_name": business_name,
            "contact_email": contact_email,
            "notes": notes,
        }
        repo.save_tax_profile(TaxProfile.from_dict(updated_profile))
        st.session_state["tax_settings_saved_notice"] = t(
            "تم حفظ إعدادات الضريبة.",
            "Tax settings saved.",
        )
        st.rerun()

    st.markdown(
        f"""
        <div style="
            background:#f8fbfd;
            border:1px dashed rgba(44,95,135,0.22);
            border-radius:14px;
            padding:12px 14px;
            margin-top:10px;
            color:#43505c;
            line-height:1.7;
            font-size:0.92rem;
        ">
            {t(
                "يُستخدم الإعداد العام كافتراضي. ويمكن أن ترث الفاتورة إعداد المشروع أو الإعداد العام. أي تغيير هنا لا يحدّث الفواتير السابقة.",
                "Global settings are defaults. Invoices can inherit from project or global settings. Changes here do not update previous invoices.",
            )}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(month_key: str, month: str, year: int) -> None:
    settings = st.session_state.settings
    is_en = settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month

    st.session_state.setdefault("tax_settings_open", False)
    save_notice = st.session_state.pop("tax_settings_saved_notice", "")

    ensure_tax_state(st.session_state)
    repo = SessionStateRepository()
    service = InvoiceTaxService(repo)
    default_currency = settings.get("default_currency", "د.ك")
    currency_symbol = default_currency.split(" - ")[0] if " - " in default_currency else default_currency
    currency_view = _currency_view(currency_symbol, is_en)

    st.markdown(
        """
        <style>
        div.st-key-tax_settings_toggle_top button {
            min-height: 42px;
            border-radius: 12px;
            padding: 0.45rem 0.9rem !important;
            font-size: 14px;
            line-height: 1.2;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
        }
        div.st-key-tax_settings_close button {
            width: 36px;
            height: 36px;
            min-height: 36px;
            border-radius: 10px;
            padding: 0 !important;
            font-size: 18px;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    title_col, action_col = st.columns([5, 2])
    with title_col:
        st.title(t("الفواتير والضرائب", "Invoices and Tax"))
        st.caption(
            t(
                f"إضافة الفواتير ومراجعة الضريبة لشهر {month_display} {year}",
                f"Add invoices and review tax for {month_display} {year}",
            )
        )
    with action_col:
        if st.button(
            t("إعدادات الضريبة", "Tax Settings"),
            key="tax_settings_toggle_top",
            help=t("فتح أو إغلاق إعدادات الضريبة", "Open or close tax settings"),
            use_container_width=True,
        ):
            st.session_state["tax_settings_open"] = not bool(st.session_state.get("tax_settings_open", False))
            st.rerun()

    if save_notice:
        st.success(save_notice)

    if st.session_state.get("tax_settings_open", False):
        _render_tax_settings_panel(t, repo, settings, is_en)

    profile = repo.get_tax_profile()

    if not bool(profile.tax_mode_enabled):
        st.warning(
            t(
                "الوضع الضريبي غير مفعّل. تعتمد الفواتير على الإعداد العام أو المشروع، والتعديل اليدوي غير متاح.",
                "Tax mode is off. Invoices use global or project defaults, and manual per-invoice editing is unavailable.",
            )
        )

    st.caption(
        t(
            "أي تغيير على إعدادات الضريبة يطبّق على الفواتير الجديدة فقط.",
            "Tax setting changes apply to new invoices only.",
        )
    )

    report = service.monthly_tax_report_from_month_key(
        month_key=month_key,
        currency=currency_symbol,
        basis=profile.reporting_basis,
    )
    transactions = repo.list_transactions(month_key)
    tax_name = str(getattr(profile, "tax_name", "VAT") or "VAT").strip() or "VAT"
    tax_basis_mode = TaxStrategyService.normalize_basis_mode(getattr(profile, "tax_basis_mode", "invoice"))
    tax_basis_label = TaxStrategyService.basis_label(tax_basis_mode, is_en=is_en)
    estimate = TaxStrategyService.estimate_month_tax(
        profile=profile,
        transactions=transactions,
        invoice_report=report,
        currency=currency_symbol,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("عدد الفواتير", "Invoices"), str(report["counts"].get("total_invoices", 0)))
    with c2:
        st.metric(t("الإجمالي قبل الضريبة", "Subtotal"), f"{report['totals'].get('subtotal', 0.0):,.2f} {currency_view}")
    with c3:
        st.metric(t("الضريبة", "Tax"), f"{report['totals'].get('tax', 0.0):,.2f} {currency_view}")
    with c4:
        st.metric(t("الإجمالي النهائي", "Total"), f"{report['totals'].get('total', 0.0):,.2f} {currency_view}")

    st.caption(
        t(
            f"أساس التقرير: {'نقدي' if report.get('basis') == 'cash' else 'استحقاق'} | مفتوح غير مسدد: {report['totals'].get('outstanding_open_total', 0.0):,.2f} {currency_view}",
            f"Basis: {report.get('basis', 'cash').title()} | Open outstanding: {report['totals'].get('outstanding_open_total', 0.0):,.2f} {currency_view}",
        )
    )

    projects = [p.name for p in repo.list_projects()]
    project_choices = [t("بدون مشروع", "No Project")] + projects
    invoices = repo.list_invoices()

    tab_summary, tab_add, tab_manage, tab_export = st.tabs(
        [
            t("الملخص", "Overview"),
            t("إضافة فاتورة", "Add Invoice"),
            t("إدارة الفواتير", "Manage Invoices"),
            t("التصدير", "Export"),
        ]
    )

    with tab_summary:
        st.subheader(t("ملخص الضريبة لهذا الشهر", "Tax Summary This Month"))
        b1, b2, b3 = st.columns(3)
        with b1:
            st.metric(t("اسم الضريبة", "Tax Name"), tax_name)
        with b2:
            st.metric(t("الأساس العام", "General Basis"), tax_basis_label)
        with b3:
            st.metric(
                t("التقدير الشهري", "Monthly Estimate"),
                f"{estimate['estimated_tax']:,.2f} {currency_view}",
                delta=f"{estimate['basis_amount']:,.2f} {currency_view}",
                delta_color="off",
            )

        if tax_basis_mode == "net_profit":
            st.info(
                t(
                    f"الاحتساب الحالي على صافي الربح: {estimate['income']:,.2f} دخل - {estimate['expense']:,.2f} مصروف = {estimate['net_profit']:,.2f} {currency_view}.",
                    f"Current estimate uses net profit: {estimate['income']:,.2f} income - {estimate['expense']:,.2f} expense = {estimate['net_profit']:,.2f} {currency_view}.",
                )
            )
        else:
            invoice_base_label = (
                t("الإجمالي النهائي", "Invoice Total")
                if bool(getattr(profile, "prices_include_tax", False))
                else t("الإجمالي قبل الضريبة", "Invoice Subtotal")
            )
            st.info(
                t(
                    f"الاحتساب الحالي على الفواتير/المبيعات. الأساس المستخدم: {invoice_base_label} = {estimate['basis_amount']:,.2f} {currency_view}.",
                    f"Current estimate uses invoices/sales. Base used: {invoice_base_label} = {estimate['basis_amount']:,.2f} {currency_view}.",
                )
            )

        if report["counts"].get("overdue_open", 0) > 0:
            st.warning(
                t(
                    f"يوجد {report['counts']['overdue_open']} فاتورة مفتوحة متأخرة الاستحقاق.",
                    f"There are {report['counts']['overdue_open']} open overdue invoice(s).",
                )
            )

        with st.expander(t("تفاصيل طريقة الحساب", "Calculation Details"), expanded=False):
            st.write(
                t(
                    "الإعداد العام هو الأساس. وإذا ارتبط المشروع بإعداد ضريبي خاص، ترث الفاتورة هذا الإعداد. لا يتاح التعديل اليدوي إلا عند تفعيل الوضع الضريبي.",
                    "Global settings are the default. If a project has its own tax setup, the invoice inherits it. Manual override is available only when tax mode is enabled.",
                )
            )
            st.write(
                t(
                    "إذا كان المبلغ شامل الضريبة، النظام يستخرج الضريبة من داخل المبلغ تلقائياً.",
                    "If the amount already includes tax, the system extracts the tax from within that amount automatically.",
                )
            )

    with tab_add:
        st.subheader(t("إضافة فاتورة جديدة", "Add a New Invoice"))
        with st.form("tax_add_invoice_form", clear_on_submit=True):
            customer_name = st.text_input(t("اسم العميل", "Customer Name"))
            customer_tax_no = st.text_input(t("رقم ضريبي للعميل (اختياري)", "Customer Tax No (Optional)"))

            c_add1, c_add2, c_add3 = st.columns(3)
            with c_add1:
                issue_date = st.date_input(t("تاريخ الإصدار", "Issue Date"), value=date.today())
            with c_add2:
                has_due_date = st.checkbox(t("تحديد تاريخ استحقاق", "Set Due Date"), value=False)
            with c_add3:
                due_date_value = st.date_input(t("تاريخ الاستحقاق", "Due Date"), value=date.today()) if has_due_date else None

            linked_project_label = st.selectbox(t("المشروع المرتبط", "Linked Project"), project_choices, index=0)
            linked_project = "" if linked_project_label == project_choices[0] else linked_project_label

            inherited = _resolve_tax_defaults(profile, month_key, linked_project)
            st.caption(_inherited_source_caption(t, inherited))

            manual_override = False
            if bool(profile.tax_mode_enabled):
                manual_override = st.checkbox(
                    t("تعديل الضريبة لهذه الفاتورة يدويًا", "Manual Tax Edit For This Invoice"),
                    value=False,
                )
            else:
                st.caption(t("التعديل اليدوي مقفل لأن الوضع الضريبي غير مفعل.", "Manual edit is locked while tax mode is off."))

            effective_tax_rate = float(inherited["tax_rate"])
            effective_include_tax = bool(inherited["prices_include_tax"])

            if manual_override:
                c_tax1, c_tax2 = st.columns(2)
                with c_tax1:
                    effective_tax_rate = st.number_input(
                        t("نسبة الضريبة لهذه الفاتورة %", "Tax Rate For This Invoice %"),
                        min_value=0.0,
                        max_value=100.0,
                        value=float(inherited["tax_rate"]),
                        step=0.5,
                        format="%.3f",
                    )
                with c_tax2:
                    effective_include_tax = st.checkbox(
                        t("المبلغ شامل ضريبة", "Amount Includes Tax"),
                        value=bool(inherited["prices_include_tax"]),
                    )
            else:
                st.caption(
                    t(
                        f"النسبة المستخدمة: {effective_tax_rate:.3f}% | شامل الضريبة: {'نعم' if effective_include_tax else 'لا'}",
                        f"Tax rate: {effective_tax_rate:.3f}% | Amount includes tax: {'yes' if effective_include_tax else 'no'}",
                    )
                )

            amount_value = st.number_input(
                _amount_label(t, effective_include_tax),
                min_value=0.0,
                value=0.0,
                step=10.0,
            )

            status_labels = [_status_label(key, is_en) for key in STATUS_ORDER]
            status_selected_label = st.selectbox(t("حالة الفاتورة", "Invoice Status"), status_labels, index=0)
            status_selected = STATUS_ORDER[status_labels.index(status_selected_label)]

            notes = st.text_area(t("ملاحظات", "Notes"))
            submitted = st.form_submit_button(t("حفظ الفاتورة", "Save Invoice"), use_container_width=True)

        if submitted:
            validation_errors = []
            if not customer_name.strip():
                validation_errors.append(
                    t(
                        "يرجى إدخال اسم العميل.",
                        "Please enter a customer name.",
                    )
                )
            if float(amount_value) <= 0:
                validation_errors.append(
                    t(
                        "يرجى إدخال مبلغ أكبر من صفر.",
                        "Please enter an amount greater than zero.",
                    )
                )

            if validation_errors:
                for message in validation_errors:
                    st.error(message)
            else:
                payload = {
                    "customer_name": customer_name,
                    "customer_tax_no": customer_tax_no,
                    "issue_date": issue_date,
                    "due_date": due_date_value if has_due_date else None,
                    "subtotal": float(amount_value),
                    "tax_rate": float(effective_tax_rate),
                    "prices_include_tax": bool(effective_include_tax),
                    "tax_source": "manual" if manual_override else ("project" if inherited.get("source") == "project" else "global"),
                    "status": status_selected,
                    "linked_project": linked_project,
                    "currency": currency_symbol,
                    "notes": notes,
                }
                created = service.create_invoice(payload)
                st.success(
                    t(
                        f"تم حفظ الفاتورة {created.invoice_number}.",
                        f"Invoice {created.invoice_number} saved.",
                    )
                )
                st.rerun()

    with tab_manage:
        st.subheader(t("الفواتير الحالية", "Current Invoices"))
        if not invoices:
            st.info(
                t(
                    "لا توجد فواتير حاليًا. يمكن إضافة أول فاتورة من تبويب إضافة فاتورة.",
                    "No invoices yet. Add the first invoice from the Add Invoice tab.",
                )
            )
        else:
            rows = []
            for idx, inv in enumerate(invoices):
                rows.append(
                    {
                        "idx": idx,
                        t("الرقم", "Number"): inv.invoice_number,
                        t("العميل", "Customer"): inv.customer_name,
                        t("المشروع", "Project"): inv.linked_project or t("بدون", "None"),
                        t("الحالة", "Status"): _status_label(inv.status, is_en),
                        t("مصدر الضريبة", "Tax Source"): _tax_source_label(getattr(inv, "tax_source", "global"), t),
                        t("الإصدار", "Issue"): inv.issue_date.isoformat(),
                        t("الاستحقاق", "Due"): inv.due_date.isoformat() if inv.due_date else "-",
                        t("نسبة الضريبة", "Tax Rate"): f"{float(inv.tax_rate):.3f}%",
                        t("شامل الضريبة", "Tax Included"): t("نعم", "Yes") if bool(getattr(inv, "prices_include_tax", False)) else t("لا", "No"),
                        t("الإجمالي", "Total"): f"{inv.total_amount:,.2f} {currency_view}",
                    }
                )

            view_df = pd.DataFrame(rows)
            st.dataframe(view_df.drop(columns=["idx"]), use_container_width=True, hide_index=True)

            labels = [
                f"{inv.invoice_number} | {inv.customer_name or '-'} | {inv.total_amount:,.2f} {currency_view}"
                for inv in invoices
            ]
            selected_idx = st.selectbox(
                t("اختر فاتورة", "Select Invoice"),
                options=list(range(len(invoices))),
                format_func=lambda i: labels[i],
            )
            selected_inv = invoices[selected_idx]

            with st.expander(t("تحديث حالة الفاتورة", "Update Invoice Status"), expanded=False):
                status_labels = [_status_label(key, is_en) for key in STATUS_ORDER]
                current_status_label = _status_label(selected_inv.status, is_en)
                status_index = status_labels.index(current_status_label) if current_status_label in status_labels else 0
                new_status_label = st.selectbox(t("الحالة الجديدة", "New Status"), status_labels, index=status_index)
                new_status = STATUS_ORDER[status_labels.index(new_status_label)]

                paid_date_value = st.date_input(
                    t("تاريخ السداد", "Paid Date"),
                    value=selected_inv.paid_date or date.today(),
                    key=f"paid_date_{selected_idx}",
                )

                if st.button(t("حفظ الحالة", "Save Status"), key=f"save_status_{selected_idx}", use_container_width=True):
                    ok, _ = service.set_invoice_status(selected_idx, new_status, paid_date=paid_date_value)
                    if ok:
                        st.success(t("تم تحديث الحالة.", "Status updated."))
                        st.rerun()
                    st.error(t("تعذر تحديث الحالة.", "Could not update status."))

            with st.expander(t("تعديل بيانات الفاتورة", "Edit Invoice Details"), expanded=False):
                with st.form(f"edit_invoice_{selected_idx}", clear_on_submit=False):
                    e_customer_name = st.text_input(t("اسم العميل", "Customer Name"), value=selected_inv.customer_name)
                    e_customer_tax_no = st.text_input(
                        t("رقم ضريبي للعميل", "Customer Tax No"),
                        value=selected_inv.customer_tax_no,
                    )

                    e1, e2, e3 = st.columns(3)
                    with e1:
                        e_issue_date = st.date_input(t("تاريخ الإصدار", "Issue Date"), value=selected_inv.issue_date)
                    with e2:
                        e_has_due = st.checkbox(
                            t("تاريخ استحقاق", "Has Due Date"),
                            value=selected_inv.due_date is not None,
                            key=f"e_has_due_{selected_idx}",
                        )
                    with e3:
                        e_due_date = st.date_input(
                            t("تاريخ الاستحقاق", "Due Date"),
                            value=selected_inv.due_date or date.today(),
                            key=f"e_due_{selected_idx}",
                        )

                    e_project_options = [t("بدون مشروع", "No Project")] + projects
                    current_project_label = selected_inv.linked_project if selected_inv.linked_project in projects else e_project_options[0]
                    e_project_label = st.selectbox(
                        t("المشروع المرتبط", "Linked Project"),
                        e_project_options,
                        index=e_project_options.index(current_project_label),
                        key=f"e_project_{selected_idx}",
                    )
                    e_linked_project = "" if e_project_label == e_project_options[0] else e_project_label

                    inherited_edit = _resolve_tax_defaults(profile, month_key, e_linked_project)
                    st.caption(_inherited_source_caption(t, inherited_edit))

                    mode_enabled = bool(profile.tax_mode_enabled)
                    stored_source = str(getattr(selected_inv, "tax_source", "global") or "global").strip().lower()
                    if stored_source not in {"global", "project", "manual"}:
                        stored_source = "global"

                    if mode_enabled:
                        detected_manual = (
                            stored_source == "manual"
                            or abs(float(selected_inv.tax_rate) - float(inherited_edit["tax_rate"])) > 0.000001
                            or bool(getattr(selected_inv, "prices_include_tax", False)) != bool(inherited_edit["prices_include_tax"])
                        )
                        e_manual_override = st.checkbox(
                            t("تعديل الضريبة لهذه الفاتورة يدويًا", "Manual Tax Edit For This Invoice"),
                            value=bool(detected_manual),
                            key=f"e_manual_tax_{selected_idx}",
                        )
                    else:
                        e_manual_override = False
                        st.caption(
                            t(
                                "التعديل اليدوي مقفل لأن الوضع الضريبي غير مفعل. الإعدادات القديمة تبقى محفوظة.",
                                "Manual edit is locked while tax mode is off. Existing invoice settings stay saved.",
                            )
                        )

                    if e_manual_override:
                        e_tax_rate = st.number_input(
                            t("نسبة الضريبة لهذه الفاتورة %", "Tax Rate For This Invoice %"),
                            min_value=0.0,
                            max_value=100.0,
                            value=float(selected_inv.tax_rate),
                            step=0.5,
                            format="%.3f",
                            key=f"e_tax_rate_{selected_idx}",
                        )
                        e_include = st.checkbox(
                            t("المبلغ شامل ضريبة", "Amount Includes Tax"),
                            value=bool(getattr(selected_inv, "prices_include_tax", False)),
                            key=f"e_include_{selected_idx}",
                        )
                        e_tax_source = "manual"
                    else:
                        if mode_enabled:
                            e_tax_rate = float(inherited_edit["tax_rate"])
                            e_include = bool(inherited_edit["prices_include_tax"])
                            e_tax_source = "project" if inherited_edit.get("source") == "project" else "global"
                            st.caption(
                                t(
                                    f"النسبة المستخدمة: {e_tax_rate:.3f}% | شامل الضريبة: {'نعم' if e_include else 'لا'}",
                                    f"Tax rate: {e_tax_rate:.3f}% | Amount includes tax: {'yes' if e_include else 'no'}",
                                )
                            )
                        else:
                            e_tax_rate = float(selected_inv.tax_rate)
                            e_include = bool(getattr(selected_inv, "prices_include_tax", False))
                            e_tax_source = stored_source
                            st.caption(
                                t(
                                    f"تم الحفاظ على إعداد الفاتورة: {e_tax_rate:.3f}% | شامل الضريبة: {'نعم' if e_include else 'لا'} | المصدر: {_tax_source_label(e_tax_source, t)}",
                                    f"Invoice tax kept as-is: {e_tax_rate:.3f}% | Amount includes tax: {'yes' if e_include else 'no'} | Source: {_tax_source_label(e_tax_source, t)}",
                                )
                            )

                    default_amount = float(selected_inv.total_amount if e_include else selected_inv.subtotal)
                    e_amount = st.number_input(
                        _amount_label(t, e_include),
                        min_value=0.0,
                        value=default_amount,
                        step=10.0,
                        key=f"e_amount_{selected_idx}_{int(e_include)}_{int(e_manual_override)}",
                    )

                    e_status_labels = [_status_label(key, is_en) for key in STATUS_ORDER]
                    e_current_status = _status_label(selected_inv.status, is_en)
                    e_status_index = e_status_labels.index(e_current_status) if e_current_status in e_status_labels else 0
                    e_status_label = st.selectbox(
                        t("حالة الفاتورة", "Invoice Status"),
                        e_status_labels,
                        index=e_status_index,
                        key=f"e_status_{selected_idx}",
                    )
                    e_status = STATUS_ORDER[e_status_labels.index(e_status_label)]

                    e_notes = st.text_area(t("ملاحظات", "Notes"), value=selected_inv.notes, key=f"e_notes_{selected_idx}")
                    save_edit = st.form_submit_button(t("حفظ التعديل", "Save Edit"), use_container_width=True)

                if save_edit:
                    payload = {
                        "invoice_id": selected_inv.invoice_id,
                        "invoice_number": selected_inv.invoice_number,
                        "customer_name": e_customer_name,
                        "customer_tax_no": e_customer_tax_no,
                        "issue_date": e_issue_date,
                        "due_date": e_due_date if e_has_due else None,
                        "subtotal": float(e_amount),
                        "tax_rate": float(e_tax_rate),
                        "prices_include_tax": bool(e_include),
                        "tax_source": e_tax_source,
                        "status": e_status,
                        "linked_project": e_linked_project,
                        "currency": selected_inv.currency,
                        "notes": e_notes,
                        "paid_date": selected_inv.paid_date if e_status == "paid" else None,
                    }
                    ok, updated = service.update_invoice(selected_idx, payload)
                    if ok:
                        st.success(
                            t(
                                f"تم تحديث الفاتورة {updated.invoice_number if updated else ''}.",
                                f"Invoice {updated.invoice_number if updated else ''} updated.",
                            )
                        )
                        st.rerun()
                    st.error(t("تعذر حفظ التعديل.", "Could not save changes."))

            with st.expander(t("حذف الفاتورة", "Delete Invoice"), expanded=False):
                confirm = st.checkbox(t("تأكيد الحذف", "Confirm Deletion"), key=f"confirm_delete_inv_{selected_idx}")
                if st.button(
                    t("حذف الفاتورة نهائياً", "Delete Invoice Permanently"),
                    key=f"delete_inv_{selected_idx}",
                    use_container_width=True,
                    disabled=not confirm,
                ):
                    if repo.delete_invoice(selected_idx):
                        st.success(t("تم حذف الفاتورة.", "Invoice deleted."))
                        st.rerun()
                    st.error(t("تعذر حذف الفاتورة.", "Could not delete invoice."))

    with tab_export:
        st.subheader(t("التصدير", "Export"))
        export_period = str(report.get("period_key") or month_key or date.today().strftime("%Y-%m"))
        csv_bytes = TaxExportService.report_to_csv_bytes(report, currency_view=currency_view, is_en=is_en)
        pdf_bytes = TaxExportService.report_to_pdf_bytes(report, currency_view=currency_view, is_en=is_en)

        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button(
                label=t("تنزيل CSV", "Download CSV"),
                data=csv_bytes,
                file_name=f"floosy_tax_report_{export_period}.csv",
                mime="text/csv",
                use_container_width=True,
                key="tax_export_csv_btn",
            )
        with ex2:
            st.download_button(
                label=t("تنزيل PDF", "Download PDF"),
                data=pdf_bytes,
                file_name=f"floosy_tax_report_{export_period}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="tax_export_pdf_btn",
            )
        st.caption(
            t(
                "CSV للتفصيل الكامل، وPDF نسخة سريعة للمشاركة.",
                "CSV gives full detail, and PDF is a quick file for sharing.",
            )
        )

        with st.expander(t("ملخص المشاريع", "Project Summary"), expanded=False):
            project_bucket = {}
            for inv in report.get("invoices", []):
                project_name = str(inv.get("linked_project") or "").strip() or t("غير مرتبط", "Unlinked")
                bucket = project_bucket.setdefault(project_name, {"subtotal": 0.0, "tax": 0.0, "total": 0.0, "count": 0})
                bucket["subtotal"] += float(inv.get("subtotal", 0.0))
                bucket["tax"] += float(inv.get("tax_amount", 0.0))
                bucket["total"] += float(inv.get("total_amount", 0.0))
                bucket["count"] += 1

            if not project_bucket:
                st.caption(t("لا توجد بيانات مشاريع في هذا الشهر.", "No project-linked data this month."))
            else:
                pr_rows = []
                for name, vals in project_bucket.items():
                    pr_rows.append(
                        {
                            t("المشروع", "Project"): name,
                            t("عدد الفواتير", "Invoice Count"): vals["count"],
                            t("قبل الضريبة", "Subtotal"): f"{vals['subtotal']:,.2f} {currency_view}",
                            t("الضريبة", "Tax"): f"{vals['tax']:,.2f} {currency_view}",
                            t("الإجمالي", "Total"): f"{vals['total']:,.2f} {currency_view}",
                        }
                    )
                st.dataframe(pd.DataFrame(pr_rows), use_container_width=True, hide_index=True)

        with st.expander(t("تفصيل نسب الضريبة", "Tax Rate Breakdown"), expanded=False):
            rates = report.get("rates", [])
            if not rates:
                st.caption(t("لا يوجد تفصيل نسب لهذا الشهر.", "No tax-rate breakdown for this month."))
            else:
                rate_rows = []
                for row in rates:
                    rate_rows.append(
                        {
                            t("النسبة", "Rate"): f"{float(row.get('tax_rate', 0.0)):.3f}%",
                            t("عدد الفواتير", "Invoice Count"): int(row.get("count", 0)),
                            t("قبل الضريبة", "Subtotal"): f"{float(row.get('subtotal', 0.0)):,.2f} {currency_view}",
                            t("الضريبة", "Tax"): f"{float(row.get('tax', 0.0)):,.2f} {currency_view}",
                            t("الإجمالي", "Total"): f"{float(row.get('total', 0.0)):,.2f} {currency_view}",
                        }
                    )
                st.dataframe(pd.DataFrame(rate_rows), use_container_width=True, hide_index=True)
