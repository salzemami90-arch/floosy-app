from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from config_floosy import arabic_months, english_months, load_transactions
from services.i18n import make_t, get_lang_code, get_months
from repositories.session_repo import SessionStateRepository
from services.cash_flow_engine import CashFlowEngine
from services.financial_analyzer import FinancialAnalyzer


def _previous_month_key(current_month: str, current_year: int) -> str:
    month_idx = arabic_months.index(current_month)
    if month_idx == 0:
        return f"{current_year - 1}-{arabic_months[-1]}"
    return f"{current_year}-{arabic_months[month_idx - 1]}"


def _section_label(title: str, summary: str = "") -> str:
    return f"{title} | {summary}" if summary else title


def _quick_take_theme(status: str) -> dict:
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


def _card_colors(value: float) -> dict:
    if value > 0:
        return {"bg": "#EAF5EF", "border": "#047857", "label": "#065F46", "value": "#064E3B"}
    if value < 0:
        return {"bg": "#FEF2F2", "border": "#EF4444", "label": "#991B1B", "value": "#7F1D1D"}
    return {"bg": "#FFFBEB", "border": "#F59E0B", "label": "#92400E", "value": "#78350F"}


def _render_action_card(title: str, value_text: str, delta_text: str, net_value: float, is_ltr: bool) -> None:
    colors = _card_colors(net_value)
    accent_side = "border-left" if is_ltr else "border-right"
    text_dir = "ltr" if is_ltr else "rtl"
    text_align = "left" if is_ltr else "right"
    st.markdown(
        f"""
        <div style="
          border-radius:14px;padding:14px 16px;border:1px solid {colors['border']};
          {accent_side}:5px solid {colors['border']};background:{colors['bg']};
          direction:{text_dir};text-align:{text_align};
        ">
          <div style="font-size:0.85rem;font-weight:700;color:{colors['label']};">{title}</div>
          <div style="font-size:1.35rem;font-weight:800;color:{colors['value']};">{value_text}</div>
          <div style="font-size:0.78rem;color:{colors['label']};margin-top:4px;">{delta_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(month_key: str, month: str, year: int):
    _lc = get_lang_code()
    is_en = _lc == "en"
    is_ltr = _lc != "ar"
    t = make_t()
    _display_months = get_months()
    month_display = _display_months[arabic_months.index(month)] if (_lc != "ar" and month in arabic_months) else month

    st.title(t("المحلل المالي", "Financial Analyzer"))
    st.caption(
        t(
            f"تحليل شهر {month_display} {year} مقارنة بالشهر السابق",
            f"Analysis for {month_display} {year} compared to previous month",
        )
    )

    currency = st.session_state.settings.get("default_currency", "د.ك")
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_ltr else currency_symbol

    repo = SessionStateRepository()
    analyzer = FinancialAnalyzer(repo)
    cash_flow_engine = CashFlowEngine(repo)

    current_tx = load_transactions(month_key)
    previous_month_key = _previous_month_key(month, year)
    previous_tx = load_transactions(previous_month_key)

    current = analyzer.totals_by_currency(current_tx, currency)
    previous = analyzer.totals_by_currency(previous_tx, currency)
    comparison = analyzer.compare_totals(current, previous)

    recurring_items = st.session_state.get("recurring", {}).get("items", [])
    active_items = [item for item in recurring_items if item.get("active", True)]
    coverage = analyzer.recurring_coverage(active_items, month_key, currency)

    projected_net_after_pending = current["net"] + coverage["net_coverage"]

    cash_flow = cash_flow_engine.cash_flow_90d(
        st.session_state,
        currency,
        as_of=date.today(),
        horizon_days=90,
    )
    actual_90 = cash_flow["actual_last_90"]
    projected_90 = cash_flow["projected_next_90"]
    carry_over = cash_flow["carry_over"]
    comparison_90 = cash_flow["comparison_vs_last_90"]
    components_90 = cash_flow["components"]

    savings = analyzer.savings_summary(st.session_state, month_key)
    project = analyzer.projects_summary(st.session_state, month_key)
    docs = analyzer.documents_summary(st.session_state)
    project_impact = analyzer.project_impact_on_personal(st.session_state, month_key, currency)
    seasonal = analyzer.seasonal_expense_summary(st.session_state, currency, limit_months=6)
    category_signal = analyzer.seasonal_category_signal(st.session_state, month_key, currency, history_months=6)

    # ── Zone A: AI Quick Take ─────────────────────────────────────────────
    brief = analyzer.dashboard_brief(st.session_state, month_key, currency)
    brief_status = str(brief.get("status", "stable") or "stable")

    show_spending_note_on_good = brief_status == "spending_high" and float(brief.get("focus_value", 0.0)) >= 0
    theme = _quick_take_theme("stable" if show_spending_note_on_good else brief_status)
    border_side = "border-left" if is_ltr else "border-right"

    if show_spending_note_on_good:
        brief_message = t("الوضع المالي تحت السيطرة", "Financial position is under control")
        brief_detail = t(
            "صافي 90 يوم ما زال إيجابيًا، لكن مصروف هذا الشهر أعلى من المعتاد.",
            "Your 90-day net is still positive, but this month's spending is above usual.",
        )
    else:
        brief_message = brief["message_en"] if is_ltr else brief["message_ar"]
        brief_detail = brief["detail_en"] if is_ltr else brief["detail_ar"]

    focus_label = brief["focus_label_en"] if is_ltr else brief["focus_label_ar"]
    support_label = brief["support_label_en"] if is_ltr else brief["support_label_ar"]
    focus_value = f"{brief.get('focus_value', 0.0):,.0f} {currency_view}"
    support_value = f"{brief.get('support_value', 0.0):,.0f} {currency_view}"

    st.markdown(
        f"### {t('نظرة سريعة', 'Quick Take')}",
    )

    if brief_status == "empty":
        st.info(
            t(
                "أضف أول حركة مالية لتفعيل التحليل.",
                "Add your first transaction to activate the analysis.",
            )
        )
    else:
        st.markdown(
            f"""
            <div style="background:{theme['background']};border:1px solid {theme['pill_border']};{border_side}:6px solid {theme['border']};border-radius:12px;padding:12px 14px;margin-bottom:8px;">
                <div style="font-weight:700;font-size:1.08rem;color:{theme['text']};">{brief_message}</div>
                <div style="color:{theme['label']};font-size:0.92rem;margin-top:4px;">{brief_detail}</div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
                    <div style="background:{theme['pill_bg']};border:1px solid {theme['pill_border']};border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                        <span style="color:{theme['label']};">{focus_label}:</span>
                        <span style="font-weight:700;color:{theme['pill_text']};"> {focus_value}</span>
                    </div>
                    <div style="background:{theme['pill_bg']};border:1px solid {theme['pill_border']};border-radius:999px;padding:6px 10px;font-size:0.85rem;">
                        <span style="color:{theme['label']};">{support_label}:</span>
                        <span style="font-weight:700;color:{theme['pill_text']};"> {support_value}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Thin-data calm caption
    tx_by_month = st.session_state.get("transactions", {})
    tx_count = sum(len(txs or []) for txs in tx_by_month.values()) if isinstance(tx_by_month, dict) else 0
    if 0 < tx_count < 5 and seasonal.get("history_month_count", 0) < 2:
        st.caption(
            t(
                "بيانات محدودة — ستتحسن الرؤى بإضافة المزيد من المعاملات.",
                "Limited data — insights will improve as you add more transactions.",
            )
        )

    # ── Zone B: 3 Action Cards ────────────────────────────────────────────
    if brief_status != "empty":
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            _render_action_card(
                title=t("هذا الشهر", "This Month"),
                value_text=f"{current['net']:,.2f} {currency_view}",
                delta_text=f"{comparison['net_delta']:+,.2f} ({comparison['net_delta_pct']:+.1f}%)",
                net_value=current["net"],
                is_ltr=is_ltr,
            )
        with ac2:
            _render_action_card(
                title=t("الاستحقاقات", "Entitlements"),
                value_text=f"{coverage['net_coverage']:,.2f} {currency_view}",
                delta_text=t(
                    f"{coverage['overdue_count']} متأخر · {coverage['expected_count']} متوقع",
                    f"{coverage['overdue_count']} overdue · {coverage['expected_count']} expected",
                ),
                net_value=coverage["net_coverage"],
                is_ltr=is_ltr,
            )
        with ac3:
            _render_action_card(
                title=t("90 يوم", "90-Day Outlook"),
                value_text=f"{projected_90['net']:,.2f} {currency_view}",
                delta_text=t(
                    f"{comparison_90['net_delta']:+,.2f} عن آخر 90 يوم",
                    f"{comparison_90['net_delta']:+,.2f} vs last 90 days",
                ),
                net_value=projected_90["net"],
                is_ltr=is_ltr,
            )
        st.markdown("")

    # ── Zone C: Upcoming Items (above the fold) ──────────────────────────
    upcoming_items = cash_flow.get("upcoming_items", [])
    if upcoming_items:
        source_labels = {
            "recurring": t("قالب متكرر", "Recurring"),
            "invoice": t("فاتورة", "Invoice"),
            "document": t("مستند", "Document"),
            "transaction": t("معاملة", "Transaction"),
        }
        type_labels = {
            "income": t("دخل", "Income"),
            "expense": t("مصروف", "Expense"),
        }
        upcoming_df = pd.DataFrame(
            [
                {
                    t("التاريخ", "Date"): item["due_date_iso"],
                    t("المصدر", "Source"): source_labels.get(item.get("source", ""), item.get("source", "")),
                    t("النوع", "Type"): type_labels.get(item.get("type", ""), item.get("type", "")),
                    t("العنصر", "Item"): item.get("name", ""),
                    t("الحالة", "Status"): item.get("status", ""),
                    t("المبلغ", "Amount"): f"{item['amount']:,.2f} {currency_view}",
                }
                for item in upcoming_items
            ]
        )
        st.markdown(f"#### {t('أقرب العناصر القادمة', 'Upcoming Items')}")
        st.dataframe(upcoming_df, hide_index=True)

    # ── Zone D: Detail Expanders (below the fold) ────────────────────────
    st.markdown(f"### {t('التفاصيل', 'Details')}")

    with st.expander(
        _section_label(
            t("ملخص هذا الشهر", "This Month Overview"),
            f"{t('الصافي', 'Net')} {current['net']:,.2f} {currency_view}",
        ),
        expanded=False,
    ):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                t("الدخل", "Income"),
                f"{current['income']:,.2f} {currency_view}",
                delta=f"{comparison['income_delta']:+,.2f} ({comparison['income_delta_pct']:+.1f}%)",
            )
        with c2:
            st.metric(
                t("المصاريف", "Expenses"),
                f"{current['expense']:,.2f} {currency_view}",
                delta=f"{comparison['expense_delta']:+,.2f} ({comparison['expense_delta_pct']:+.1f}%)",
                delta_color="inverse",
            )
        with c3:
            st.metric(
                t("الصافي", "Net"),
                f"{current['net']:,.2f} {currency_view}",
                delta=f"{comparison['net_delta']:+,.2f} ({comparison['net_delta_pct']:+.1f}%)",
            )

        s1, s2 = st.columns(2)
        with s1:
            st.write(t(f"عدد معاملات هذا الشهر: **{current['count']}**", f"Transactions this month: **{current['count']}**"))
        with s2:
            st.write(t(f"عدد معاملات الشهر السابق: **{previous['count']}**", f"Transactions previous month: **{previous['count']}**"))

    with st.expander(
        _section_label(
            t("الاستحقاقات والتغطية", "Entitlements and Coverage"),
            f"{t('صافي التغطية', 'Coverage Net')} {coverage['net_coverage']:,.2f} {currency_view}",
        ),
        expanded=False,
    ):
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric(t("عدد العناصر الشهرية المفعلة", "Active Monthly Items"), f"{len(active_items)}")
        with r2:
            st.metric(t("إجمالي الدخل المتوقع غير المستلم", "Total Expected Income Not Received"), f"{coverage['expected_income']:,.2f} {currency_view}")
        with r3:
            st.metric(t("إجمالي الالتزامات المتأخرة", "Total Overdue Commitments"), f"{coverage['overdue_commitments']:,.2f} {currency_view}")

        st.caption(
            t(
                f"الفعلي المسجل الآن: دخل {current['income']:,.2f} / مصاريف {current['expense']:,.2f}. "
                f"غير المؤكد (دخل متوقع {coverage['expected_income']:,.2f} - التزامات {coverage['overdue_commitments']:,.2f}) لا يدخل في الفعلي إلا بعد التأكيد.",
                f"Recorded now: income {current['income']:,.2f} / expenses {current['expense']:,.2f}. "
                f"Unconfirmed values (expected income {coverage['expected_income']:,.2f} - commitments {coverage['overdue_commitments']:,.2f}) are not included in actual totals until confirmed.",
            )
        )

        u1, u2, u3 = st.columns(3)
        with u1:
            st.metric(t("الصافي الفعلي الآن", "Actual Net Now"), f"{current['net']:,.2f} {currency_view}")
        with u2:
            st.metric(
                t("صافي الاستحقاقات غير المؤكدة", "Unconfirmed Entitlement Net"),
                f"{coverage['net_coverage']:,.2f} {currency_view}",
                delta=t(
                    f"دخل متوقع {coverage['expected_income']:,.2f} - التزامات {coverage['overdue_commitments']:,.2f}",
                    f"Expected income {coverage['expected_income']:,.2f} - commitments {coverage['overdue_commitments']:,.2f}",
                ),
                delta_color="off",
            )
        with u3:
            st.metric(
                t("صافي متوقع بعد التحصيل/السداد", "Expected Net After Settle"),
                f"{projected_net_after_pending:,.2f} {currency_view}",
                delta=t("تقدير", "Estimate"),
                delta_color="off",
            )

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(
                t("التزامات متأخرة (غير مسددة)", "Overdue Commitments (Unpaid)"),
                f"{coverage['overdue_commitments']:,.2f} {currency_view}",
                delta=t(
                    f"{coverage['overdue_count']} عنصر | {coverage.get('overdue_pending_months', coverage['overdue_count'])} شهر",
                    f"{coverage['overdue_count']} item(s) | {coverage.get('overdue_pending_months', coverage['overdue_count'])} month(s)",
                ),
                delta_color="inverse",
            )
        with k2:
            st.metric(
                t("دخل متوقع غير مستلم", "Expected Income Not Received"),
                f"{coverage['expected_income']:,.2f} {currency_view}",
                delta=t(
                    f"{coverage['expected_count']} عنصر | {coverage.get('expected_pending_months', coverage['expected_count'])} شهر",
                    f"{coverage['expected_count']} item(s) | {coverage.get('expected_pending_months', coverage['expected_count'])} month(s)",
                ),
            )
        with k3:
            st.metric(
                t("صافي تغطية الاستحقاقات", "Entitlement Coverage Net"),
                f"{coverage['net_coverage']:,.2f} {currency_view}",
            )

        if coverage["net_coverage"] > 0:
            st.success(t("التغطية المستقبلية إيجابية بعد التحصيل.", "Future coverage is positive after collection."))
        elif coverage["net_coverage"] < 0:
            st.warning(t("في فجوة تغطية حالياً وتحتاج متابعة.", "There is a current coverage gap that needs follow-up."))
        else:
            st.info(t("الوضع متعادل تقريباً بين الالتزامات والدخل المتوقع.", "The situation is nearly balanced between commitments and expected income."))

    with st.expander(
        _section_label(
            t("تدفق نقدي 90 يوم", "90-Day Cash Flow"),
            f"{t('صافي متوقع', 'Projected Net')} {projected_90['net']:,.2f} {currency_view}",
        ),
        expanded=False,
    ):
        f1, f2, f3 = st.columns(3)
        with f1:
            st.metric(
                t("صافي آخر 90 يوم", "Net Last 90 Days"),
                f"{actual_90['net']:,.2f} {currency_view}",
                delta=t(
                    f"دخل {actual_90['income']:,.2f} | مصروف {actual_90['expense']:,.2f}",
                    f"Income {actual_90['income']:,.2f} | Expense {actual_90['expense']:,.2f}",
                ),
                delta_color="off",
            )
        with f2:
            st.metric(
                t("صافي متوقع خلال 90 يوم", "Projected Net Next 90 Days"),
                f"{projected_90['net']:,.2f} {currency_view}",
                delta=t(
                    f"دخل {projected_90['income']:,.2f} | مصروف {projected_90['expense']:,.2f}",
                    f"Income {projected_90['income']:,.2f} | Expense {projected_90['expense']:,.2f}",
                ),
                delta_color="off",
            )
        with f3:
            st.metric(
                t("الفرق عن آخر 90 يوم", "Delta vs Last 90 Days"),
                f"{comparison_90['net_delta']:+,.2f} {currency_view}",
                delta=t("تقديري", "Estimate"),
                delta_color="normal" if comparison_90["net_delta"] >= 0 else "inverse",
            )

        g1, g2, g3 = st.columns(3)
        with g1:
            st.metric(
                t("المتكرر المتوقع", "Recurring Planned"),
                f"{(components_90['recurring_income'] - components_90['recurring_expense']):,.2f} {currency_view}",
                delta=t(
                    f"دخل {components_90['recurring_income']:,.2f} | مصروف {components_90['recurring_expense']:,.2f}",
                    f"Income {components_90['recurring_income']:,.2f} | Expense {components_90['recurring_expense']:,.2f}",
                ),
                delta_color="off",
            )
        with g2:
            st.metric(
                t("تحصيل فواتير متوقع", "Open Invoice Inflow"),
                f"{components_90['invoice_income']:,.2f} {currency_view}",
                delta=t(
                    f"متأخر حالي {carry_over['overdue_open_invoice_total']:,.2f}",
                    f"Current overdue {carry_over['overdue_open_invoice_total']:,.2f}",
                ),
                delta_color="off",
            )
        with g3:
            st.metric(
                t("رسوم مستندات قريبة", "Upcoming Document Fees"),
                f"{components_90['document_expense']:,.2f} {currency_view}",
                delta=t(
                    f"متأخر حالي {carry_over['overdue_document_fee_total']:,.2f}",
                    f"Current overdue {carry_over['overdue_document_fee_total']:,.2f}",
                ),
                delta_color="inverse" if components_90["document_expense"] > 0 else "normal",
            )

        st.caption(
            t(
                "آخر 90 يوم = الفعلي المسجل فقط. الـ 90 يوم القادمة = المتوقع من المتكرر والفواتير المفتوحة ورسوم المستندات. الاستحقاقات الحالية تبقى منفصلة للوضوح.",
                "Last 90 days = recorded actual movement only. Next 90 days = projection from recurring items, open invoices, and upcoming document fees. Current entitlements stay separate for clarity.",
            )
        )

        h1, h2, h3 = st.columns(3)
        with h1:
            st.metric(
                t("صافي الاستحقاقات الحالية", "Current Entitlement Net"),
                f"{carry_over['recurring_delayed_net']:,.2f} {currency_view}",
                delta=t(
                    f"دخل متوقع {carry_over['delayed_income']:,.2f} | التزامات {carry_over['overdue_commitments']:,.2f}",
                    f"Expected income {carry_over['delayed_income']:,.2f} | commitments {carry_over['overdue_commitments']:,.2f}",
                ),
                delta_color="off",
            )
        with h2:
            st.metric(
                t("فواتير متأخرة مفتوحة", "Overdue Open Invoices"),
                f"{carry_over['overdue_open_invoice_total']:,.2f} {currency_view}",
                delta=t(
                    f"{carry_over['overdue_open_invoice_count']} فاتورة",
                    f"{carry_over['overdue_open_invoice_count']} invoice(s)",
                ),
                delta_color="off",
            )
        with h3:
            st.metric(
                t("رسوم مستندات متأخرة", "Overdue Document Fees"),
                f"{carry_over['overdue_document_fee_total']:,.2f} {currency_view}",
                delta=t(
                    f"{carry_over['overdue_document_count']} مستند",
                    f"{carry_over['overdue_document_count']} document(s)",
                ),
                delta_color="inverse" if carry_over["overdue_document_fee_total"] > 0 else "normal",
            )

        monthly_projection_rows = cash_flow.get("monthly_projection", [])
        if monthly_projection_rows:
            monthly_projection_df = pd.DataFrame(
                [
                    {
                        t("الفترة", "Period"): f"{row['year']:04d}-{row['month']:02d}",
                        t("الدخل المتوقع", "Projected Income"): f"{row['income']:,.2f} {currency_view}",
                        t("المصروف المتوقع", "Projected Expense"): f"{row['expense']:,.2f} {currency_view}",
                        t("الصافي المتوقع", "Projected Net"): f"{row['net']:,.2f} {currency_view}",
                        t("عدد العناصر", "Items"): row["count"],
                    }
                    for row in monthly_projection_rows
                ]
            )
            st.markdown(f"#### {t('تقسيم 90 يوم حسب الشهر', '90-Day Monthly Split')}")
            st.dataframe(monthly_projection_df, hide_index=True)

    with st.expander(
        _section_label(
            t("التوفير والمشاريع", "Savings and Projects"),
            f"{t('صافي المشاريع', 'Projects Net')} {project['month_net']:,.2f} {currency_view}",
        ),
        expanded=False,
    ):
        p1, p2, p3 = st.columns(3)
        with p1:
            st.metric(t("صافي التوفير (كل الشهور)", "Savings Net (All Months)"), f"{savings['all_net']:,.2f} {currency_view}")
        with p2:
            st.metric(t("صافي المشاريع لهذا الشهر", "Projects Net This Month"), f"{project['month_net']:,.2f} {currency_view}")
        with p3:
            st.metric(
                t("صافي المشاريع (كل الشهور)", "Projects Net (All Months)"),
                f"{project['all_net']:,.2f} {currency_view}",
                delta=t(f"{project['all_count']} معاملة", f"{project['all_count']} transaction(s)"),
            )

        x1, x2, x3 = st.columns(3)
        with x1:
            st.metric(
                t("الدعم المطلوب للمشاريع", "Estimated Project Support"),
                f"{project_impact['estimated_personal_support']:,.2f} {currency_view}",
                delta=t(
                    f"عجز 3 أشهر: {project_impact['last_3m_project_deficit']:,.2f}",
                    f"3M deficit: {project_impact['last_3m_project_deficit']:,.2f}",
                ),
                delta_color="inverse",
            )
        with x2:
            st.metric(
                t("صافي الحساب قبل الدعم", "Personal Net Before Support"),
                f"{project_impact['personal_net']:,.2f} {currency_view}",
            )
        with x3:
            st.metric(
                t("صافي الحساب بعد دعم المشاريع", "Personal Net After Support"),
                f"{project_impact['personal_net_after_support']:,.2f} {currency_view}",
                delta=t(
                    f"شهور عجز آخر 3: {project_impact['deficit_months_in_last_3']}",
                    f"Deficit months in last 3: {project_impact['deficit_months_in_last_3']}",
                ),
                delta_color="inverse" if project_impact["personal_net_after_support"] < 0 else "normal",
            )

    with st.expander(
        _section_label(
            t("السلوك الموسمي للمصاريف", "Seasonal Expense Behavior"),
            f"{t('مصروف الشهر', 'Current Expense')} {seasonal['current_expense']:,.2f} {currency_view}",
        ),
        expanded=False,
    ):
        z1, z2, z3 = st.columns(3)
        with z1:
            st.metric(
                t("مصروف آخر شهر", "Current Expense"),
                f"{seasonal['current_expense']:,.2f} {currency_view}",
                delta=f"{seasonal['delta_from_avg']:+,.2f} ({seasonal['delta_pct']:+.1f}%)",
                delta_color="inverse",
            )
        with z2:
            st.metric(
                t("متوسط 6 أشهر", "6-Month Average"),
                f"{seasonal['average_expense']:,.2f} {currency_view}",
            )
        with z3:
            st.metric(
                t("أعلى شهر صرف", "Peak Expense Month"),
                f"{seasonal['peak_expense']:,.2f} {currency_view}",
                delta=seasonal["peak_month"],
                delta_color="off",
            )

        if seasonal["status"] == "high":
            st.info(t("مصاريفك أعلى من متوسط آخر 6 أشهر.", "Your spending is above the 6-month average."))
        elif seasonal["status"] == "low":
            st.info(t("مصاريفك أقل من متوسط آخر 6 أشهر.", "Your spending is below the 6-month average."))
        else:
            st.info(t("مصاريفك قريبة من متوسطك المعتاد.", "Your spending is close to your usual average."))

        if category_signal["top_category"]:
            if category_signal["status"] == "high":
                st.caption(
                    t(
                        f"أعلى تصنيف صرف الآن: {category_signal['top_category']} وهو أعلى من متوسطه السابق.",
                        f"Top expense category now: {category_signal['top_category']}, and it is above its previous average.",
                    )
                )
            elif category_signal["status"] == "low":
                st.caption(
                    t(
                        f"أعلى تصنيف صرف الآن: {category_signal['top_category']} وهو أقل من متوسطه السابق.",
                        f"Top expense category now: {category_signal['top_category']}, and it is below its previous average.",
                    )
                )
            else:
                st.caption(
                    t(
                        f"أعلى تصنيف صرف الآن: {category_signal['top_category']} وهو قريب من المتوسط.",
                        f"Top expense category now: {category_signal['top_category']}, and it is near average.",
                    )
                )

    with st.expander(
        _section_label(
            t("المستندات", "Documents"),
            f"{t('عدد المستندات', 'Documents Count')} {docs['count']}",
        ),
        expanded=False,
    ):
        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric(t("عدد المستندات", "Documents Count"), f"{docs['count']}")
        with d2:
            st.metric(t("تنتهي خلال 30 يوم", "Expiring in 30 Days"), f"{docs['upcoming_30_count']}")
        with d3:
            st.metric(
                t("رسوم سنوية تقديرية", "Estimated Annual Fees"),
                f"{docs['annual_fees_estimate']:,.2f} {currency_view}",
                delta=t(f"منتهي: {docs['expired_count']}", f"Expired: {docs['expired_count']}"),
                delta_color="inverse" if docs["expired_count"] > 0 else "normal",
            )

    st.caption(t(f"آخر تحديث: {date.today().isoformat()}", f"Last update: {date.today().isoformat()}"))
