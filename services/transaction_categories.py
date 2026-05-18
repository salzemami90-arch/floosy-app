from __future__ import annotations

from services.i18n import get_lang_code


INCOME_CATEGORY_ROWS = [
    {"ar": "راتب", "en": "Salary", "zh": "薪资", "ko": "급여", "ja": "給与", "id": "Gaji", "ms": "Gaji"},
    {"ar": "مبيعات", "en": "Sales", "zh": "销售", "ko": "매출", "ja": "売上", "id": "Penjualan", "ms": "Jualan"},
    {"ar": "دفعة عميل", "en": "Client Payment", "zh": "客户付款", "ko": "고객 결제", "ja": "顧客支払い", "id": "Pembayaran Klien", "ms": "Pembayaran Klien"},
    {"ar": "دخل مشروع", "en": "Project Income", "zh": "项目收入", "ko": "프로젝트 수입", "ja": "プロジェクト収入", "id": "Pendapatan Proyek", "ms": "Pendapatan Projek"},
    {"ar": "استرجاع", "en": "Refund", "zh": "退款", "ko": "환불", "ja": "返金", "id": "Pengembalian Dana", "ms": "Bayaran Balik"},
    {"ar": "هدية / دعم", "en": "Gift / Support", "zh": "礼物 / 支持", "ko": "선물 / 지원", "ja": "ギフト / 支援", "id": "Hadiah / Dukungan", "ms": "Hadiah / Sokongan"},
    {"ar": "دخل إضافي", "en": "Extra Income", "zh": "额外收入", "ko": "추가 수입", "ja": "追加収入", "id": "Pendapatan Tambahan", "ms": "Pendapatan Tambahan"},
    {"ar": "دخل آخر", "en": "Other Income", "zh": "其他收入", "ko": "기타 수입", "ja": "その他収入", "id": "Pendapatan Lain", "ms": "Pendapatan Lain"},
]

EXPENSE_CATEGORY_ROWS = [
    {"ar": "إيجار / قسط", "en": "Rent / Installment", "zh": "租金 / 分期", "ko": "임대료 / 할부", "ja": "家賃 / 分割払い", "id": "Sewa / Cicilan", "ms": "Sewa / Ansuran"},
    {"ar": "فواتير", "en": "Bills", "zh": "账单", "ko": "청구서", "ja": "請求", "id": "Tagihan", "ms": "Bil"},
    {"ar": "مشتريات", "en": "Shopping", "zh": "购物", "ko": "쇼핑", "ja": "買い物", "id": "Belanja", "ms": "Belanja"},
    {"ar": "طلعات وكوفي", "en": "Coffee / Outings", "zh": "咖啡 / 外出", "ko": "커피 / 외출", "ja": "コーヒー / 外出", "id": "Kopi / Keluar", "ms": "Kopi / Keluar"},
    {"ar": "أكل أونلاين", "en": "Food Delivery", "zh": "外卖", "ko": "음식 배달", "ja": "フードデリバリー", "id": "Pesan Antar Makanan", "ms": "Penghantaran Makanan"},
    {"ar": "مواصلات", "en": "Transport", "zh": "交通", "ko": "교통", "ja": "交通", "id": "Transportasi", "ms": "Pengangkutan"},
    {"ar": "صحة / صالون", "en": "Health / Salon", "zh": "健康 / 沙龙", "ko": "건강 / 살롱", "ja": "健康 / サロン", "id": "Kesehatan / Salon", "ms": "Kesihatan / Salon"},
    {"ar": "مستلزمات", "en": "Supplies", "zh": "用品", "ko": "용품", "ja": "用品", "id": "Perlengkapan", "ms": "Bekalan"},
    {"ar": "تسويق", "en": "Marketing", "zh": "营销", "ko": "마케팅", "ja": "マーケティング", "id": "Pemasaran", "ms": "Pemasaran"},
    {"ar": "اشتراكات", "en": "Subscriptions", "zh": "订阅", "ko": "구독", "ja": "サブスクリプション", "id": "Langganan", "ms": "Langganan"},
    {"ar": "رواتب", "en": "Payroll", "zh": "工资单", "ko": "급여 지급", "ja": "給与支払い", "id": "Penggajian", "ms": "Gaji Pekerja"},
    {"ar": "رسوم بنكية", "en": "Bank Fees", "zh": "银行费用", "ko": "은행 수수료", "ja": "銀行手数料", "id": "Biaya Bank", "ms": "Yuran Bank"},
    {"ar": "ضرائب / رسوم حكومية", "en": "Taxes / Government Fees", "zh": "税费 / 政府费用", "ko": "세금 / 정부 수수료", "ja": "税金 / 政府手数料", "id": "Pajak / Biaya Pemerintah", "ms": "Cukai / Yuran Kerajaan"},
    {"ar": "تحويل للمشروع", "en": "Project Transfer", "zh": "项目转移", "ko": "프로젝트 이체", "ja": "プロジェクト転送", "id": "Transfer Proyek", "ms": "Transfer Proyek"},
    {"ar": "أخرى", "en": "Other", "zh": "其他", "ko": "기타", "ja": "その他", "id": "Lainnya", "ms": "Lain-lain"},
]

