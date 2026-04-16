from __future__ import annotations


INCOME_CATEGORY_PAIRS = [
    ("راتب", "Salary"),
    ("مبيعات", "Sales"),
    ("دفعة عميل", "Client Payment"),
    ("دخل مشروع", "Project Income"),
    ("استرجاع", "Refund"),
    ("هدية / دعم", "Gift / Support"),
    ("دخل إضافي", "Extra Income"),
    ("دخل آخر", "Other Income"),
]

EXPENSE_CATEGORY_PAIRS = [
    ("إيجار / قسط", "Rent / Installment"),
    ("فواتير", "Bills"),
    ("مشتريات", "Shopping"),
    ("طلعات وكوفي", "Coffee / Outings"),
    ("أكل أونلاين", "Food Delivery"),
    ("مواصلات", "Transport"),
    ("صحة / صالون", "Health / Salon"),
    ("مستلزمات", "Supplies"),
    ("تسويق", "Marketing"),
    ("اشتراكات", "Subscriptions"),
    ("رواتب", "Payroll"),
    ("رسوم بنكية", "Bank Fees"),
    ("ضرائب / رسوم حكومية", "Taxes / Government Fees"),
    ("أخرى", "Other"),
]

ALL_CATEGORY_PAIRS = []
_seen_ar = set()
for pair in INCOME_CATEGORY_PAIRS + EXPENSE_CATEGORY_PAIRS:
    if pair[0] in _seen_ar:
        continue
    ALL_CATEGORY_PAIRS.append(pair)
    _seen_ar.add(pair[0])

CATEGORY_AR_TO_EN = dict(ALL_CATEGORY_PAIRS)
CATEGORY_EN_TO_AR = {en: ar for ar, en in ALL_CATEGORY_PAIRS}


def is_income_type(tx_type: str) -> bool:
    return str(tx_type or "").strip() in {"دخل", "Income"}


def localized_categories(tx_type: str, is_en: bool) -> list[str]:
    pairs = INCOME_CATEGORY_PAIRS if is_income_type(tx_type) else EXPENSE_CATEGORY_PAIRS
    return [en if is_en else ar for ar, en in pairs]


def localized_all_categories(is_en: bool) -> list[str]:
    return [en if is_en else ar for ar, en in ALL_CATEGORY_PAIRS]


def category_label(value: str, is_en: bool) -> str:
    clean = str(value or "").strip()
    if is_en:
        return CATEGORY_AR_TO_EN.get(clean, clean)
    return CATEGORY_EN_TO_AR.get(clean, clean)
