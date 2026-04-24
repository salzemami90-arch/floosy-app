import pandas as pd

from pages_floosy.account_page import _apply_transaction_edits
from services.expense_tax_service import ExpenseTaxService


def _tax_context(is_en: bool = True):
    state = {"transactions": {}}
    options = ExpenseTaxService.expense_options(state, is_en=is_en)
    by_code = {opt["code"]: opt["label"] for opt in options}
    default_code = next((opt["code"] for opt in options if opt.get("deductible")), options[0]["code"])
    return state, by_code, default_code


def test_apply_transaction_edits_updates_existing_account_transaction():
    state, tax_label_by_code, default_code = _tax_context(is_en=True)
    state["transactions"] = {
        "2026-أبريل": [
            {
                "date": "2026-04-10",
                "type": "مصروف",
                "amount": 5.0,
                "currency": "د.ك - دينار كويتي",
                "category": "مشتريات",
                "note": "Old note",
                "payment_month_key": "2026-أبريل",
                "tax_tag_code": "expense_deductible_generic",
            }
        ]
    }

    original_rows = pd.DataFrame([{"tx_id": 0}])
    edited_rows = pd.DataFrame(
        [
            {
                "ID": 0,
                "Movement Date": "2026-04-11",
                "Type": "Expense",
                "Category": "Shopping",
                "Amount": 9.0,
                "Currency": "KWD - Kuwaiti Dinar",
                "Tax Classification": "Rent",
                "Note": "Updated note",
            }
        ]
    )

    result = _apply_transaction_edits(
        state,
        "2026-أبريل",
        original_rows,
        edited_rows,
        is_en=True,
        default_expense_tax_code=default_code,
        tax_label_by_code=tax_label_by_code,
    )

    assert result == {"updated": 1, "moved": 0, "moved_targets": [], "errors": []}
    updated_tx = state["transactions"]["2026-أبريل"][0]
    assert updated_tx["date"] == "2026-04-11"
    assert updated_tx["amount"] == 9.0
    assert updated_tx["category"] == "مشتريات"
    assert updated_tx["note"] == "Updated note"
    assert updated_tx["tax_tag_code"] == "expense_rent"


def test_apply_transaction_edits_moves_transaction_when_date_changes_month():
    state, tax_label_by_code, default_code = _tax_context(is_en=True)
    state["transactions"] = {
        "2026-أبريل": [
            {
                "date": "2026-04-10",
                "type": "مصروف",
                "amount": 5.0,
                "currency": "د.ك - دينار كويتي",
                "category": "مشتريات",
                "note": "Old note",
                "payment_month_key": "2026-أبريل",
                "tax_tag_code": "expense_deductible_generic",
            }
        ]
    }

    original_rows = pd.DataFrame([{"tx_id": 0}])
    edited_rows = pd.DataFrame(
        [
            {
                "ID": 0,
                "Movement Date": "2026-05-02",
                "Type": "Expense",
                "Category": "Shopping",
                "Amount": 7.0,
                "Currency": "KWD - Kuwaiti Dinar",
                "Tax Classification": "Other",
                "Note": "Moved to May",
            }
        ]
    )

    result = _apply_transaction_edits(
        state,
        "2026-أبريل",
        original_rows,
        edited_rows,
        is_en=True,
        default_expense_tax_code=default_code,
        tax_label_by_code=tax_label_by_code,
    )

    assert result["updated"] == 1
    assert result["moved"] == 1
    assert result["moved_targets"] == ["2026-مايو"]
    assert state["transactions"]["2026-أبريل"] == []
    moved_tx = state["transactions"]["2026-مايو"][0]
    assert moved_tx["date"] == "2026-05-02"
    assert moved_tx["payment_month_key"] == "2026-مايو"
    assert moved_tx["note"] == "Moved to May"


def test_apply_transaction_edits_clears_tax_fields_when_type_becomes_income():
    state, tax_label_by_code, default_code = _tax_context(is_en=True)
    state["transactions"] = {
        "2026-أبريل": [
            {
                "date": "2026-04-10",
                "type": "مصروف",
                "amount": 5.0,
                "currency": "د.ك - دينار كويتي",
                "category": "مشتريات",
                "note": "Old note",
                "payment_month_key": "2026-أبريل",
                "tax_tag_code": "expense_rent",
                "tax_classification": "deductible",
            }
        ]
    }

    original_rows = pd.DataFrame([{"tx_id": 0}])
    edited_rows = pd.DataFrame(
        [
            {
                "ID": 0,
                "Movement Date": "2026-04-10",
                "Type": "Income",
                "Category": "Salary",
                "Amount": 50.0,
                "Currency": "KWD - Kuwaiti Dinar",
                "Tax Classification": "Rent",
                "Note": "Salary received",
            }
        ]
    )

    result = _apply_transaction_edits(
        state,
        "2026-أبريل",
        original_rows,
        edited_rows,
        is_en=True,
        default_expense_tax_code=default_code,
        tax_label_by_code=tax_label_by_code,
    )

    assert result["updated"] == 1
    updated_tx = state["transactions"]["2026-أبريل"][0]
    assert updated_tx["type"] == "دخل"
    assert updated_tx["category"] == "راتب"
    assert updated_tx["tax_tag_code"] == ""
    assert updated_tx["tax_classification"] == "not_applicable"
