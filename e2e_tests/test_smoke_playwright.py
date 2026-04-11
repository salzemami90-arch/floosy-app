from __future__ import annotations

import os
import re
import time

import pytest


pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, expect  # noqa: E402


BASE_URL = os.environ.get("FLOOSY_BASE_URL", "http://127.0.0.1:8501")
EXPECT_CLOUD_CONFIG = str(os.environ.get("FLOOSY_EXPECT_CLOUD_CONFIG", "1") or "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


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


def _goto_language(page: Page, lang_code: str) -> None:
    separator = "&" if "?" in BASE_URL else "?"
    page.goto(f"{BASE_URL}{separator}f_w=1&f_lang={lang_code}", wait_until="networkidle")


def _open_sidebar_page(page: Page, label_pattern: re.Pattern[str], heading_pattern: re.Pattern[str]) -> None:
    sidebar = page.locator('[data-testid="stSidebar"]')
    page_link = sidebar.locator("label").filter(has_text=label_pattern).first
    expect(page_link).to_be_visible()
    page_link.click()
    expect(page.get_by_role("heading", name=heading_pattern)).to_be_visible()


def _open_account(page: Page, label_pattern: re.Pattern[str], heading_pattern: re.Pattern[str]) -> None:
    _open_sidebar_page(page, label_pattern, heading_pattern)


def _open_documents(page: Page, label_pattern: re.Pattern[str], heading_pattern: re.Pattern[str]) -> None:
    _open_sidebar_page(page, label_pattern, heading_pattern)


def _open_settings(page: Page, label_pattern: re.Pattern[str], heading_pattern: re.Pattern[str]) -> None:
    _open_sidebar_page(page, label_pattern, heading_pattern)


def _assert_account_core_ui(
    page: Page,
    add_tx_pattern: re.Pattern[str],
    transactions_pattern: re.Pattern[str],
) -> None:
    expect(page.get_by_text(add_tx_pattern)).to_be_visible()
    expect(page.get_by_role("heading", name=transactions_pattern)).to_be_visible()


def _add_basic_transaction(
    page: Page,
    add_tx_pattern: re.Pattern[str],
    amount_label: re.Pattern[str],
    note_selector: str,
    save_button_pattern: re.Pattern[str],
    success_pattern: re.Pattern[str],
    monthly_items_close_pattern: re.Pattern[str],
    note_prefix: str,
) -> None:
    page.get_by_text(add_tx_pattern).click()
    page.get_by_label(amount_label).first.fill("17")

    note_value = f"{note_prefix}-{int(time.time())}"
    page.locator(note_selector).first.fill(note_value)
    page.get_by_role("button", name=save_button_pattern).click()

    expect(page.get_by_text(success_pattern).first).to_be_visible()
    expect(page.locator("body")).to_contain_text(note_value)
    expect(page.get_by_role("button", name=monthly_items_close_pattern)).to_have_count(0)


def _selectbox_input(page: Page, label_pattern: re.Pattern[str]):
    return (
        page.locator('div[data-testid="stSelectbox"]')
        .filter(has_text=label_pattern)
        .first
        .locator('input[role="combobox"]')
        .first
    )


def _choose_selectbox_option(page: Page, label_pattern: re.Pattern[str], option_pattern: re.Pattern[str]) -> None:
    selectbox = _selectbox_input(page, label_pattern)
    expect(selectbox).to_be_visible()
    selectbox.click()
    page.get_by_role("option", name=option_pattern).click()


def _combobox_after_text(page: Page, label_text: str):
    return page.locator(
        f'xpath=//*[normalize-space(text())="{label_text}"]/following::input[@role="combobox"][1]'
    ).first


def _click_tab(page: Page, name_pattern: re.Pattern[str]) -> None:
    page.get_by_role("tab", name=name_pattern).last.click()


def _click_checkbox_label(page: Page, label_pattern: re.Pattern[str]) -> None:
    page.locator("label").filter(has_text=label_pattern).last.click()


def _add_and_delete_basic_document(
    page: Page,
    doc_name: str,
    save_button_pattern: re.Pattern[str],
    confirm_delete_pattern: re.Pattern[str],
    delete_button_pattern: re.Pattern[str],
) -> None:
    page.locator("div.st-key-mustndaty_add_btn button").first.click()
    page.get_by_label(re.compile(r"^Document Name$|^اسم المستند$")).fill(doc_name)
    page.get_by_role("button", name=save_button_pattern).click()

    expect(page.locator("body")).to_contain_text(doc_name)
    document_selector = page.locator('input[role="combobox"]').last
    document_selector.click()
    page.get_by_role("option", name=re.compile(re.escape(doc_name))).click()

    confirm_delete_label = page.get_by_text(confirm_delete_pattern, exact=True).last
    expect(confirm_delete_label).to_be_visible()
    confirm_delete_label.click()
    delete_button = page.get_by_role("button", name=delete_button_pattern)
    expect(delete_button).to_be_enabled()
    delete_button.click()

    expect(page.locator("body")).not_to_contain_text(doc_name)


def test_floosy_english_smoke(page: Page) -> None:
    _goto_language(page, "en")
    _open_account(page, re.compile(r"^Account$"), re.compile(r"^Account$"))
    _assert_account_core_ui(
        page,
        re.compile(r"Add New Transaction"),
        re.compile(r"^Transactions$"),
    )


def test_floosy_arabic_smoke(page: Page) -> None:
    _goto_language(page, "ar")
    _open_account(page, re.compile(r"^الحساب$"), re.compile(r"^الحساب$"))
    _assert_account_core_ui(
        page,
        re.compile(r"إضافة معاملة جديدة"),
        re.compile(r"^سجل المعاملات$"),
    )

def test_account_can_add_transaction_without_opening_monthly_items(page: Page) -> None:
    _goto_language(page, "en")
    _open_account(page, re.compile(r"^Account$"), re.compile(r"^Account$"))
    _add_basic_transaction(
        page,
        add_tx_pattern=re.compile(r"Add New Transaction"),
        amount_label=re.compile(r"^Amount$"),
        note_selector='input[aria-label*="Note"]',
        save_button_pattern=re.compile(r"Save Transaction"),
        success_pattern=re.compile(r"Transaction saved successfully"),
        monthly_items_close_pattern=re.compile(r"Close Monthly Items"),
        note_prefix="playwright-smoke-en",
    )


def test_account_can_add_transaction_in_arabic_without_opening_monthly_items(page: Page) -> None:
    _goto_language(page, "ar")
    _open_account(page, re.compile(r"^الحساب$"), re.compile(r"^الحساب$"))
    _add_basic_transaction(
        page,
        add_tx_pattern=re.compile(r"إضافة معاملة جديدة"),
        amount_label=re.compile(r"^المبلغ$"),
        note_selector='input[aria-label*="ملاحظة"]',
        save_button_pattern=re.compile(r"حفظ المعاملة"),
        success_pattern=re.compile(r"تمت إضافة المعاملة بنجاح|تم حفظ المعاملة"),
        monthly_items_close_pattern=re.compile(r"إغلاق إدارة العناصر الشهرية"),
        note_prefix="playwright-smoke-ar",
    )


def test_documents_can_add_and_delete_in_english(page: Page) -> None:
    _goto_language(page, "en")
    _open_documents(page, re.compile(r"^Documents$"), re.compile(r"^Documents$"))
    _add_and_delete_basic_document(
        page,
        doc_name=f"playwright-doc-en-{int(time.time())}",
        save_button_pattern=re.compile(r"^Save$"),
        confirm_delete_pattern=re.compile(r"^Confirm Document Deletion$"),
        delete_button_pattern=re.compile(r"^Delete Document$"),
    )


def test_documents_can_add_and_delete_in_arabic(page: Page) -> None:
    _goto_language(page, "ar")
    _open_documents(page, re.compile(r"^مستنداتي$"), re.compile(r"^مستنداتي$"))
    _add_and_delete_basic_document(
        page,
        doc_name=f"مستند-اختبار-{int(time.time())}",
        save_button_pattern=re.compile(r"^حفظ$"),
        confirm_delete_pattern=re.compile(r"^تأكيد حذف المستند$"),
        delete_button_pattern=re.compile(r"^حذف المستند$"),
    )


def test_settings_language_switch_updates_multiple_pages(page: Page) -> None:
    _goto_language(page, "en")
    _open_settings(page, re.compile(r"^Settings$"), re.compile(r"^Floosy Settings$"))

    expect(page.get_by_text(re.compile(r"Cloud Status Bar: Disabled"))).to_be_visible()

    language_input = _combobox_after_text(page, "Language")
    expect(language_input).to_be_visible()
    language_input.click()
    page.get_by_role("option", name=re.compile(r"^العربية$")).click()

    expect(page.get_by_role("heading", name=re.compile(r"^إعدادات فلوسي$"))).to_be_visible()
    expect(page.locator('[data-testid="stSidebar"]')).to_contain_text("الحساب")

    _open_account(page, re.compile(r"^الحساب$"), re.compile(r"^الحساب$"))
    expect(page.get_by_text(re.compile(r"إضافة معاملة جديدة"))).to_be_visible()
    expect(page.get_by_role("heading", name=re.compile(r"^سجل المعاملات$"))).to_be_visible()


def test_settings_cloud_status_disabled_then_ready(page: Page) -> None:
    if not EXPECT_CLOUD_CONFIG:
        pytest.skip("Configured cloud flow is skipped when running against a no-secrets server.")

    _goto_language(page, "en")
    _open_settings(page, re.compile(r"^Settings$"), re.compile(r"^Floosy Settings$"))

    expect(page.get_by_text(re.compile(r"Cloud Status Bar: Disabled"))).to_be_visible()
    expect(page.get_by_text(re.compile(r"Cloud is currently disabled\. You can enable it or export your data now\."))).to_be_visible()

    _click_tab(page, re.compile(r"^Cloud$"))
    expect(page.get_by_text(re.compile(r"Cloud sync is disabled\. Please enable it first from the Privacy tab\."))).to_be_visible()

    _click_tab(page, re.compile(r"^Privacy$"))
    _click_checkbox_label(page, re.compile(r"^Enable Cloud Sync \(Optional\)$"))

    expect(page.get_by_text(re.compile(r"Cloud Status Bar: Ready"))).to_be_visible()
    expect(page.get_by_text(re.compile(r"Cloud sync is enabled and ready\. Sign in from the Cloud tab to start syncing\."))).to_be_visible()

    _click_tab(page, re.compile(r"^Cloud$"))
    expect(page.get_by_role("heading", name=re.compile(r"Cloud Account \(Supabase\)"))).to_be_visible()
    expect(_combobox_after_text(page, "Action")).to_be_visible()
    expect(page.get_by_label(re.compile(r"^Email$"))).to_be_visible()
    expect(page.get_by_label(re.compile(r"^Password$"))).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"^Continue$"))).to_be_visible()


