import base64

import pandas as pd
import streamlit as st

from config_floosy import arabic_months, english_months, get_all_transactions_df, get_logo_bytes, get_saving_totals
from repositories.session_repo import SessionStateRepository
from services.financial_analyzer import FinancialAnalyzer


def render(month_key: str, month: str, year: int):
    """Dashboard page entry point. App expects this function."""

    settings = st.session_state.settings
    currency = settings.get("default_currency", "د.ك")
    is_en = settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month

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
            (t("الرصيد الحالي", "Current Balance"), f"{account_balance:,.0f} {currency_view}"),
            (t("دخل هذا الشهر", "Income This Month"), f"{month_income:,.0f} {currency_view}"),
            (t("مصروف هذا الشهر", "Expenses This Month"), f"{month_expenses:,.0f} {currency_view}"),
        ])
    if show_saving:
        metric_items.append((t("رصيد التوفير", "Savings Balance"), f"{saving_balance:,.0f} {currency_view}"))
    if show_project:
        metric_items.append((t("صافي المشاريع هذا الشهر", "Projects Net This Month"), f"{project_net_month:,.0f} {currency_view}"))

    if not metric_items:
        st.info(t("كل بطاقات الملخص مخفية من الإعدادات.", "All summary cards are hidden in settings."))
    else:
        for i in range(0, len(metric_items), 2):
            row_items = metric_items[i:i + 2]
            cols = st.columns(len(row_items))
            for col, (label, value) in zip(cols, row_items):
                with col:
                    st.metric(label, value)

    analyzer = FinancialAnalyzer(SessionStateRepository())
    brief = analyzer.dashboard_brief(st.session_state, month_key, currency)

    st.markdown("### " + t("الملخص الذكي", "Smart Summary"))
    brief_message = brief["message_en"] if is_en else brief["message_ar"]
    brief_detail = brief["detail_en"] if is_en else brief["detail_ar"]
    focus_label = brief["focus_label_en"] if is_en else brief["focus_label_ar"]
    support_label = brief["support_label_en"] if is_en else brief["support_label_ar"]
    focus_value = f"{brief.get('focus_value', 0.0):,.0f} {currency_view}"
    support_value = f"{brief.get('support_value', 0.0):,.0f} {currency_view}"

    st.markdown(
        f"""
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-right:6px solid #2c5f87;border-radius:12px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-weight:700;font-size:1.02rem;">{brief_message}</div>
            <div style="color:#4b5563;font-size:0.92rem;margin-top:4px;">{brief_detail}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
                <div style="background:#f8fafc;border:1px solid #dbe3ea;border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                    <span style="color:#64748b;">{focus_label}:</span>
                    <span style="font-weight:700;color:#0f172a;"> {focus_value}</span>
                </div>
                <div style="background:#f8fafc;border:1px solid #dbe3ea;border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                    <span style="color:#64748b;">{support_label}:</span>
                    <span style="font-weight:700;color:#0f172a;"> {support_value}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(t("فتح المحلل المالي", "Open Financial Analyzer"), key="open_assistant_from_dashboard"):
        st.session_state.current_page = "assistant"
        st.rerun()
