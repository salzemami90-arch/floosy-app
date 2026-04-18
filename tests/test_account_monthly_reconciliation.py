from pages_floosy.account_page import _sync_monthly_item_after_transaction_delete


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
