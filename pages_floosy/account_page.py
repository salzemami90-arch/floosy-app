from __future__ import annotations

from datetime import datetime
import html

import pandas as pd
import streamlit as st

from config_floosy import CURRENCY_OPTIONS, add_transaction, arabic_months, english_months, load_transactions
from services.expense_tax_service import ExpenseTaxService
from services.transaction_categories import category_label, localized_all_categories


TX_TYPE_AR_TO_EN = {"دخل": "Income", "مصروف": "Expense"}
TX_TYPE_EN_TO_AR = {v: k for k, v in TX_TYPE_AR_TO_EN.items()}
CURRENCY_OPTION_AR_TO_EN = {
    "د.ك - دينار كويتي": "KWD - Kuwaiti Dinar",
    "ر.س - ريال سعودي": "SAR - Saudi Riyal",
    "د.إ - درهم إماراتي": "AED - UAE Dirham",
    "$ - دولار أمريكي": "USD - US Dollar",
    "€ - يورو": "EUR - Euro",
}

def _render_account_summary_styles() -> None:
    st.markdown(
        """
        <style>
        .floosy-account-summary-card {
            border-radius: 16px;
            padding: 16px 18px 14px 18px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.8rem;
            background: #ffffff;
            position: relative;
            overflow: hidden;
        }

        .floosy-account-summary-card--remaining {
            min-height: 118px;
            background: linear-gradient(135deg, #164c72 0%, #1f7a92 55%, #2aa47c 100%);
            color: #f8fafc;
            border-color: rgba(255, 255, 255, 0.16);
        }

        .floosy-account-summary-card--income {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-account-summary-card--expense {
            --label-color: #475569;
            --value-color: #0f172a;
        }

        .floosy-account-summary-card__accent {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 6px;
            background: linear-gradient(180deg, #164c72 0%, #1f7a92 55%, #2aa47c 100%);
        }

        .floosy-account-summary-card__label {
            font-size: 0.88rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
            color: var(--label-color, #475569);
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            line-height: 1.2;
        }

        .floosy-account-summary-card__label-icon {
            font-size: 0.82rem;
            line-height: 1;
            opacity: 0.8;
            flex: 0 0 auto;
        }

        .floosy-account-summary-card__value {
            font-size: 1.46rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.02em;
            color: var(--value-color, #0f172a);
        }

        .floosy-account-summary-card__currency {
            font-size: 0.8em;
            font-weight: 700;
            color: #64748b;
            opacity: 0.88;
        }

        .floosy-account-summary-card--remaining .floosy-account-summary-card__label,
        .floosy-account-summary-card--remaining .floosy-account-summary-card__value {
            color: #ffffff;
        }

        .floosy-account-summary-card--remaining .floosy-account-summary-card__currency {
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
        f'<span class="floosy-account-summary-card__currency">{html.escape(currency_part)}</span>'
    )


def _metric_label_html(label: str, tone: str, is_en: bool) -> str:
    icon_map = {
        "remaining": "◎",
        "income": "↗",
        "expense": "↘",
    }
    icon = html.escape(icon_map.get(tone, "•"))
    text = html.escape(label)
    icon_html = f'<span class="floosy-account-summary-card__label-icon" aria-hidden="true">{icon}</span>'
    text_html = f"<span>{text}</span>"
    return f"{icon_html}{text_html}" if is_en else f"{text_html}{icon_html}"


def _render_account_summary_card(label: str, value: str, tone: str, is_en: bool) -> None:
    direction = "ltr" if is_en else "rtl"
    align = "left" if is_en else "right"
    accent_side = "left" if is_en else "right"
    accent_html = "" if tone == "remaining" else f'<div class="floosy-account-summary-card__accent" style="{accent_side}:0;"></div>'
    card_markup = (
        f'<div class="floosy-account-summary-card floosy-account-summary-card--{tone}" '
        f'style="direction:{direction};text-align:{align};">'
        f"{accent_html}"
        f'<div class="floosy-account-summary-card__label">{_metric_label_html(label, tone, is_en)}</div>'
        f'<div class="floosy-account-summary-card__value">{_metric_value_html(value)}</div>'
        "</div>"
    )

    st.markdown(card_markup, unsafe_allow_html=True)


def _tx_type_label(value: str, is_en: bool) -> str:
    clean_value = str(value or "").strip()
    if not is_en:
        if clean_value in TX_TYPE_EN_TO_AR:
            return TX_TYPE_EN_TO_AR[clean_value]
        return clean_value
    if clean_value in TX_TYPE_AR_TO_EN:
        return TX_TYPE_AR_TO_EN[clean_value]
    return clean_value


def _currency_option_label(value: str, is_en: bool) -> str:
    clean_value = str(value or "").strip()
    if not is_en:
        return clean_value
    return CURRENCY_OPTION_AR_TO_EN.get(clean_value, clean_value)


def _currency_short_label(value: str, is_en: bool) -> str:
    clean_value = str(value or "").strip()
    symbol = clean_value.split(" - ")[0] if " - " in clean_value else clean_value
    if not is_en:
        return symbol
    return {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}.get(symbol, symbol)


def _category_label(value: str, is_en: bool) -> str:
    return category_label(value, is_en)


def _build_filtered_df(
    tx_list: list[dict],
    currency: str,
    query: str,
    type_filter: str,
    category_filter: str,
    newest_first: bool = True,
) -> pd.DataFrame:
    if not tx_list:
        return pd.DataFrame()

    df = pd.DataFrame(tx_list).copy()
    df["tx_id"] = df.index
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["note"] = df["note"].fillna("")

    # same behavior as existing summary: focus on selected currency
    df = df[df["currency"] == currency].copy()
    if df.empty:
        return pd.DataFrame()

    if type_filter != "الكل":
        df = df[df["type"] == type_filter]

    if category_filter != "الكل":
        df = df[df["category"] == category_filter]

    q = query.strip().lower()
    if q:
        df = df[
            df["category"].astype(str).str.lower().str.contains(q, na=False)
            | df["note"].astype(str).str.lower().str.contains(q, na=False)
            | df["date"].astype(str).str.lower().str.contains(q, na=False)
        ]

    ascending = [not newest_first, not newest_first]
    return df.sort_values(by=["date_dt", "tx_id"], ascending=ascending)


def _month_key_from_date(dt: datetime) -> str:
    return f"{dt.year}-{arabic_months[dt.month - 1]}"


def _month_label_from_key(month_key: str, is_en: bool) -> str:
    if "-" not in month_key:
        return month_key
    year_txt, month_name = month_key.split("-", 1)
    if is_en and month_name in arabic_months:
        month_name = english_months[arabic_months.index(month_name)]
    return f"{month_name} {year_txt}"


def _sort_month_keys(keys: list[str]) -> list[str]:
    def _key(mk: str):
        if "-" not in mk:
            return (9999, 99)
        y, m = mk.split("-", 1)
        try:
            return (int(y), arabic_months.index(m) + 1 if m in arabic_months else 99)
        except ValueError:
            return (9999, 99)

    return sorted(keys, key=_key)


def _ensure_pending_month(item: dict, month_key: str) -> None:
    pending = item.setdefault("pending_entitlements", [])
    if not isinstance(pending, list):
        item["pending_entitlements"] = []
        pending = item["pending_entitlements"]

    if month_key not in pending and item.get("last_paid_month") != month_key:
        pending.append(month_key)
        item["pending_entitlements"] = _sort_month_keys(pending)


def render(month_key: str, month: str, year: int):
    is_en = st.session_state.settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month
    save_notice = st.session_state.pop("account_save_notice", "")

    if save_notice:
        st.success(save_notice)

    st.session_state.setdefault("account_templates_open", False)

    def _close_templates_panel():
        st.session_state["account_templates_open"] = False
    st.markdown(
        """
        <style>
        div.st-key-account_templates_toggle_top button {
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
        </style>
        """,
        unsafe_allow_html=True,
    )
    title_col, action_col = st.columns([5, 2])
    with title_col:
        st.title(t("الحساب", "Account"))
        st.caption(f"{month_display} {year}")
    with action_col:
        if st.button(
            t("إخفاء العناصر الشهرية", "Hide Monthly Items")
            if st.session_state["account_templates_open"]
            else t("إدارة العناصر الشهرية", "Manage Monthly Items"),
            key="account_templates_toggle_top",
            help=t("إضافة أو تعديل الالتزامات والدخل الشهري", "Add or edit monthly commitments and income"),
            use_container_width=True,
        ):
            st.session_state["account_templates_open"] = not bool(st.session_state.get("account_templates_open", False))
            st.rerun()

    tx_list = load_transactions(month_key)
    currency = st.session_state.settings.get("default_currency", CURRENCY_OPTIONS[0])
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol
    tax_options = ExpenseTaxService.expense_options(st.session_state, is_en=is_en)
    tax_codes = [opt["code"] for opt in tax_options]
    tax_label_by_code = {opt["code"]: opt["label"] for opt in tax_options}
    default_expense_tax_code = next((opt["code"] for opt in tax_options if opt.get("deductible")), tax_codes[0] if tax_codes else "")

    df_all = pd.DataFrame(tx_list) if tx_list else pd.DataFrame()
    total_income = 0.0
    total_expense = 0.0
    if not df_all.empty:
        df_k = df_all[df_all["currency"] == currency]
        total_income = float(df_k[df_k["type"] == "دخل"]["amount"].sum())
        total_expense = float(df_k[df_k["type"] == "مصروف"]["amount"].sum())

    _render_account_summary_styles()
    _render_account_summary_card(
        t("المتبقي", "Remaining"),
        f"{(total_income - total_expense):,.0f} {currency_view}",
        "remaining",
        is_en=is_en,
    )

    c1, c2 = st.columns(2)
    with c1:
        _render_account_summary_card(
            t("إجمالي الدخل", "Total Income"),
            f"{total_income:,.0f} {currency_view}",
            "income",
            is_en=is_en,
        )
    with c2:
        _render_account_summary_card(
            t("إجمالي المصاريف", "Total Expenses"),
            f"{total_expense:,.0f} {currency_view}",
            "expense",
            is_en=is_en,
        )

    st.markdown("---")

    recurring_items = st.session_state.setdefault("recurring", {}).setdefault("items", [])

    st.markdown(f"### {t('الالتزامات والدخل الشهري', 'Monthly Commitments and Income')}")

    def _render_templates_manager():
        st.caption(t("إدارة الالتزامات والدخل (إضافة، تعديل، حذف)", "Manage commitments and income (add, edit, delete)"))

        with st.form("account_add_template_form", clear_on_submit=True):
            t1, t2 = st.columns(2)
            with t1:
                name = st.text_input(t("اسم العنصر", "Item Name"))
                tx_type = st.selectbox(t("النوع", "Type"), [t("مصروف", "Expense"), t("دخل", "Income")])
                amount = st.number_input(t("المبلغ الافتراضي", "Default Amount"), min_value=0.0, step=1.0)
            with t2:
                category = st.text_input(t("التصنيف", "Category"), value=t("أخرى", "Other"))
                due_day = st.number_input(t("يوم الاستحقاق", "Due Day"), min_value=1, max_value=31, value=25, step=1)
                item_currency = st.selectbox(
                    t("العملة", "Currency"),
                    CURRENCY_OPTIONS,
                    index=CURRENCY_OPTIONS.index(currency) if currency in CURRENCY_OPTIONS else 0,
                    format_func=lambda opt: _currency_option_label(opt, is_en),
                )

            is_variable = st.checkbox(t("مبلغ متغير", "Variable Amount"), value=False)
            add_btn = st.form_submit_button(t("إضافة عنصر جديد", "Add New Item"), use_container_width=True)

            if add_btn:
                if not name.strip() or amount <= 0:
                        st.warning(t("يرجى إدخال الاسم والمبلغ بصورة صحيحة.", "Please enter a valid name and amount."))
                else:
                    recurring_items.append(
                        {
                            "name": name.strip(),
                            "type": "مصروف" if tx_type == t("مصروف", "Expense") else "دخل",
                            "amount": float(amount),
                            "currency": item_currency,
                            "category": category.strip() or t("أخرى", "Other"),
                            "day": int(due_day),
                            "active": True,
                            "is_variable": bool(is_variable),
                            "last_paid_month": "",
                            "pending_entitlements": [],
                        }
                    )
                    st.success(t("تمت إضافة العنصر.", "Item added successfully."))
                    st.rerun()

        st.markdown(f"#### {t('العناصر المحفوظة', 'Saved Items')}")
        if not recurring_items:
            st.info(t("لا توجد عناصر مدخلة.", "No saved items yet."))
            return

        for i, item in enumerate(recurring_items):
            state = t("نشط", "Active") if item.get("active", True) else t("متوقف", "Paused")
            item_type_label = _tx_type_label(item.get("type", ""), is_en)
            st.markdown(f"**{item.get('name','بدون اسم')}** • {item_type_label} • {state}")

            type_options = [t("مصروف", "Expense"), t("دخل", "Income")]
            current_type_label = _tx_type_label(item.get("type", "مصروف"), is_en)
            type_index = type_options.index(current_type_label) if current_type_label in type_options else 0
            current_currency = item.get("currency", currency)
            currency_index = CURRENCY_OPTIONS.index(current_currency) if current_currency in CURRENCY_OPTIONS else 0

            e1, e2 = st.columns(2)
            with e1:
                new_name = st.text_input(
                    t("اسم العنصر", "Item Name"),
                    value=str(item.get("name", "") or ""),
                    key=f"acct_tpl_name_{i}",
                )
            with e2:
                new_type_label = st.selectbox(
                    t("النوع", "Type"),
                    type_options,
                    index=type_index,
                    key=f"acct_tpl_type_{i}",
                )

            e3, e4 = st.columns(2)
            with e3:
                new_category = st.text_input(
                    t("التصنيف", "Category"),
                    value=str(item.get("category", t("أخرى", "Other")) or t("أخرى", "Other")),
                    key=f"acct_tpl_cat_{i}",
                )
            with e4:
                new_currency = st.selectbox(
                    t("العملة", "Currency"),
                    CURRENCY_OPTIONS,
                    index=currency_index,
                    format_func=lambda opt: _currency_option_label(opt, is_en),
                    key=f"acct_tpl_currency_{i}",
                )

            e5, e6, e7, e8 = st.columns(4)
            with e5:
                new_amount = st.number_input(t("المبلغ", "Amount"), min_value=0.0, value=float(item.get("amount", 0.0)), step=1.0, key=f"acct_tpl_amt_{i}")
            with e6:
                new_day = st.number_input(t("اليوم", "Day"), min_value=1, max_value=31, value=int(item.get("day", 1)), step=1, key=f"acct_tpl_day_{i}")
            with e7:
                new_active = st.checkbox(t("فعال", "Active"), value=bool(item.get("active", True)), key=f"acct_tpl_active_{i}")
            with e8:
                new_variable = st.checkbox(t("متغير", "Variable"), value=bool(item.get("is_variable", False)), key=f"acct_tpl_var_{i}")

            a1, a2 = st.columns(2)
            with a1:
                if st.button(t("تعديل", "Edit"), key=f"acct_tpl_update_{i}", use_container_width=True):
                    if not str(new_name).strip() or float(new_amount) <= 0:
                        st.warning(t("يرجى إدخال الاسم والمبلغ بصورة صحيحة.", "Please enter a valid name and amount."))
                    else:
                        item["name"] = str(new_name).strip()
                        item["type"] = "مصروف" if new_type_label == t("مصروف", "Expense") else "دخل"
                        item["category"] = str(new_category).strip() or t("أخرى", "Other")
                        item["currency"] = new_currency
                        item["amount"] = float(new_amount)
                        item["day"] = int(new_day)
                        item["active"] = bool(new_active)
                        item["is_variable"] = bool(new_variable)
                        st.success(t("تم تعديل العنصر.", "Item updated."))
                        st.rerun()
            with a2:
                if st.button(t("حذف", "Delete"), key=f"acct_tpl_delete_{i}", use_container_width=True):
                    recurring_items.pop(i)
                    st.success(t("تم حذف العنصر.", "Item deleted."))
                    st.rerun()

            st.markdown("---")

    if st.session_state["account_templates_open"]:
        st.markdown(f"#### {t('إدارة العناصر الشهرية', 'Monthly Items')}")
        _render_templates_manager()
        if st.button(
            t("إغلاق إدارة العناصر الشهرية", "Close Monthly Items"),
            key="close_templates_inline_btn",
            use_container_width=True,
        ):
            st.session_state["account_templates_open"] = False
            st.rerun()

    active_items = [item for item in recurring_items if item.get("active", True)]
    for item in active_items:
        _ensure_pending_month(item, month_key)

    overdue_commitments_total = sum(
        float(item.get("amount", 0.0)) * len(item.get("pending_entitlements", []))
        for item in active_items
        if item.get("type") == "مصروف"
    )
    delayed_incomes_total = sum(
        float(item.get("amount", 0.0)) * len(item.get("pending_entitlements", []))
        for item in active_items
        if item.get("type") == "دخل"
    )

    rc1, rc2 = st.columns([2, 2])
    with rc1:
        st.metric(t("إجمالي الالتزامات المتأخرة", "Total Overdue Commitments"), f"{overdue_commitments_total:,.0f} {currency_view}")
    with rc2:
        st.metric(t("إجمالي الدخل المتأخر", "Total Delayed Income"), f"{delayed_incomes_total:,.0f} {currency_view}")

    if not active_items:
        st.info(
            t(
                "لا توجد عناصر نشطة حاليًا. يمكن إضافة العناصر من زر إدارة العناصر الشهرية بالأعلى.",
                "No active items right now. Items can be added from the Manage Monthly Items button above.",
            )
        )
    else:
        for idx, item in enumerate(active_items):
            pending = item.get("pending_entitlements", [])
            is_income = item.get("type") == "دخل"
            state_txt = (f"{t('معلّق', 'Pending')}: {len(pending)} {t('شهر', 'month')}" if pending else t("مكتمل", "Completed"))
            var_txt = t("متغير", "Variable") if item.get("is_variable", False) else t("ثابت", "Fixed")
            border = "#2563eb" if is_income else "#dc2626"
            direction = "ltr" if is_en else "rtl"
            align = "left" if is_en else "right"
            border_side = "border-left" if is_en else "border-right"
            item_currency = _currency_short_label(item.get("currency", currency), is_en)

            st.markdown(
                f"""
                <div style="background:#fff; border:1px solid #e5e7eb; {border_side}:6px solid {border}; border-radius:10px; padding:10px; margin-bottom:6px; direction:{direction}; text-align:{align};">
                    <strong>{item.get('name',t('بدون اسم','Untitled'))}</strong> — {state_txt}<br/>
                    <span style="color:#6b7280;">{item.get('amount',0)} {item_currency} | {var_txt} | {t('يوم الاستحقاق', 'Due day')}: {item.get('day', 1)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_pay, c_open = st.columns([1, 4])
            with c_pay:
                if st.button(t("تأكيد", "Confirm"), key=f"tick_open_{idx}", use_container_width=True):
                    st.session_state[f"open_pay_form_{idx}"] = not st.session_state.get(f"open_pay_form_{idx}", False)
                    st.rerun()
            with c_open:
                if pending:
                    st.caption(f"{t('الأشهر غير المؤكدة', 'Unconfirmed months')}: {', '.join(pending)}")
                else:
                    st.caption(t("لا توجد أشهر معلقة.", "No pending months."))

            if st.session_state.get(f"open_pay_form_{idx}", False):
                with st.form(f"confirm_item_form_{idx}", clear_on_submit=False):
                    f1, f2, f3 = st.columns(3)
                    with f1:
                        default_amount = float(item.get("amount", 0.0))
                        pay_amount = st.number_input(
                            t("المبلغ الفعلي", "Actual Amount"),
                            min_value=0.0,
                            value=default_amount,
                            step=1.0,
                            key=f"pay_amount_{idx}",
                        )
                    with f2:
                        pay_date = st.date_input(t("تاريخ الحركة", "Transaction Date"), value=datetime.today(), key=f"pay_date_{idx}")
                    with f3:
                        options = pending if pending else [month_key]
                        entitlement_key = st.selectbox(t("شهر الاستحقاق", "Entitlement Month"), options, key=f"entitlement_{idx}")

                    update_template = st.checkbox(t("تحديث المبلغ الافتراضي دائمًا", "Update default amount permanently"), value=False, key=f"upd_tpl_{idx}")
                    pay_tax_code = ""
                    if item.get("type") == "مصروف" and tax_codes:
                        pay_tax_code = st.selectbox(
                            t("التصنيف الضريبي", "Tax Classification"),
                            tax_codes,
                            index=tax_codes.index(default_expense_tax_code) if default_expense_tax_code in tax_codes else 0,
                            format_func=lambda code: tax_label_by_code.get(code, code),
                            key=f"pay_tax_tag_{idx}",
                        )
                    b1, b2 = st.columns(2)
                    with b1:
                        confirm_btn = st.form_submit_button(t("تأكيد المعاملة", "Confirm Transaction"), use_container_width=True)
                    with b2:
                        cancel_btn = st.form_submit_button(t("إلغاء", "Cancel"), use_container_width=True)

                if cancel_btn:
                    st.session_state[f"open_pay_form_{idx}"] = False
                    st.rerun()

                if confirm_btn:
                    if pay_amount <= 0:
                        st.warning(t("المبلغ لازم يكون أكبر من صفر.", "Amount must be greater than zero."))
                    else:
                        pay_dt = datetime.combine(pay_date, datetime.min.time())
                        payment_month_key = _month_key_from_date(pay_dt)
                        tx_payload = {
                            "date": pay_date.strftime("%Y-%m-%d"),
                            "type": item.get("type", "مصروف"),
                            "amount": float(pay_amount),
                            "currency": item.get("currency", currency),
                            "category": item.get("category", t("أخرى", "Other")),
                            "note": f"{t('تأكيد من الالتزامات الشهرية', 'Confirmed from monthly commitments')}: {item.get('name', '')}",
                            "payment_month_key": payment_month_key,
                            "entitlement_month_key": entitlement_key,
                            "source_template_name": item.get("name", ""),
                        }
                        if tx_payload["type"] == "مصروف" and pay_tax_code:
                            tx_payload["tax_tag_code"] = pay_tax_code
                        add_transaction(payment_month_key, tx_payload)
                        if entitlement_key in item.get("pending_entitlements", []):
                            item["pending_entitlements"].remove(entitlement_key)
                        item["last_paid_month"] = entitlement_key
                        if update_template:
                            item["amount"] = float(pay_amount)
                        st.session_state[f"open_pay_form_{idx}"] = False
                    st.success(t("تم تسجيل المعاملة في الحساب.", "Transaction recorded in account."))
                    st.rerun()

    st.divider()

    with st.expander(t("إضافة معاملة جديدة", "Add New Transaction"), expanded=False):
        with st.form("add_transaction_account_form"):
            t1, t2 = st.columns(2)
            with t1:
                t_amount = st.number_input(t("المبلغ", "Amount"), min_value=0.0, step=1.0)
                t_type_lbl = st.selectbox(t("النوع", "Type"), [t("مصروف", "Expense"), t("دخل", "Income")])
            with t2:
                t_date = st.date_input(t("التاريخ", "Date"), value=datetime.today())
                t_category = st.selectbox(
                    t("التصنيف", "Category"),
                    localized_all_categories(is_en),
                )

            selected_tx_type = "مصروف" if t_type_lbl == t("مصروف", "Expense") else "دخل"
            selected_tax_code = ""
            if selected_tx_type == "مصروف" and tax_codes:
                selected_tax_code = st.selectbox(
                    t("التصنيف الضريبي", "Tax Classification"),
                    tax_codes,
                    index=tax_codes.index(default_expense_tax_code) if default_expense_tax_code in tax_codes else 0,
                    format_func=lambda code: tax_label_by_code.get(code, code),
                    key="account_add_tx_tax_tag",
                )
                if selected_tax_code == ExpenseTaxService.DEDUCTIBLE_CODE:
                    st.caption(
                        t(
                            "إذا اخترت أخرى، اكتبي التفاصيل في الملاحظة.",
                            "If you choose Other, add the details in the note.",
                        )
                    )

            t_note = st.text_input(t("ملاحظة (اختياري)", "Note (Optional)"))
            default_currency_label = t("نفس العملة الافتراضية", "Use Default Currency")
            t_currency_options = [default_currency_label] + CURRENCY_OPTIONS
            t_currency = st.selectbox(
                t("العملة", "Currency"),
                t_currency_options,
                format_func=lambda opt: opt if opt == default_currency_label else _currency_option_label(opt, is_en),
            )
            submit_btn = st.form_submit_button(t("حفظ المعاملة", "Save Transaction"), use_container_width=True)

            if submit_btn and t_amount > 0:
                tx_currency = currency if t_currency == default_currency_label else t_currency
                target_month_key = _month_key_from_date(datetime.combine(t_date, datetime.min.time()))
                tx_payload = {
                    "date": t_date.strftime("%Y-%m-%d"),
                    "type": selected_tx_type,
                    "amount": float(t_amount),
                    "currency": tx_currency,
                    "category": t_category,
                    "note": t_note,
                }
                if selected_tx_type == "مصروف" and selected_tax_code:
                    tx_payload["tax_tag_code"] = selected_tax_code
                add_transaction(target_month_key, tx_payload)
                st.session_state["account_templates_open"] = False
                if target_month_key == month_key:
                    st.session_state["account_save_notice"] = t(
                        "تمت إضافة المعاملة بنجاح.",
                        "Transaction saved successfully.",
                    )
                else:
                    target_label = _month_label_from_key(target_month_key, is_en)
                    st.session_state["account_save_notice"] = t(
                        f"تم حفظ المعاملة في شهر {target_label} حسب التاريخ. يمكن تغيير الشهر لعرضها.",
                        f"Transaction was saved in {target_label} based on date. Change the month to view it.",
                    )
                st.rerun()

    st.markdown(f"### {t('سجل المعاملات', 'Transactions')}")
    order_options = [
        t("الأحدث أولاً", "Newest First"),
        t("الأقدم أولاً", "Oldest First"),
    ]
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        query = st.text_input(
            t("بحث", "Search"),
            placeholder=t("البحث بالتاريخ أو التصنيف أو الملاحظة", "Search by date, category, or note"),
            on_change=_close_templates_panel,
        )
    with f2:
        type_filter_lbl = st.selectbox(
            t("النوع", "Type"),
            [t("الكل", "All"), t("مصروف", "Expense"), t("دخل", "Income")],
            on_change=_close_templates_panel,
        )
        type_filter = "الكل" if type_filter_lbl == t("الكل", "All") else ("مصروف" if type_filter_lbl == t("مصروف", "Expense") else "دخل")
    with f3:
        categories = [t("الكل", "All")]
        if not df_all.empty and "category" in df_all.columns:
            categories.extend(sorted(df_all["category"].dropna().astype(str).unique().tolist()))
        category_filter_lbl = st.selectbox(
            t("التصنيف", "Category"),
            categories,
            format_func=lambda x: x if x == t("الكل", "All") else _category_label(x, is_en),
            on_change=_close_templates_panel,
        )
        category_filter = "الكل" if category_filter_lbl == t("الكل", "All") else category_filter_lbl
    with f4:
        sort_order_lbl = st.selectbox(t("الترتيب", "Order"), order_options, on_change=_close_templates_panel)
        newest_first = sort_order_lbl == t("الأحدث أولاً", "Newest First")

    filtered_df = _build_filtered_df(tx_list, currency, query, type_filter, category_filter, newest_first=newest_first)
    if filtered_df.empty:
        st.info(t("لا توجد معاملات مطابقة للفلاتر الحالية.", "No transactions match current filters."))
        return

    id_col = t("معرّف", "ID")
    date_col = t("التاريخ", "Date")
    type_col = t("النوع", "Type")
    category_col = t("التصنيف", "Category")
    amount_col = t("المبلغ", "Amount")
    currency_col = t("العملة", "Currency")
    note_col = t("ملاحظة", "Note")
    delete_col = t("حذف", "Delete")

    view_df = filtered_df[["tx_id", "date", "type", "category", "amount", "currency", "note"]].copy()
    if is_en and "type" in view_df.columns:
        view_df["type"] = view_df["type"].apply(lambda x: _tx_type_label(x, True))
    if is_en and "category" in view_df.columns:
        view_df["category"] = view_df["category"].apply(lambda x: _category_label(x, True))
    if is_en and "currency" in view_df.columns:
        view_df["currency"] = view_df["currency"].apply(lambda x: _currency_option_label(x, True))
    view_df.rename(
        columns={
            "tx_id": id_col,
            "date": date_col,
            "type": type_col,
            "category": category_col,
            "amount": amount_col,
            "currency": currency_col,
            "note": note_col,
        },
        inplace=True,
    )
    view_df[delete_col] = False

    edited = st.data_editor(
        view_df,
        use_container_width=True,
        hide_index=True,
        disabled=[id_col, date_col, type_col, category_col, amount_col, currency_col, note_col],
        column_config={
            delete_col: st.column_config.CheckboxColumn(t("حذف", "Delete"), help=t("تحديد المعاملات المراد حذفها", "Select transactions to delete")),
            id_col: st.column_config.NumberColumn(t("معرّف", "ID"), format="%d"),
        },
        key="account_tx_editor",
        on_change=_close_templates_panel,
    )

    to_delete = edited[edited[delete_col]][id_col].tolist()
    if st.button(t("حذف المحدد", "Delete Selected"), type="secondary", use_container_width=True):
        if not to_delete:
            st.warning(t("يرجى اختيار معاملة واحدة على الأقل.", "Select at least one transaction."))
        else:
            st.session_state["account_templates_open"] = False
            for idx in sorted(to_delete, reverse=True):
                if 0 <= int(idx) < len(tx_list):
                    tx_list.pop(int(idx))
            st.success(t(f"تم حذف {len(to_delete)} معاملة.", f"Deleted {len(to_delete)} transaction(s)."))
            st.rerun()