def test_documents_modal_is_usable_on_short_viewport(page: Page) -> None:
    page.set_viewport_size({"width": 1280, "height": 620})
    _goto_language(page, "en")
    _open_documents(page, re.compile(r"^Documents$"), re.compile(r"^Documents$"))

    page.locator("div.st-key-mustndaty_add_btn button").first.click()
    expect(page.get_by_text(re.compile(r"^Add Document$"))).to_be_visible()
    expect(page.get_by_label(re.compile(r"^Document Name$"))).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"^Save$"))).to_be_visible()
    expect(page.get_by_role("button", name=re.compile(r"^Cancel$"))).to_be_visible()

    page.get_by_role("button", name=re.compile(r"^Cancel$")).click()
    expect(page.get_by_role("button", name=re.compile(r"^Cancel$"))).to_have_count(0)


def test_settings_cloud_status_requires_setup_without_secrets(page: Page) -> None:
    if EXPECT_CLOUD_CONFIG:
        pytest.skip("No-secrets cloud flow only runs against a server without Supabase secrets.")

    _goto_language(page, "en")
    _open_settings(page, re.compile(r"^Settings$"), re.compile(r"^Floosy Settings$"))

    expect(page.get_by_text(re.compile(r"Cloud Status Bar: Disabled"))).to_be_visible()

    _click_tab(page, re.compile(r"^Privacy$"))
    _click_checkbox_label(page, re.compile(r"^Enable Cloud Sync \(Optional\)$"))

    expect(page.get_by_text(re.compile(r"Cloud Status Bar: Setup Required"))).to_be_visible()
    expect(page.get_by_text(re.compile(r"Cloud sync is enabled, but Supabase is not configured yet\. Add the connection secrets first\."))).to_be_visible()
    expect(page.get_by_text(re.compile(r"Cloud sync is enabled but not fully configured\. Sync will not start until Supabase secrets are added\."))).to_be_visible()

    _click_tab(page, re.compile(r"^Cloud$"))
    expect(page.get_by_text(re.compile(r"To enable cloud sync, add SUPABASE_URL and SUPABASE_ANON_KEY in secrets or environment variables\."))).to_be_visible()
