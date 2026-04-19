from __future__ import annotations

import calendar
from datetime import date, datetime
import html
from uuid import uuid4

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


def _proof_payload(uploaded_file) -> dict:
    if uploaded_file is None:
        return {}
    return {
        "proof_name": getattr(uploaded_file, "name", "") or "",
        "proof_bytes": uploaded_file.getvalue(),
        "proof_type": getattr(uploaded_file, "type", "") or "",
    }


def _proof_bytes(tx: dict) -> bytes:
    proof_data = tx.get("proof_bytes")
    if isinstance(proof_data, bytes):
        return proof_data
    if isinstance(proof_data, bytearray):
        return bytes(proof_data)
    return b""


def _has_proof(tx: dict) -> bool:
    return bool(_proof_bytes(tx))


def _proof_label(tx: dict, fallback: str = "") -> str:
    name = str(tx.get("proof_name") or "").strip()
    if not name or name.lower() == "nan":
        return fallback
    return name or fallback


def _month_search_text(value) -> str:
    raw = str(value or "").strip()
    if not raw or raw.lower() == "nan":
        return ""

    parts = [raw]
    if "-" in raw:
        year_txt, month_name = raw.split("-", 1)
        if month_name in arabic_months:
            month_index = arabic_months.index(month_name)
            month_number = month_index + 1
            english_name = english_months[month_index]
            arabic_number = str(month_number).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
            parts.extend(
                [
                    f"{month_name} {year_txt}",
                    f"{english_name} {year_txt}",
                    f"{year_txt}-{month_number:02d}",
                    f"شهر {month_number}",
                    f"شهر {arabic_number}",
                    f"month {month_number}",
                ]
            )
    return " ".join(parts)


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
    for optional_col in ["note", "proof_name", "payment_month_key", "entitlement_month_key"]:
        if optional_col not in df.columns:
            df[optional_col] = ""
        df[optional_col] = df[optional_col].fillna("")

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
        month_search = (
            df["payment_month_key"].apply(_month_search_text)
            + " "
            + df["entitlement_month_key"].apply(_month_search_text)
        )
        df = df[
            df["category"].astype(str).str.lower().str.contains(q, na=False)
            | df["note"].astype(str).str.lower().str.contains(q, na=False)
            | df["date"].astype(str).str.lower().str.contains(q, na=False)
            | df["proof_name"].astype(str).str.lower().str.contains(q, na=False)
            | month_search.astype(str).str.lower().str.contains(q, na=False)
        ]

    ascending = [not newest_first, not newest_first]
    return df.sort_values(by=["date_dt", "tx_id"], ascending=ascending)


def _month_key_from_date(dt: datetime) -> str:
    return f"{dt.year}-{arabic_months[dt.month - 1]}"


def _month_key_to_parts(month_key: str) -> tuple[int, int] | None:
    raw = str(month_key or "").strip()
    if "-" not in raw:
        return None
    year_txt, month_name = raw.split("-", 1)
    if month_name not in arabic_months:
        return None
    try:
        return int(year_txt), arabic_months.index(month_name) + 1
    except ValueError:
        return None


def _month_key_from_parts(year_value: int, month_value: int) -> str:
    return f"{int(year_value)}-{arabic_months[int(month_value) - 1]}"


def _shift_month_key(month_key: str, month_delta: int) -> str:
    parts = _month_key_to_parts(month_key)
    if not parts:
        return str(month_key or "")
    year_value, month_value = parts
    month_index = (year_value * 12) + (month_value - 1) + int(month_delta)
    shifted_year = month_index // 12
    shifted_month = (month_index % 12) + 1
    return _month_key_from_parts(shifted_year, shifted_month)


