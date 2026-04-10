from __future__ import annotations

import os
import re
import time

import pytest


pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, expect  # noqa: E402


BASE_URL = os.environ.get("FLOOSY_BASE_URL", "http://127.0.0.1:8501")


@pytest.fixture()
def page() -> Page:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        try:
            yield page
        finally:
            browser.close()


def test_floosy_english_smoke(page: Page) -> None:
    page.goto(BASE_URL, wait_until="networkidle")

    welcome_title = page.get_by_text("Welcome to Floosy")
    if welcome_title.count() > 0:
        expect(welcome_title).to_be_visible()
        page.get_by_label("Language").select_option("English")
        page.get_by_role("button", name="Start").click()

    sidebar = page.locator('[data-testid="stSidebar"]')
    account_link = sidebar.locator("label").filter(has_text=re.compile(r"^Account$|^الحساب$")).first
    expect(account_link).to_be_visible()
    account_link.click()

    expect(page.get_by_role("heading", name=re.compile(r"Account|الحساب"))).to_be_visible()
    expect(page.get_by_text(re.compile(r"Add New Transaction|إضافة معاملة جديدة"))).to_be_visible()
    expect(page.get_by_role("heading", name=re.compile(r"Transactions|سجل المعاملات"))).to_be_visible()


def test_account_can_add_transaction_without_opening_monthly_items(page: Page) -> None:
    page.goto(BASE_URL, wait_until="networkidle")

    welcome_title = page.get_by_text("Welcome to Floosy")
    if welcome_title.count() > 0:
        expect(welcome_title).to_be_visible()
        page.get_by_label("Language").select_option("English")
        page.get_by_role("button", name="Start").click()

    sidebar = page.locator('[data-testid="stSidebar"]')
    account_link = sidebar.locator("label").filter(has_text=re.compile(r"^Account$|^الحساب$")).first
    expect(account_link).to_be_visible()
    account_link.click()

    expect(page.get_by_role("heading", name=re.compile(r"Account|الحساب"))).to_be_visible()

    page.get_by_text(re.compile(r"Add New Transaction|إضافة معاملة جديدة")).click()

    amount_input = page.get_by_label(re.compile(r"^Amount$|^المبلغ$")).first
    amount_input.fill("17")

    note_value = f"playwright-smoke-{int(time.time())}"
    note_input = page.locator('input[aria-label*="Note"], input[aria-label*="ملاحظة"]').first
    note_input.fill(note_value)

    page.get_by_role("button", name=re.compile(r"Save Transaction|حفظ المعاملة")).click()

    success_message = page.get_by_text(
        re.compile(r"Transaction saved successfully|تمت إضافة المعاملة بنجاح|تم حفظ المعاملة")
    )
    expect(success_message.first).to_be_visible()
    expect(page.locator("body")).to_contain_text(note_value)

    monthly_items_close = page.get_by_role("button", name=re.compile(r"Close Monthly Items|إغلاق إدارة العناصر الشهرية"))
    expect(monthly_items_close).to_have_count(0)