INCOME_CATEGORY_PAIRS = [(row["ar"], row["en"]) for row in INCOME_CATEGORY_ROWS]
EXPENSE_CATEGORY_PAIRS = [(row["ar"], row["en"]) for row in EXPENSE_CATEGORY_ROWS]

ALL_CATEGORY_ROWS = []
_seen_ar = set()
for row in INCOME_CATEGORY_ROWS + EXPENSE_CATEGORY_ROWS:
    if row["ar"] in _seen_ar:
        continue
    ALL_CATEGORY_ROWS.append(row)
    _seen_ar.add(row["ar"])

ALL_CATEGORY_PAIRS = [(row["ar"], row["en"]) for row in ALL_CATEGORY_ROWS]

CATEGORY_AR_TO_EN = dict(ALL_CATEGORY_PAIRS)
CATEGORY_EN_TO_AR = {en: ar for ar, en in ALL_CATEGORY_PAIRS}
_CATEGORY_VALUE_TO_AR = {
    str(value).strip(): row["ar"]
    for row in ALL_CATEGORY_ROWS
    for value in row.values()
    if str(value).strip()
}


def is_income_type(tx_type: str) -> bool:
    return str(tx_type or "").strip() in {"دخل", "Income"}


def localized_categories(tx_type: str, is_en: bool) -> list[str]:
    rows = INCOME_CATEGORY_ROWS if is_income_type(tx_type) else EXPENSE_CATEGORY_ROWS
    code = _display_lang_code(is_en)
    return [row.get(code, row["en"] if code != "ar" else row["ar"]) for row in rows]


def localized_all_categories(is_en: bool) -> list[str]:
    code = _display_lang_code(is_en)
    return [row.get(code, row["en"] if code != "ar" else row["ar"]) for row in ALL_CATEGORY_ROWS]


def category_label(value: str, is_en: bool) -> str:
    clean = str(value or "").strip()
    canonical_ar = _CATEGORY_VALUE_TO_AR.get(clean, clean)
    code = _display_lang_code(is_en)
    for row in ALL_CATEGORY_ROWS:
        if row["ar"] == canonical_ar:
            return row.get(code, row["en"] if code != "ar" else row["ar"])
    return clean


def canonical_category(value: str) -> str:
    clean = str(value or "").strip()
    return _CATEGORY_VALUE_TO_AR.get(clean, clean)


def _display_lang_code(is_en: bool) -> str:
    code = get_lang_code()
    if code == "ar" and is_en:
        return "en"
    if code in {"zh", "ko", "ja", "id", "ms"}:
        return code
    return "en" if is_en else "ar"