def _month_keys_between(start_key: str, end_key: str) -> list[str]:
    start = _month_key_to_parts(start_key)
    end = _month_key_to_parts(end_key)
    if not start or not end:
        return []

    start_index = start[0] * 12 + (start[1] - 1)
    end_index = end[0] * 12 + (end[1] - 1)
    if start_index > end_index:
        return []

    keys = []
    for month_index in range(start_index, end_index + 1):
        keys.append(_month_key_from_parts(month_index // 12, (month_index % 12) + 1))
    return keys


def _month_key_window(anchor_key: str, months_before: int = 12, months_after: int = 3) -> list[str]:
    start_key = _shift_month_key(anchor_key, -abs(int(months_before)))
    end_key = _shift_month_key(anchor_key, abs(int(months_after)))
    return _month_keys_between(start_key, end_key) or [anchor_key]


def _month_label_from_key(month_key: str, is_en: bool) -> str:
    if "-" not in month_key:
        return month_key
    year_txt, month_name = month_key.split("-", 1)
    if is_en and month_name in arabic_months:
        month_name = english_months[arabic_months.index(month_name)]
    return f"{month_name} {year_txt}"


def _display_month_label(value, is_en: bool) -> str:
    raw = str(value or "").strip()
    if not raw or raw.lower() == "nan":
        return ""
    return _month_label_from_key(raw, is_en)


def _payment_month_label_for_row(row, is_en: bool) -> str:
    payment_key = str(row.get("payment_month_key") or "").strip()
    if payment_key:
        return _month_label_from_key(payment_key, is_en)

    parsed_date = pd.to_datetime(row.get("date"), errors="coerce")
    if pd.isna(parsed_date):
        return ""
    return _month_label_from_key(_month_key_from_date(parsed_date.to_pydatetime()), is_en)


def _sort_month_keys(keys: list[str]) -> list[str]:
    def _key(mk: str):
        parts = _month_key_to_parts(mk)
        if not parts:
            return (9999, 99)
        return parts

    return sorted(keys, key=_key)


def _ensure_item_id(item: dict) -> str:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        item_id = str(uuid4())
        item["id"] = item_id
    return item_id


def _ensure_pending_month(item: dict, month_key: str) -> None:
    pending = item.setdefault("pending_entitlements", [])
    if not isinstance(pending, list):
        item["pending_entitlements"] = []
        pending = item["pending_entitlements"]

    pending = [str(mk) for mk in pending if isinstance(mk, str) and mk.strip()]
    item["pending_entitlements"] = _sort_month_keys(pending)

    last_paid_month = str(item.get("last_paid_month") or "").strip()
    if last_paid_month and _month_key_to_parts(last_paid_month):
        start_key = _shift_month_key(last_paid_month, 1)
    elif pending:
        start_key = _sort_month_keys(pending)[0]
    else:
        start_key = month_key

    for entitlement_key in _month_keys_between(start_key, month_key) or [month_key]:
        if entitlement_key not in item["pending_entitlements"] and last_paid_month != entitlement_key:
            item["pending_entitlements"].append(entitlement_key)

    item["pending_entitlements"] = _sort_month_keys(item["pending_entitlements"])


def _safe_entitlement_date(month_key: str, due_day: int) -> date | None:
    parts = _month_key_to_parts(month_key)
    if not parts:
        return None
    year_value, month_value = parts
    day_value = max(1, min(int(due_day or 1), calendar.monthrange(year_value, month_value)[1]))
    return date(year_value, month_value, day_value)


def _monthly_item_status_label(item: dict, pending: list[str], is_en: bool, today: date | None = None) -> str:
    if not isinstance(pending, list):
        pending = []
    clean_pending = _sort_month_keys([str(mk) for mk in pending if isinstance(mk, str) and mk.strip()])
    is_income = item.get("type") == "دخل"
    if not clean_pending:
        return "Received" if is_en and is_income else "Paid" if is_en else "مستلم" if is_income else "مدفوع"

    today_value = today or date.today()
    due_dates = [_safe_entitlement_date(mk, int(item.get("day", 1) or 1)) for mk in clean_pending]
    has_passed_due = any(due_dt is not None and due_dt < today_value for due_dt in due_dates)
    count_txt = f"{len(clean_pending)} {'month' if len(clean_pending) == 1 else 'months'}" if is_en else f"{len(clean_pending)} شهر"

    if is_income:
        state = "Not received yet" if has_passed_due and is_en else "Expected" if is_en else "لم يُستلم بعد" if has_passed_due else "متوقع"
    else:
        state = "Overdue" if has_passed_due and is_en else "Awaiting payment" if is_en else "متأخر" if has_passed_due else "بانتظار الدفع"
    return f"{state}: {count_txt}"


def _entitlement_options_for_item(item: dict, month_key: str) -> list[str]:
    pending = item.get("pending_entitlements", [])
    if not isinstance(pending, list):
        pending = []
    raw_options = [str(mk) for mk in pending if isinstance(mk, str) and mk.strip()]
    raw_options.extend(_month_key_window(month_key, months_before=12, months_after=3))
    raw_options.append(month_key)
    return _sort_month_keys(list(dict.fromkeys(raw_options)))


def _iter_transactions(transactions_by_month) -> list[dict]:
    if not isinstance(transactions_by_month, dict):
        return []

    rows = []
    for month_transactions in transactions_by_month.values():
        if not isinstance(month_transactions, list):
            continue
        rows.extend(tx for tx in month_transactions if isinstance(tx, dict))
    return rows


def _monthly_transaction_matches_item(tx: dict, item: dict) -> bool:
    source_id = str(tx.get("source_template_id") or "").strip()
    item_id = str(item.get("id") or "").strip()
    if source_id and item_id:
        return source_id == item_id

    source_name = str(tx.get("source_template_name") or "").strip()
    item_name = str(item.get("name") or "").strip()
    if not source_name or source_name != item_name:
        return False

    tx_type = str(tx.get("type") or "").strip()
    item_type = str(item.get("type") or "").strip()
    if tx_type and item_type and tx_type != item_type:
        return False

    tx_currency = str(tx.get("currency") or "").strip()
    item_currency = str(item.get("currency") or "").strip()
    if tx_currency and item_currency and tx_currency != item_currency:
        return False

    return True


def _sync_monthly_item_after_transaction_delete(deleted_tx: dict, recurring_items: list[dict], transactions_by_month) -> bool:
    entitlement_key = str(deleted_tx.get("entitlement_month_key") or "").strip()
    if not entitlement_key:
        return False

    all_transactions = _iter_transactions(transactions_by_month)
    changed = False

    for item in recurring_items:
        if not isinstance(item, dict):
            continue
        _ensure_item_id(item)
        if not _monthly_transaction_matches_item(deleted_tx, item):
            continue

        remaining_confirmed_keys = [
            str(tx.get("entitlement_month_key") or "").strip()
            for tx in all_transactions
            if _monthly_transaction_matches_item(tx, item)
            and str(tx.get("entitlement_month_key") or "").strip()
        ]

        if entitlement_key not in remaining_confirmed_keys:
            pending = item.setdefault("pending_entitlements", [])
            if not isinstance(pending, list):
                pending = []
                item["pending_entitlements"] = pending
            if entitlement_key not in pending:
                pending.append(entitlement_key)
                item["pending_entitlements"] = _sort_month_keys(pending)
                changed = True

        if remaining_confirmed_keys:
            latest_paid = _sort_month_keys(remaining_confirmed_keys)[-1]
            if item.get("last_paid_month") != latest_paid:
                item["last_paid_month"] = latest_paid
                changed = True
        elif item.get("last_paid_month") == entitlement_key:
            item["last_paid_month"] = ""
            changed = True

    return changed


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
    for item in recurring_items:
        if isinstance(item, dict):
            _ensure_item_id(item)

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
                due_day = st.number_input(t("يوم الاستحقاق/المتوقع", "Due/Expected Day"), min_value=1, max_value=31, value=25, step=1)
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
                            "id": str(uuid4()),
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

    waiting_expenses_total = sum(
        float(item.get("amount", 0.0)) * len(item.get("pending_entitlements", []))
        for item in active_items
        if item.get("type") == "مصروف"
    )
    expected_incomes_total = sum(
        float(item.get("amount", 0.0)) * len(item.get("pending_entitlements", []))
        for item in active_items
        if item.get("type") == "دخل"
    )

    rc1, rc2 = st.columns([2, 2])
    with rc1:
        st.metric(t("إجمالي المصاريف بانتظار الدفع", "Total Expenses Awaiting Payment"), f"{waiting_expenses_total:,.0f} {currency_view}")
    with rc2:
        st.metric(t("إجمالي الدخل المتوقع غير المستلم", "Total Expected Income Not Received"), f"{expected_incomes_total:,.0f} {currency_view}")

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
            pay_form_key = f"open_pay_form_{idx}"
            if not pending and st.session_state.get(pay_form_key, False):
                st.session_state[pay_form_key] = False
            is_income = item.get("type") == "دخل"
            state_txt = _monthly_item_status_label(item, pending, is_en)
            var_txt = t("متغير", "Variable") if item.get("is_variable", False) else t("ثابت", "Fixed")
            border = "#2563eb" if is_income else "#dc2626"
            direction = "ltr" if is_en else "rtl"
            align = "left" if is_en else "right"
            border_side = "border-left" if is_en else "border-right"
            item_currency = _currency_short_label(item.get("currency", currency), is_en)
            day_label = t("يوم الاستلام المتوقع", "Expected receipt day") if is_income else t("يوم الاستحقاق", "Due day")

            st.markdown(
                f"""
                <div style="background:#fff; border:1px solid #e5e7eb; {border_side}:6px solid {border}; border-radius:10px; padding:10px; margin-bottom:6px; direction:{direction}; text-align:{align};">
                    <strong>{item.get('name',t('بدون اسم','Untitled'))}</strong> — {state_txt}<br/>
                    <span style="color:#6b7280;">{item.get('amount',0)} {item_currency} | {var_txt} | {day_label}: {item.get('day', 1)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_pay, c_open = st.columns([1, 4])
            with c_pay:
                if pending:
                    if st.button(t("تأكيد", "Confirm"), key=f"tick_open_{idx}", use_container_width=True):
                        st.session_state[pay_form_key] = not st.session_state.get(pay_form_key, False)
                        st.rerun()
                else:
                    done_label = t("مستلم", "Received") if is_income else t("مدفوع", "Paid")
                    st.button(done_label, key=f"tick_complete_{idx}", use_container_width=True, disabled=True)
            with c_open:
                if pending:
                    pending_labels = ", ".join(_month_label_from_key(mk, is_en) for mk in _sort_month_keys(pending))
                    st.caption(f"{t('أشهر الاستحقاق غير المؤكدة', 'Unconfirmed entitlement months')}: {pending_labels}")
                else:
                    st.caption(t("لا توجد أشهر استحقاق بانتظار التأكيد.", "No entitlement months waiting for confirmation."))

            if pending and st.session_state.get(pay_form_key, False):
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
                        pay_date = st.date_input(
                            t("تاريخ الدفع/الاستلام الفعلي", "Actual Payment/Receipt Date"),
                            value=datetime.today(),
                            key=f"pay_date_{idx}",
                        )
                    with f3:
                        options = _entitlement_options_for_item(item, month_key)
                        default_entitlement = _sort_month_keys(pending)[0] if pending else month_key
                        entitlement_index = options.index(default_entitlement) if default_entitlement in options else 0
                        entitlement_key = st.selectbox(
                            t("شهر الاستحقاق", "Entitlement Month"),
                            options,
                            index=entitlement_index,
                            format_func=lambda mk: _month_label_from_key(mk, is_en),
                            key=f"entitlement_{idx}",
                        )

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
                    pay_proof = st.file_uploader(
                        t("إرفاق إثبات الدفع/الاستلام (اختياري)", "Attach Payment/Receipt Proof (Optional)"),
                        type=["png", "jpg", "jpeg", "pdf"],
                        key=f"pay_proof_{idx}_{int(st.session_state.get(f'pay_proof_nonce_{idx}', 0))}",
                    )
                    st.caption(
                        t(
                            "يمكن إرفاق صورة أو PDF. بعد الحفظ سيظهر الإثبات مع المعاملة في السجل.",
                            "Upload an image or PDF. After saving, the proof appears with the transaction log entry.",
                        )
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        confirm_btn = st.form_submit_button(
                            t("تسجيل الاستلام", "Record Receipt") if is_income else t("تسجيل الدفع", "Record Payment"),
                            use_container_width=True,
                        )
                    with b2:
                        cancel_btn = st.form_submit_button(t("إلغاء", "Cancel"), use_container_width=True)

                if cancel_btn:
                    st.session_state[pay_form_key] = False
                    st.session_state[f"pay_proof_nonce_{idx}"] = int(st.session_state.get(f"pay_proof_nonce_{idx}", 0)) + 1
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
                            "note": f"{t('استلام دخل شهري', 'Monthly income receipt') if is_income else t('دفع عنصر شهري', 'Monthly item payment')}: {item.get('name', '')}",
                            "payment_month_key": payment_month_key,
                            "entitlement_month_key": entitlement_key,
                            "source_template_id": _ensure_item_id(item),
                            "source_template_name": item.get("name", ""),
                            "monthly_item_status": "received" if is_income else "paid",
                        }
                        if tx_payload["type"] == "مصروف" and pay_tax_code:
                            tx_payload["tax_tag_code"] = pay_tax_code
                        tx_payload.update(_proof_payload(pay_proof))
                        add_transaction(payment_month_key, tx_payload)
                        if entitlement_key in item.get("pending_entitlements", []):
                            item["pending_entitlements"].remove(entitlement_key)
                        item["last_paid_month"] = entitlement_key
                        if update_template:
                            item["amount"] = float(pay_amount)
                        st.session_state[pay_form_key] = False
                        st.session_state[f"pay_proof_nonce_{idx}"] = int(st.session_state.get(f"pay_proof_nonce_{idx}", 0)) + 1
                        st.success(t("تم تسجيل المعاملة في الحساب.", "Transaction recorded in account."))
                        st.rerun()

    st.divider()

    with st.expander(t("إضافة معاملة جديدة", "Add New Transaction"), expanded=False):
        form_nonce = int(st.session_state.get("account_tx_form_nonce", 0))
        with st.form("add_transaction_account_form"):
            t1, t2 = st.columns(2)
            with t1:
                t_amount = st.number_input(
                    t("المبلغ", "Amount"),
                    min_value=0.0,
                    step=1.0,
                    key=f"account_tx_amount_{form_nonce}",
                )
                t_type_lbl = st.selectbox(
                    t("النوع", "Type"),
                    [t("مصروف", "Expense"), t("دخل", "Income")],
                    key=f"account_tx_type_{form_nonce}",
                )
            with t2:
                t_date = st.date_input(t("التاريخ", "Date"), value=datetime.today(), key=f"account_tx_date_{form_nonce}")
                t_category = st.selectbox(
                    t("التصنيف", "Category"),
                    localized_all_categories(is_en),
                    key=f"account_tx_category_{form_nonce}",
                )

            selected_tx_type = "مصروف" if t_type_lbl == t("مصروف", "Expense") else "دخل"
            selected_tax_code = ""
            if selected_tx_type == "مصروف" and tax_codes:
                selected_tax_code = st.selectbox(
                    t("التصنيف الضريبي", "Tax Classification"),
                    tax_codes,
                    index=tax_codes.index(default_expense_tax_code) if default_expense_tax_code in tax_codes else 0,
                    format_func=lambda code: tax_label_by_code.get(code, code),
                    key=f"account_add_tx_tax_tag_{form_nonce}",
                )
                if selected_tax_code == ExpenseTaxService.DEDUCTIBLE_CODE:
                    st.caption(
                        t(
                            "إذا تم اختيار أخرى، يرجى إضافة التفاصيل في الملاحظة.",
                            "If you choose Other, add the details in the note.",
                        )
                    )

            t_note = st.text_input(t("ملاحظة (اختياري)", "Note (Optional)"), key=f"account_tx_note_{form_nonce}")
            t_proof = st.file_uploader(
                t("إرفاق إثبات (اختياري)", "Attach Proof (Optional)"),
                type=["png", "jpg", "jpeg", "pdf"],
                key=f"account_tx_proof_{int(st.session_state.get('account_tx_proof_nonce', 0))}",
            )
            st.caption(
                t(
                    "اختياري: يمكن إرفاق صورة أو PDF يظهر لاحقًا في سجل المعاملات.",
                    "Optional: upload an image or PDF that appears later in the transaction log.",
                )
            )
            default_currency_label = t("نفس العملة الافتراضية", "Use Default Currency")
            t_currency_options = [default_currency_label] + CURRENCY_OPTIONS
            t_currency = st.selectbox(
                t("العملة", "Currency"),
                t_currency_options,
                format_func=lambda opt: opt if opt == default_currency_label else _currency_option_label(opt, is_en),
                key=f"account_tx_currency_{form_nonce}",
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
                    "payment_month_key": target_month_key,
                }
                if selected_tx_type == "مصروف" and selected_tax_code:
                    tx_payload["tax_tag_code"] = selected_tax_code
                tx_payload.update(_proof_payload(t_proof))
                add_transaction(target_month_key, tx_payload)
                st.session_state["account_tx_form_nonce"] = form_nonce + 1
                st.session_state["account_tx_proof_nonce"] = int(st.session_state.get("account_tx_proof_nonce", 0)) + 1
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
            placeholder=t(
                "البحث بالتاريخ أو التصنيف أو الملاحظة أو الإثبات أو شهر الاستحقاق",
                "Search by date, category, note, proof, or entitlement month",
            ),
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
    date_col = t("تاريخ الحركة", "Movement Date")
    payment_month_col = t("شهر التسجيل", "Recorded Month")
    entitlement_month_col = t("شهر الاستحقاق", "Entitlement Month")
    type_col = t("النوع", "Type")
    category_col = t("التصنيف", "Category")
    amount_col = t("المبلغ", "Amount")
    currency_col = t("العملة", "Currency")
    note_col = t("ملاحظة", "Note")
    proof_col = t("إثبات", "Proof")
    delete_col = t("حذف", "Delete")

    view_df = filtered_df[["tx_id", "date", "payment_month_key", "entitlement_month_key", "type", "category", "amount", "currency", "note"]].copy()
    view_df["payment_month_key"] = view_df.apply(lambda row: _payment_month_label_for_row(row, is_en), axis=1)
    view_df["entitlement_month_key"] = view_df["entitlement_month_key"].apply(lambda mk: _display_month_label(mk, is_en))
    if is_en and "type" in view_df.columns:
        view_df["type"] = view_df["type"].apply(lambda x: _tx_type_label(x, True))
    if is_en and "category" in view_df.columns:
        view_df["category"] = view_df["category"].apply(lambda x: _category_label(x, True))
    if is_en and "currency" in view_df.columns:
        view_df["currency"] = view_df["currency"].apply(lambda x: _currency_option_label(x, True))
    proof_lookup = {
        int(row["tx_id"]): _proof_label(row, t("مرفق", "Attached"))
        for _, row in filtered_df.iterrows()
        if _has_proof(row.to_dict())
    }
    view_df[proof_col] = view_df["tx_id"].apply(lambda idx: proof_lookup.get(int(idx), ""))
    view_df.rename(
        columns={
            "tx_id": id_col,
            "date": date_col,
            "payment_month_key": payment_month_col,
            "entitlement_month_key": entitlement_month_col,
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
        disabled=[id_col, date_col, payment_month_col, entitlement_month_col, type_col, category_col, amount_col, currency_col, note_col, proof_col],
        column_config={
            delete_col: st.column_config.CheckboxColumn(t("حذف", "Delete"), help=t("تحديد المعاملات المراد حذفها", "Select transactions to delete")),
            id_col: st.column_config.NumberColumn(t("معرّف", "ID"), format="%d"),
        },
        key="account_tx_editor",
        on_change=_close_templates_panel,
    )

    proof_rows = [row.to_dict() for _, row in filtered_df.iterrows() if _has_proof(row.to_dict())]
    if proof_rows:
        st.markdown(f"#### {t('إثباتات المعاملات', 'Transaction Proofs')}")
        proof_cols = st.columns(2)
        for proof_idx, tx in enumerate(proof_rows):
            col = proof_cols[proof_idx % 2]
            with col:
                proof_name = _proof_label(tx, t("إثبات", "Proof"))
                proof_data = _proof_bytes(tx)
                caption = f"{tx.get('date', '')} | {_category_label(tx.get('category', ''), is_en)} | {tx.get('amount', 0)} {_currency_short_label(tx.get('currency', currency), is_en)}"
                entitlement_key = str(tx.get("entitlement_month_key") or "").strip()
                if entitlement_key:
                    caption = f"{caption} | {t('استحقاق', 'Entitlement')}: {_month_label_from_key(entitlement_key, is_en)}"
                st.caption(caption)
                st.download_button(
                    t("تحميل الفاتورة/الإثبات", "Download Invoice/Proof"),
                    data=proof_data,
                    file_name=proof_name,
                    mime=str(tx.get("proof_type") or "application/octet-stream"),
                    key=f"download_tx_proof_{int(tx.get('tx_id', proof_idx))}_{proof_idx}",
                    use_container_width=True,
                )

    to_delete = edited[edited[delete_col]][id_col].tolist()
    if st.button(t("حذف المحدد", "Delete Selected"), type="secondary", use_container_width=True):
        if not to_delete:
            st.warning(t("يرجى اختيار معاملة واحدة على الأقل.", "Select at least one transaction."))
        else:
            st.session_state["account_templates_open"] = False
            deleted_transactions = []
            for idx in sorted(to_delete, reverse=True):
                if 0 <= int(idx) < len(tx_list):
                    deleted_transactions.append(tx_list.pop(int(idx)))

            restored_monthly_items = 0
            transactions_by_month = st.session_state.get("transactions", {})
            for deleted_tx in deleted_transactions:
                if _sync_monthly_item_after_transaction_delete(deleted_tx, recurring_items, transactions_by_month):
                    restored_monthly_items += 1

            if restored_monthly_items:
                st.success(
                    t(
                        f"تم حذف {len(deleted_transactions)} معاملة وإرجاع {restored_monthly_items} عنصر شهري للتأكيد.",
                        f"Deleted {len(deleted_transactions)} transaction(s) and returned {restored_monthly_items} monthly item(s) to confirmation.",
                    )
                )
            else:
                st.success(t(f"تم حذف {len(deleted_transactions)} معاملة.", f"Deleted {len(deleted_transactions)} transaction(s)."))
            st.rerun()
