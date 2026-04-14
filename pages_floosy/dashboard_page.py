import base64
import html
from datetime import datetime

import pandas as pd
import streamlit as st

from config_floosy import add_transaction, arabic_months, english_months, get_all_transactions_df, get_logo_bytes, get_saving_totals
from repositories.session_repo import SessionStateRepository
from services.expense_tax_service import ExpenseTaxService
from services.financial_analyzer import FinancialAnalyzer


def _render_summary_card_styles() -> None:
    st.markdown(
        """
        <style>
        .floosy-summary-card {
            border-radius: 16px;
            padding: 16px 18px 14px 18px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.8rem;
            background: #ffffff;
            position: relative;
            overflow: hidden;
        }

        .floosy-summary-card--featured {
            min-height: 124px;
            background: linear-gradient(135deg, #164c72 0%, #1f7a92 55%, #2aa47c 100%);
            color: #f8fafc;
            border-color: rgba(255, 255, 255, 0.16);
        }

        .floosy-summary-card--income {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-summary-card--expense {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-summary-card--neutral {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-summary-card--savings {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-summary-card--projects {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-summary-card__accent {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 6px;
            background: linear-gradient(180deg, #164c72 0%, #1f7a92 55%, #2aa47c 100%);
        }

        .floosy-summary-card__label {
            font-size: 0.88rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
            color: var(--label-color, #475569);
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            line-height: 1.2;
        }

        .floosy-summary-card__label-icon {
            font-size: 0.82rem;
            line-height: 1;
            opacity: 0.8;
            flex: 0 0 auto;
        }

        .floosy-summary-card__value {
            font-size: 1.52rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.02em;
            color: var(--value-color, #0f172a);
        }

        .floosy-summary-card__currency {
            font-size: 0.8em;
            font-weight: 700;
            color: #64748b;
            opacity: 0.88;
        }

        .floosy-summary-card--featured .floosy-summary-card__label,
        .floosy-summary-card--featured .floosy-summary-card__value {
            color: #ffffff;
        }

        .floosy-summary-card--featured .floosy-summary-card__currency {
            color: rgba(255, 255, 255, 0.82);
            opacity: 1;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_value_html(value: str) -> str:
    clean_value = str(value or "").strip()
    if " " not in clean_value:
        return html.escape(clean_value)
    amount_part, currency_part = clean_value.rsplit(" ", 1)
    return (
        f"{html.escape(amount_part)} "
        f'<span class="floosy-summary-card__currency">{html.escape(currency_part)}</span>'
    )


def _metric_label_html(label: str, tone: str, is_en: bool) -> str:
    icon_map = {
        "balance": "◎",
        "income": "↗",
        "expense": "↘",
        "savings": "◌",
        "projects": "◇",
        "neutral": "•",
    }
    icon = html.escape(icon_map.get(tone, "•"))
    text = html.escape(label)
    icon_html = f'<span class="floosy-summary-card__label-icon" aria-hidden="true">{icon}</span>'
    text_html = f"<span>{text}</span>"
    return f"{icon_html}{text_html}" if is_en else f"{text_html}{icon_html}"


def _render_summary_card(label: str, value: str, tone: str, is_en: bool, featured: bool = False) -> None:
    direction = "ltr" if is_en else "rtl"
    align = "left" if is_en else "right"
    accent_side = "left" if is_en else "right"
    tone_class = {
        "balance": "floosy-summary-card--featured",
        "income": "floosy-summary-card--income",
        "expense": "floosy-summary-card--expense",
        "neutral": "floosy-summary-card--neutral",
        "savings": "floosy-summary-card--savings",
        "projects": "floosy-summary-card--projects",
    }.get(tone, "floosy-summary-card--neutral")
    featured_class = " floosy-summary-card--featured" if featured and tone != "balance" else ""
    accent_html = "" if tone == "balance" else f'<div class="floosy-summary-card__accent" style="{accent_side}:0;"></div>'
    card_markup = (
        f'<div class="floosy-summary-card {tone_class}{featured_class}" '
        f'style="direction:{direction};text-align:{align};">'
        f"{accent_html}"
        f'<div class="floosy-summary-card__label">{_metric_label_html(label, tone, is_en)}</div>'
        f'<div class="floosy-summary-card__value">{_metric_value_html(value)}</div>'
        "</div>"
    )

    st.markdown(card_markup, unsafe_allow_html=True)


def _summary_theme(status: str) -> dict:
    if status in {"cash_pressure_90", "coverage_gap", "project_pressure"}:
        return {
            "background": "#FEF2F2",
            "border": "#EF4444",
            "label": "#991B1B",
            "text": "#7F1D1D",
            "pill_bg": "#FFF1F2",
            "pill_border": "#FECACA",
            "pill_text": "#991B1B",
        }
    if status in {"needs_follow_up", "spending_high", "docs_due"}:
        return {
            "background": "#FFFBEB",
            "border": "#F59E0B",
            "label": "#92400E",
            "text": "#78350F",
            "pill_bg": "#FFF7D6",
            "pill_border": "#FDE68A",
            "pill_text": "#92400E",
        }
    return {
        "background": "#ECFDF5",
        "border": "#22C55E",
        "label": "#166534",
        "text": "#14532D",
        "pill_bg": "#F0FDF4",
        "pill_border": "#BBF7D0",
        "pill_text": "#166534",
    }


def render(month_key: str, month: str, year: int):
    """Dashboard page entry point. App expects this function."""

    settings = st.session_state.settings
    currency = settings.get("default_currency", "د.ك")
    is_en = settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol
    tax_options = ExpenseTaxService.expense_options(st.session_state, is_en=is_en)
    tax_codes = [opt["code"] for opt in tax_options]
    tax_label_by_code = {opt["code"]: opt["label"] for opt in tax_options}
    default_expense_tax_code = next((opt["code"] for opt in tax_options if opt.get("deductible")), tax_codes[0] if tax_codes else "")
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month

    def _toast(msg: str, level: str = "success"):
        if hasattr(st, "toast"):
            st.toast(msg)
        else:
            if level == "warning":
                st.warning(msg)
            else:
                st.success(msg)

    # ===== Header (uses CSS from config_floosy.py) =====
    logo_html = ""
    logo_bytes = get_logo_bytes()
    if logo_bytes:
        b64 = base64.b64encode(logo_bytes).decode("utf-8")
        logo_html = f'<img src="data:image/png;base64,{b64}" alt="Floosy logo" />'

    st.markdown(
        f"""
        <div class="flossy-header">
            <div class="flossy-header-inner">
                <div class="flossy-header-title">فلوسي | Floosy</div>
                <div>{logo_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== Greeting (above the cards) =====
    user_name = (settings.get("name") or "").strip()
    if user_name:
        st.markdown(t(f"مرحباً، **{user_name}**", f"Hello, **{user_name}**"))
    else:
        st.markdown(t("مرحباً", "Hello"))

    st.caption(t(f"الشهر المعروض: {month_display} {year}", f"Selected month: {month_display} {year}"))
    st.markdown("---")

    _render_summary_card_styles()

    # ===== Build metrics =====
    df_all = get_all_transactions_df(currency)

    account_balance = 0.0
    month_income = 0.0
    month_expenses = 0.0

    # Arabic month name -> month number
    month_map = {
        "يناير": 1,
        "فبراير": 2,
        "مارس": 3,
        "أبريل": 4,
        "مايو": 5,
        "يونيو": 6,
        "يوليو": 7,
        "أغسطس": 8,
        "سبتمبر": 9,
        "أكتوبر": 10,
        "نوفمبر": 11,
        "ديسمبر": 12,
    }
    month_num = month_map.get(month)

    if isinstance(df_all, pd.DataFrame) and not df_all.empty:
        # Ensure datetime column
        if "date_dt" not in df_all.columns:
            if "date" in df_all.columns:
                df_all["date_dt"] = pd.to_datetime(df_all["date"], errors="coerce")
            else:
                df_all["date_dt"] = pd.NaT
        else:
            df_all["date_dt"] = pd.to_datetime(df_all["date_dt"], errors="coerce")

        total_in_all = df_all[df_all["type"] == "دخل"]["amount"].sum()
        total_out_all = df_all[df_all["type"] == "مصروف"]["amount"].sum()
        account_balance = float(total_in_all) - float(total_out_all)

        # Month filter
        if month_num:
            mask = (
                (df_all["date_dt"].dt.year == int(year))
                & (df_all["date_dt"].dt.month == int(month_num))
            )
            df_month = df_all[mask]
        else:
            df_month = df_all[df_all["date_dt"].dt.year == int(year)]

        if not df_month.empty:
            month_income = df_month[df_month["type"] == "دخل"]["amount"].sum()
            month_expenses = df_month[df_month["type"] == "مصروف"]["amount"].sum()

    # Savings balance (all time)
    total_saved_all, total_withdraw_all = get_saving_totals()
    saving_balance = float(total_saved_all) - float(total_withdraw_all)

    # Project net (this month) for dashboard card toggle.
    project_month_obj = st.session_state.get("project_data", {}).get(month_key, {})
    projects_map = project_month_obj.get("projects", {})
    if isinstance(projects_map, dict) and projects_map:
        project_txs = []
        for _, project_obj in projects_map.items():
            project_txs.extend(project_obj.get("transactions", []))
    else:
        project_txs = project_month_obj.get("project_transactions", [])

    project_income = sum(float(tx.get("amount", 0.0)) for tx in project_txs if tx.get("type") == "دخل")
    project_expense = sum(float(tx.get("amount", 0.0)) for tx in project_txs if tx.get("type") == "مصروف")
    project_net_month = project_income - project_expense


    show_account = settings.get("show_status_account", True)
    show_saving = settings.get("show_status_saving", True)
    show_project = settings.get("show_status_project", True)

    metric_items = []
    if show_account:
        metric_items.extend([
            {
                "label": t("الرصيد الحالي", "Current Balance"),
                "value": f"{account_balance:,.0f} {currency_view}",
                "tone": "balance",
                "featured": True,
            },
            {
                "label": t("دخل هذا الشهر", "Income This Month"),
                "value": f"{month_income:,.0f} {currency_view}",
                "tone": "income",
                "featured": False,
            },
            {
                "label": t("مصروف هذا الشهر", "Expenses This Month"),
                "value": f"{month_expenses:,.0f} {currency_view}",
                "tone": "expense",
                "featured": False,
            },
        ])
    if show_saving:
        metric_items.append(
            {
                "label": t("رصيد التوفير", "Savings Balance"),
                "value": f"{saving_balance:,.0f} {currency_view}",
                "tone": "savings",
                "featured": False,
            }
        )
    if show_project:
        metric_items.append(
            {
                "label": t("صافي المشاريع هذا الشهر", "Projects Net This Month"),
                "value": f"{project_net_month:,.0f} {currency_view}",
                "tone": "projects",
                "featured": False,
            }
        )

    if not metric_items:
        st.info(t("كل بطاقات الملخص مخفية من الإعدادات.", "All summary cards are hidden in settings."))
    else:
        featured_item = next((item for item in metric_items if item.get("featured")), None)
        if featured_item:
            _render_summary_card(
                featured_item["label"],
                featured_item["value"],
                featured_item["tone"],
                is_en=is_en,
                featured=True,
            )

        grid_items = [item for item in metric_items if item is not featured_item]
        for i in range(0, len(grid_items), 2):
            row_items = grid_items[i:i + 2]
            cols = st.columns(len(row_items))
            for col, item in zip(cols, row_items):
                with col:
                    _render_summary_card(
                        item["label"],
                        item["value"],
                        item["tone"],
                        is_en=is_en,
                        featured=False,
                    )

    analyzer = FinancialAnalyzer(SessionStateRepository())
    brief = analyzer.dashboard_brief(st.session_state, month_key, currency)
    summary_theme = _summary_theme(str(brief.get("status", "stable") or "stable"))
    summary_border_side = "border-left" if is_en else "border-right"

    st.markdown("### " + t("الملخص الذكي", "Smart Summary"))
    brief_message = brief["message_en"] if is_en else brief["message_ar"]
    brief_detail = brief["detail_en"] if is_en else brief["detail_ar"]
    focus_label = brief["focus_label_en"] if is_en else brief["focus_label_ar"]
    support_label = brief["support_label_en"] if is_en else brief["support_label_ar"]
    focus_value = f"{brief.get('focus_value', 0.0):,.0f} {currency_view}"
    support_value = f"{brief.get('support_value', 0.0):,.0f} {currency_view}"

    st.markdown(
        f"""
        <div style="background:{summary_theme['background']};border:1px solid {summary_theme['pill_border']};{summary_border_side}:6px solid {summary_theme['border']};border-radius:12px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-weight:700;font-size:1.02rem;color:{summary_theme['text']};">{brief_message}</div>
            <div style="color:{summary_theme['label']};font-size:0.92rem;margin-top:4px;">{brief_detail}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
                <div style="background:{summary_theme['pill_bg']};border:1px solid {summary_theme['pill_border']};border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                    <span style="color:{summary_theme['label']};">{focus_label}:</span>
                    <span style="font-weight:700;color:{summary_theme['pill_text']};"> {focus_value}</span>
                </div>
                <div style="background:{summary_theme['pill_bg']};border:1px solid {summary_theme['pill_border']};border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                    <span style="color:{summary_theme['label']};">{support_label}:</span>
                    <span style="font-weight:700;color:{summary_theme['pill_text']};"> {support_value}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(t("فتح المحلل المالي", "Open Financial Analyzer"), key="open_assistant_from_dashboard"):
        st.session_state.current_page = "assistant"
        st.rerun()

    # ===== Floating + button + Modal (session_state only) =====
    default_quick_form = {"type": "مصروف", "amount": 0.0, "category": "أخرى", "note": "", "tax_tag_code": ""}
    st.session_state.setdefault("dash_quick_open", False)
    st.session_state.setdefault("dash_quick_form", default_quick_form.copy())

    fab_side_css = "left: 22px; right: auto;" if not is_en else "right: 22px; left: auto;"

    fab_css = """
        <style>
        div.st-key-dash_quick_fab {
            position: fixed;
            __FAB_SIDE__
            bottom: 22px;
            z-index: 999999;
        }

        div.st-key-dash_quick_fab button {
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

        div.st-key-dash_quick_fab button::before {
            content: "+";
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            line-height: 56px;
            font-weight: 900;
            color: #ffffff;
            pointer-events: none;
        }

        div.st-key-dash_quick_fab button:hover {
            filter: brightness(1.05);
        }
        </style>
    """.replace("__FAB_SIDE__", fab_side_css)
    st.markdown(fab_css, unsafe_allow_html=True)

    if st.button("", key="dash_quick_fab", help=t("إضافة", "Add")):
        st.session_state["dash_quick_open"] = True
        st.rerun()

    if st.session_state["dash_quick_open"]:
        categories = [
            t("راتب", "Salary"),
            t("دخل إضافي", "Extra Income"),
            t("إيجار / قسط", "Rent / Installment"),
            t("فواتير", "Bills"),
            t("مشتريات", "Shopping"),
            t("طلعات وكوفي", "Coffee / Outings"),
            t("أكل أونلاين", "Food Delivery"),
            t("مواصلات", "Transport"),
            t("صحة / صالون", "Health / Salon"),
            t("أخرى", "Other"),
        ]
        st.markdown(f"### {t('إضافة معاملة', 'Add Transaction')}")

        form_state = st.session_state["dash_quick_form"]
        type_map_ar_en = {"مصروف": "Expense", "دخل": "Income"}
        type_map_en_ar = {"Expense": "مصروف", "Income": "دخل"}
        type_options = [t("مصروف", "Expense"), t("دخل", "Income")]
        cat_map_ar_en = {
            "راتب": "Salary",
            "دخل إضافي": "Extra Income",
            "إيجار / قسط": "Rent / Installment",
            "فواتير": "Bills",
            "مشتريات": "Shopping",
            "طلعات وكوفي": "Coffee / Outings",
            "أكل أونلاين": "Food Delivery",
            "مواصلات": "Transport",
            "صحة / صالون": "Health / Salon",
            "أخرى": "Other",
        }
        cat_map_en_ar = {v: k for k, v in cat_map_ar_en.items()}

        default_type = form_state.get("type", "مصروف")
        if is_en and default_type in type_map_ar_en:
            default_type = type_map_ar_en[default_type]
        if (not is_en) and default_type in type_map_en_ar:
            default_type = type_map_en_ar[default_type]

        default_category = form_state.get("category", "أخرى")
        if is_en and default_category in cat_map_ar_en:
            default_category = cat_map_ar_en[default_category]
        if (not is_en) and default_category in cat_map_en_ar:
            default_category = cat_map_en_ar[default_category]

        current_type = st.session_state.get("dash_q_type", default_type)
        if is_en and current_type in type_map_ar_en:
            current_type = type_map_ar_en[current_type]
        elif (not is_en) and current_type in type_map_en_ar:
            current_type = type_map_en_ar[current_type]
        if current_type not in type_options:
            current_type = default_type if default_type in type_options else type_options[0]
        st.session_state["dash_q_type"] = current_type

        current_category = st.session_state.get("dash_q_category", default_category)
        if is_en and current_category in cat_map_ar_en:
            current_category = cat_map_ar_en[current_category]
        elif (not is_en) and current_category in cat_map_en_ar:
            current_category = cat_map_en_ar[current_category]
        if current_category not in categories:
            current_category = default_category if default_category in categories else categories[-1]
        st.session_state["dash_q_category"] = current_category

        st.session_state.setdefault("dash_q_amount", float(form_state.get("amount", 0.0)))
        st.session_state.setdefault("dash_q_note", form_state.get("note", ""))

        default_form_tax_code = str(form_state.get("tax_tag_code", "") or "")
        if default_form_tax_code not in tax_codes:
            default_form_tax_code = default_expense_tax_code
        current_tax_code = str(st.session_state.get("dash_q_tax_code", default_form_tax_code) or "")
        if current_tax_code not in tax_codes:
            current_tax_code = default_form_tax_code if default_form_tax_code in tax_codes else (tax_codes[0] if tax_codes else "")
        st.session_state["dash_q_tax_code"] = current_tax_code

        st.markdown(
            """<style>
div[data-testid="stForm"] {
  position: fixed !important;
  top: 6vh !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  width: min(360px, 92vw) !important;
  height: auto !important;
  max-height: 88vh !important;
  overflow-y: auto !important;
  overscroll-behavior: contain !important;
  -webkit-overflow-scrolling: touch !important;
  padding: 12px 12px 10px 12px !important;
  background: #ffffff !important;
  border-radius: 16px !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25) !important;
  z-index: 999999 !important;
}

.flossy-quick-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 999998;
  display: block;
}
</style>
<div class="flossy-quick-overlay"></div>
""",
            unsafe_allow_html=True,
        )

        with st.form("quick_add_form", clear_on_submit=False):
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                q_type_lbl = st.selectbox(t("النوع", "Type"), type_options, key="dash_q_type")
            with r1c2:
                q_amount = st.number_input(t("المبلغ", "Amount"), min_value=0.0, step=1.0, key="dash_q_amount")

            q_category = st.selectbox(t("التصنيف", "Category"), categories, key="dash_q_category")
            q_selected_type = "مصروف" if q_type_lbl == t("مصروف", "Expense") else "دخل"
            q_tax_code = ""
            if q_selected_type == "مصروف" and tax_codes:
                q_tax_code = st.selectbox(
                    t("التصنيف الضريبي", "Tax Classification"),
                    tax_codes,
                    index=tax_codes.index(st.session_state["dash_q_tax_code"]) if st.session_state["dash_q_tax_code"] in tax_codes else 0,
                    format_func=lambda code: tax_label_by_code.get(code, code),
                    key="dash_q_tax_code",
                )
                if q_tax_code == ExpenseTaxService.DEDUCTIBLE_CODE:
                    st.caption(
                        t(
                            "إذا اخترت أخرى، اكتبي التفاصيل في الملاحظة.",
                            "If you choose Other, add the details in the note.",
                        )
                    )
            note_placeholder = (
                t("اكتبي التفاصيل هنا إذا اخترت أخرى", "Write the details here if you choose Other")
                if q_tax_code == ExpenseTaxService.DEDUCTIBLE_CODE
                else ""
            )
            q_note = st.text_input(
                t("ملاحظة (اختياري)", "Note (Optional)"),
                key="dash_q_note",
                placeholder=note_placeholder,
            )

            b1, b2 = st.columns(2)
            with b1:
                save_btn = st.form_submit_button(t("حفظ", "Save"))
            with b2:
                cancel_btn = st.form_submit_button(t("إغلاق", "Close"))

        if cancel_btn:
            st.session_state["dash_quick_open"] = False
            st.rerun()

        if save_btn:
            st.session_state["dash_quick_form"] = {
                "type": q_selected_type,
                "amount": float(q_amount),
                "category": q_category,
                "note": q_note,
                "tax_tag_code": q_tax_code if q_selected_type == "مصروف" else "",
            }
            if q_amount and q_amount > 0:
                tx_payload = {
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "type": q_selected_type,
                    "amount": float(q_amount),
                    "currency": currency,
                    "category": q_category,
                    "note": q_note,
                }
                if q_selected_type == "مصروف" and q_tax_code:
                    tx_payload["tax_tag_code"] = q_tax_code
                add_transaction(month_key, tx_payload)
                st.session_state["dash_quick_open"] = False
                st.session_state["dash_quick_form"] = default_quick_form.copy()
                st.session_state["dash_q_type"] = default_quick_form["type"]
                st.session_state["dash_q_amount"] = default_quick_form["amount"]
                st.session_state["dash_q_category"] = default_quick_form["category"]
                st.session_state["dash_q_note"] = default_quick_form["note"]
                st.session_state["dash_q_tax_code"] = default_expense_tax_code if tax_codes else ""
                _toast(t("تمت إضافة المعاملة.", "Transaction added."))
                st.rerun()
            else:
                _toast(t("أدخل مبلغًا أكبر من 0.", "Enter amount greater than 0."), level="warning")
