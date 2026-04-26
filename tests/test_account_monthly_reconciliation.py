from datetime import date

from pages_floosy.account_page import (
    _ensure_pending_month,
    _entitlement_options_for_item,
    _latest_confirmed_tx_for_item,
    _monthly_item_status_label,
    _sync_monthly_item_after_transaction_delete,
)


def test_deleting_monthly_confirmation_reopens_entitlement_month():
    item = {
        "id": "social-insurance",
        "name": "التأمينات",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
        "last_paid_month": "2026-مارس",
        "pending_entitlements": [],
    }
    deleted_tx = {
        "source_template_id": "social-insurance",
        "source_template_name": "التأمينات",
        "entitlement_month_key": "2026-مارس",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
    }

    changed = _sync_monthly_item_after_transaction_delete(deleted_tx, [item], {"2026-مارس": []})

    assert changed is True
    assert item["pending_entitlements"] == ["2026-مارس"]
    assert item["last_paid_month"] == ""


def test_deleting_older_month_keeps_latest_remaining_confirmation():
    item = {
        "id": "social-insurance",
        "name": "التأمينات",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
        "last_paid_month": "2026-أبريل",
        "pending_entitlements": [],
    }
    deleted_tx = {
        "source_template_id": "social-insurance",
        "source_template_name": "التأمينات",
        "entitlement_month_key": "2026-مارس",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
    }
    remaining_april_tx = {
        "source_template_id": "social-insurance",
        "source_template_name": "التأمينات",
        "entitlement_month_key": "2026-أبريل",
        "date": "2026-04-20",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
    }

    changed = _sync_monthly_item_after_transaction_delete(
        deleted_tx,
        [item],
        {"2026-أبريل": [remaining_april_tx]},
    )

    assert changed is True
    assert item["pending_entitlements"] == ["2026-مارس"]
    assert item["last_paid_month"] == "2026-أبريل"
    assert item["last_paid_date"] == "2026-04-20"


def test_pending_entitlements_fill_missing_months_from_last_paid():
    item = {
        "id": "social-insurance",
        "name": "التأمينات",
        "type": "مصروف",
        "currency": "د.ك - دينار كويتي",
        "day": 20,
        "last_paid_month": "2026-يناير",
        "pending_entitlements": [],
    }

    _ensure_pending_month(item, "2026-أبريل")

    assert item["pending_entitlements"] == ["2026-فبراير", "2026-مارس", "2026-أبريل"]


def test_income_monthly_status_uses_expected_language_not_overdue():
    item = {
        "name": "راتب شرق",
        "type": "دخل",
        "day": 15,
    }

    label = _monthly_item_status_label(item, ["2026-فبراير"], is_en=False, today=date(2026, 4, 19))

    assert "لم يُستلم بعد" in label
    assert "متأخر" not in label


def test_expense_monthly_status_marks_passed_due_as_overdue():
    item = {
        "name": "التأمينات",
        "type": "مصروف",
        "day": 20,
    }

    label = _monthly_item_status_label(item, ["2026-فبراير"], is_en=False, today=date(2026, 4, 19))

    assert "متأخر" in label


def test_entitlement_options_include_prior_month_for_late_income_receipt():
    item = {
        "name": "شرق",
        "type": "دخل",
        "pending_entitlements": ["2026-أبريل"],
    }

    options = _entitlement_options_for_item(item, "2026-أبريل")

    assert "2026-فبراير" in options
    assert "2026-أبريل" in options


def test_latest_confirmed_transaction_prefers_actual_latest_date():
    item = {
        "id": "salary-east",
        "name": "شرق",
        "type": "دخل",
        "currency": "د.ك - دينار كويتي",
    }
    transactions_by_month = {
        "2026-مارس": [
            {
                "source_template_id": "salary-east",
                "source_template_name": "شرق",
                "entitlement_month_key": "2026-فبراير",
                "date": "2026-03-01",
                "type": "دخل",
                "currency": "د.ك - دينار كويتي",
            }
        ],
        "2026-أبريل": [
            {
                "source_template_id": "salary-east",
                "source_template_name": "شرق",
                "entitlement_month_key": "2026-مارس",
                "date": "2026-04-10",
                "type": "دخل",
                "currency": "د.ك - دينار كويتي",
            }
        ],
    }

    latest_tx = _latest_confirmed_tx_for_item(item, transactions_by_month)

    assert latest_tx is not None
    assert latest_tx["date"] == "2026-04-10"
    assert latest_tx["entitlement_month_key"] == "2026-مارس"
