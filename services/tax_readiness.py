from models.tax_profile import TaxProfile
from models.tax_tag import TaxTag


TAX_GLOSSARY = [
    {"key": "invoice_system", "ar": "نظام الفواتير", "en": "Invoice System"},
    {"key": "tax_report", "ar": "تقرير ضريبي", "en": "Tax Report"},
    {"key": "expense_classification", "ar": "تصنيف المصاريف", "en": "Expense Classification"},
    {"key": "cash_flow", "ar": "التدفق النقدي", "en": "Cash Flow"},
    {"key": "tax_rate", "ar": "نسبة الضريبة", "en": "Tax Rate"},
    {"key": "tax_number", "ar": "الرقم الضريبي", "en": "Tax Registration Number"},
    {"key": "tax_period", "ar": "الفترة الضريبية", "en": "Tax Period"},
    {"key": "deductible", "ar": "قابل للخصم", "en": "Deductible"},
    {"key": "non_deductible", "ar": "غير قابل للخصم", "en": "Non-deductible"},
    {"key": "tax_ready", "ar": "جاهزية ضريبية", "en": "Tax Readiness"},
]


def default_tax_profile() -> TaxProfile:
    return TaxProfile(
        country_code="KW",
        tax_mode_enabled=False,
        tax_name="VAT",
        tax_basis_mode="invoice",
        regime="standard",
        default_tax_rate=0.0,
        prices_include_tax=False,
        reporting_basis="cash",
        filing_frequency="monthly",
    )


def default_tax_tags() -> list[TaxTag]:
    return [
        TaxTag(code="income_sales", name="مبيعات", kind="income", deductible=False, tax_applicable=True, sort_order=1),
        TaxTag(code="income_other", name="دخل آخر", kind="income", deductible=False, tax_applicable=False, sort_order=2),
        TaxTag(code="expense_rent", name="إيجار", kind="expense", deductible=True, tax_applicable=False, sort_order=10),
        TaxTag(code="expense_telecom", name="اتصالات", kind="expense", deductible=True, tax_applicable=True, sort_order=11),
        TaxTag(code="expense_salary", name="رواتب", kind="expense", deductible=True, tax_applicable=False, sort_order=12),
        TaxTag(code="expense_subscription", name="اشتراكات", kind="expense", deductible=True, tax_applicable=True, sort_order=13),
        TaxTag(code="expense_non_deductible_generic", name="مصروف شخصي", kind="expense", deductible=False, tax_applicable=False, sort_order=998),
        TaxTag(code="expense_deductible_generic", name="أخرى", kind="expense", deductible=True, tax_applicable=False, sort_order=999),
    ]


def get_tax_glossary(language: str = "ar") -> list[dict]:
    lang = "en" if str(language).lower().startswith("en") else "ar"
    return [{"key": row["key"], "label": row[lang]} for row in TAX_GLOSSARY]


def ensure_tax_state(session_state) -> None:
    session_state.setdefault("invoices", [])
    if not isinstance(session_state.get("invoices"), list):
        session_state["invoices"] = []

    profile_raw = session_state.get("tax_profile", {})
    if not isinstance(profile_raw, dict):
        profile_raw = {}
    session_state["tax_profile"] = TaxProfile.from_dict(profile_raw).to_dict()

    tags_raw = session_state.get("tax_tags", [])
    if not isinstance(tags_raw, list):
        tags_raw = []

    cleaned_tags = []
    for item in tags_raw:
        if isinstance(item, dict):
            cleaned_tags.append(TaxTag.from_dict(item).to_dict())

    defaults = [tag.to_dict() for tag in default_tax_tags()]
    if not cleaned_tags:
        cleaned_tags = defaults
    else:
        existing_codes = {
            str(item.get("code", "") or "").strip()
            for item in cleaned_tags
            if isinstance(item, dict)
        }
        for default_tag in defaults:
            code = str(default_tag.get("code", "") or "").strip()
            if code and code not in existing_codes:
                cleaned_tags.append(default_tag)

    session_state["tax_tags"] = cleaned_tags


def tax_readiness_snapshot(session_state) -> dict:
    ensure_tax_state(session_state)

    invoices = session_state.get("invoices", [])
    draft_count = 0
    sent_count = 0
    paid_count = 0

    for item in invoices:
        status = str(item.get("status", "draft") or "draft").lower()
        if status == "paid":
            paid_count += 1
        elif status == "sent":
            sent_count += 1
        else:
            draft_count += 1

    profile = TaxProfile.from_dict(session_state.get("tax_profile", {}))

    return {
        "tax_mode_enabled": bool(profile.tax_mode_enabled),
        "default_tax_rate": float(profile.default_tax_rate),
        "registration_number": profile.registration_number,
        "invoices_total": len(invoices),
        "invoices_draft": draft_count,
        "invoices_sent": sent_count,
        "invoices_paid": paid_count,
        "tags_count": len(session_state.get("tax_tags", [])),
    }
