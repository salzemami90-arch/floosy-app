import html
from datetime import datetime

import pandas as pd
import streamlit as st

from config_floosy import add_transaction, arabic_months, english_months, get_all_transactions_df, get_saving_totals, get_builtin_logo_b64
from services.currency_localization import currency_short_label
from services.i18n import dashboard_brief_copy, format_i18n, make_t, get_lang_code, get_months
from repositories.session_repo import SessionStateRepository
from services.expense_tax_service import ExpenseTaxService
from services.financial_analyzer import FinancialAnalyzer
from services.transaction_categories import canonical_category, category_label, localized_all_categories


def _proof_payload(uploaded_file) -> dict:
    if uploaded_file is None:
        return {}
    return {
        "proof_name": getattr(uploaded_file, "name", "") or "",
        "proof_bytes": uploaded_file.getvalue(),
        "proof_type": getattr(uploaded_file, "type", "") or "",
    }


def _render_summary_card_styles() -> None:
    st.markdown(
        """
        <style>
        .floosy-summary-card {
            border-radius: 16px;
            padding: 14px 16px 13px 16px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.55rem;
            background: #ffffff;
            position: relative;
            overflow: hidden;
        }

        .floosy-summary-card--featured {
            min-height: 116px;
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
            margin-bottom: 0.42rem;
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

        .floosy-smart-summary {
            border-radius: 12px;
            padding: 14px 16px 13px 16px;
            margin: 0.15rem 0 0.65rem 0;
        }

        .floosy-smart-summary__message {
            font-weight: 800;
            font-size: 1.04rem;
            line-height: 1.35;
        }

        .floosy-smart-summary__detail {
            font-size: 0.92rem;
            line-height: 1.45;
            margin-top: 0.32rem;
        }

        .floosy-smart-summary__facts {
            display: flex;
            gap: 0.45rem;
            flex-wrap: wrap;
            margin-top: 0.8rem;
        }

        .floosy-smart-summary__pill {
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.84rem;
            line-height: 1.35;
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


def _metric_label_html(label: str, tone: str, is_ltr: bool) -> str:
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
    return f"{icon_html}{text_html}" if is_ltr else f"{text_html}{icon_html}"


def _render_summary_card(label: str, value: str, tone: str, is_ltr: bool, featured: bool = False) -> None:
    direction = "ltr" if is_ltr else "rtl"
    align = "left" if is_ltr else "right"
    accent_side = "left" if is_ltr else "right"
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
        f'<div class="floosy-summary-card__label">{_metric_label_html(label, tone, is_ltr)}</div>'
        f'<div class="floosy-summary-card__value">{_metric_value_html(value)}</div>'
        "</div>"
    )

    st.markdown(card_markup, unsafe_allow_html=True)


def _tx_type_label(value: str) -> str:
    t = make_t()
    clean_value = str(value or "").strip()
    if clean_value in {"دخل", "Income", t("دخل", "Income")}:
        return t("دخل", "Income")
    if clean_value in {"مصروف", "Expense", t("مصروف", "Expense")}:
        return t("مصروف", "Expense")
    return clean_value


def _canonical_tx_type(value: str) -> str:
    t = make_t()
    clean_value = str(value or "").strip()
    if clean_value in {"دخل", "Income", t("دخل", "Income")}:
        return "دخل"
    if clean_value in {"مصروف", "Expense", t("مصروف", "Expense")}:
        return "مصروف"
    return clean_value


def _summary_theme(status: str) -> dict:
    if status == "empty":
        return {
            "background": "#FFFFFF",
            "border": "#E2E8F0",
            "label": "#64748B",
            "text": "#0F172A",
            "pill_bg": "#F8FAFC",
            "pill_border": "#E2E8F0",
            "pill_text": "#475569",
        }
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
    if status in {"needs_follow_up", "spending_high", "docs_due", "note_pattern"}:
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
        "background": "#EAF5EF",
        "border": "#047857",
        "label": "#065F46",
        "text": "#064E3B",
        "pill_bg": "#F6FBF8",
        "pill_border": "#BFD8CC",
        "pill_text": "#064E3B",
    }


def render(month_key: str, month: str, year: int):
    """Dashboard page entry point. App expects this function."""

    settings = st.session_state.settings
    currency = settings.get("default_currency", "د.ك")
    _lc = get_lang_code()
    is_en = _lc == "en"
    is_ltr = _lc != "ar"
    t = make_t()
    currency_view = currency_short_label(currency, _lc)
    tax_options = ExpenseTaxService.expense_options(st.session_state, is_en=(_lc != "ar"))
    tax_codes = [opt["code"] for opt in tax_options]
    tax_label_by_code = {opt["code"]: opt["label"] for opt in tax_options}
    default_expense_tax_code = next((opt["code"] for opt in tax_options if opt.get("deductible")), tax_codes[0] if tax_codes else "")
    _display_months = get_months()
    month_display = _display_months[arabic_months.index(month)] if (_lc != "ar" and month in arabic_months) else month

    def _toast(msg: str, level: str = "success"):
        if hasattr(st, "toast"):
            st.toast(msg)
        else:
            if level == "warning":
                st.warning(msg)
            else:
                st.success(msg)

    # ===== Header (uses CSS from config_floosy.py) =====
    header_tagline = t("Flow · Control · Growth", "Flow · Control · Growth")
    _logo_src = get_builtin_logo_b64()
    logo_html = f"""
    <div class="flossy-header-logo-wrap">
        <img class="flossy-header-logo" src="{_logo_src}" alt="GoushFi" />
    </div>
    """

    st.markdown(
        f"""
        <div class="flossy-header">
            <div class="flossy-header-inner">
                <div class="flossy-header-title">
                    <span>GoushFi</span>
                    <span class="flossy-header-tagline">{header_tagline}</span>
                </div>
                <div>{logo_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== Greeting (above the cards) =====
    user_name = (settings.get("name") or "").strip()
    if user_name:
        st.markdown(format_i18n("hello_user", name=user_name))
    else:
        st.markdown(t("مرحباً", "Hello"))

    st.caption(format_i18n("selected_month", month=month_display, year=year))
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
                is_ltr=is_ltr,
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
                        is_ltr=is_ltr,
                        featured=False,
                    )

    analyzer = FinancialAnalyzer(SessionStateRepository())
    brief = analyzer.dashboard_brief(st.session_state, month_key, currency)
    brief_status = str(brief.get("status", "stable") or "stable")
    show_spending_note_on_good = brief_status == "spending_high" and float(brief.get("focus_value", 0.0)) >= 0
    summary_theme = _summary_theme("stable" if show_spending_note_on_good else brief_status)
    summary_border_side = "border-left" if is_ltr else "border-right"

    st.markdown("### " + t("الملخص الذكي", "Smart Summary"))
    brief_message, brief_detail, focus_label, support_label = dashboard_brief_copy(
        brief,
        currency_view,
        spending_note_on_good=show_spending_note_on_good,
    )
    focus_value = f"{brief.get('focus_value', 0.0):,.0f} {currency_view}"
    support_value = f"{brief.get('support_value', 0.0):,.0f} {currency_view}"

    st.markdown(
        f"""
        <div class="floosy-smart-summary" style="background:{summary_theme['background']};border:1px solid {summary_theme['pill_border']};{summary_border_side}:6px solid {summary_theme['border']};">
            <div class="floosy-smart-summary__message" style="color:{summary_theme['text']};">{brief_message}</div>
            <div class="floosy-smart-summary__detail" style="color:{summary_theme['label']};">{brief_detail}</div>
            <div class="floosy-smart-summary__facts">
                <div class="floosy-smart-summary__pill" style="background:{summary_theme['pill_bg']};border:1px solid {summary_theme['pill_border']};">
                    <span style="color:{summary_theme['label']};">{focus_label}:</span>
                    <span style="font-weight:700;color:{summary_theme['pill_text']};"> {focus_value}</span>
                </div>
                <div class="floosy-smart-summary__pill" style="background:{summary_theme['pill_bg']};border:1px solid {summary_theme['pill_border']};">
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
        st.session_state["sidebar_section"] = "assistant"
        st.rerun()

    # ===== Floating + button + Modal (session_state only) =====
    default_quick_form = {"type": "مصروف", "amount": 0.0, "category": "أخرى", "note": "", "tax_tag_code": ""}
    st.session_state.setdefault("dash_quick_open", False)
    st.session_state.setdefault("dash_quick_form", default_quick_form.copy())
    if st.session_state.pop("dash_quick_reset", False):
        st.session_state["dash_q_type"] = default_quick_form["type"]
        st.session_state["dash_q_amount"] = default_quick_form["amount"]
        st.session_state["dash_q_category"] = default_quick_form["category"]
        st.session_state["dash_q_note"] = default_quick_form["note"]

    fab_side_css = "left: 22px; right: auto;" if not is_ltr else "right: 22px; left: auto;"

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
        st.markdown(f"### {t('إضافة معاملة', 'Add Transaction')}")

        form_state = st.session_state["dash_quick_form"]
        type_options = [_tx_type_label("مصروف"), _tx_type_label("دخل")]

        default_type = _tx_type_label(form_state.get("type", "مصروف"))
        default_category = category_label(form_state.get("category", "أخرى"), is_en)

        current_type = st.session_state.get("dash_q_type", default_type)
        current_type = _tx_type_label(current_type)
        if current_type not in type_options:
            current_type = default_type if default_type in type_options else type_options[0]
        st.session_state["dash_q_type"] = current_type
        categories = localized_all_categories(is_en)

        current_category = st.session_state.get("dash_q_category", default_category)
        current_category = category_label(current_category, is_en)
        if current_category not in categories:
            current_category = default_category if default_category in categories else categories[-1]
        st.session_state["dash_q_category"] = current_category

        st.session_state.setdefault("dash_q_amount", float(form_state.get("amount", 0.0)))
        st.session_state.setdefault("dash_q_note", form_state.get("note", ""))

        default_form_tax_code = str(form_state.get("tax_tag_code", "") or "")
        if default_form_tax_code not in tax_codes:
            default_form_tax_code = default_expense_tax_code
        current_tax_code = default_form_tax_code if default_form_tax_code in tax_codes else (tax_codes[0] if tax_codes else "")

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
            q_selected_type = _canonical_tx_type(q_type_lbl)
            q_tax_code = ""
            if q_selected_type == "مصروف" and tax_codes:
                q_tax_index = tax_codes.index(current_tax_code) if current_tax_code in tax_codes else 0
                q_tax_code = st.selectbox(
                    t("التصنيف الضريبي", "Tax Classification"),
                    tax_codes,
                    index=q_tax_index,
                    format_func=lambda code: tax_label_by_code.get(code, code),
                )
                if q_tax_code == ExpenseTaxService.DEDUCTIBLE_CODE:
                    st.caption(
                        t(
                            "إذا تم اختيار أخرى، يرجى إضافة التفاصيل في الملاحظة.",
                            "If you choose Other, add the details in the note.",
                        )
                    )
            q_note = st.text_input(
                t("ملاحظة (اختياري)", "Note (Optional)"),
                key="dash_q_note",
            )
            q_proof = st.file_uploader(
                t("إرفاق فاتورة/إثبات الحركة (اختياري)", "Attach Invoice/Transaction Proof (Optional)"),
                type=["png", "jpg", "jpeg", "pdf"],
                key=f"dash_q_proof_{int(st.session_state.get('dash_q_proof_nonce', 0))}",
            )
            st.caption(
                t(
                    "اختياري: يمكن إرفاق صورة كابچر أو PDF، وسيظهر لاحقًا في سجل الحساب.",
                    "Optional: upload a screenshot or PDF, then find it later in the account log.",
                )
            )

            b1, b2 = st.columns(2)
            with b1:
                save_btn = st.form_submit_button(t("حفظ", "Save"))
            with b2:
                cancel_btn = st.form_submit_button(t("إغلاق", "Close"))

        if cancel_btn:
            st.session_state["dash_quick_open"] = False
            st.session_state["dash_q_proof_nonce"] = int(st.session_state.get("dash_q_proof_nonce", 0)) + 1
            st.rerun()

        if save_btn:
            st.session_state["dash_quick_form"] = {
                "type": q_selected_type,
                "amount": float(q_amount),
                "category": canonical_category(q_category),
                "note": q_note,
                "tax_tag_code": q_tax_code if q_selected_type == "مصروف" else "",
            }
            if q_amount and q_amount > 0:
                tx_payload = {
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "type": q_selected_type,
                    "amount": float(q_amount),
                    "currency": currency,
                    "category": canonical_category(q_category),
                    "note": q_note,
                }
                if q_selected_type == "مصروف" and q_tax_code:
                    tx_payload["tax_tag_code"] = q_tax_code
                tx_payload.update(_proof_payload(q_proof))
                add_transaction(month_key, tx_payload)
                st.session_state["dash_quick_open"] = False
                st.session_state["dash_quick_form"] = default_quick_form.copy()
                st.session_state["dash_q_proof_nonce"] = int(st.session_state.get("dash_q_proof_nonce", 0)) + 1
                st.session_state["dash_quick_reset"] = True
                _toast(t("تمت إضافة المعاملة.", "Transaction added."))
                st.rerun()
            else:
                _toast(t("أدخل مبلغًا أكبر من 0.", "Enter amount greater than 0."), level="warning")
