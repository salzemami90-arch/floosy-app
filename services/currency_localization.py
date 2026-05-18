"""Currency display helpers shared across Floosy pages.

The app stores currency selections as the original ``CURRENCY_OPTIONS`` values
for backward compatibility.  These helpers keep that storage stable while
showing localized labels and unambiguous short codes in the UI.
"""

from __future__ import annotations


CURRENCY_LABELS: dict[str, dict[str, str]] = {
    "د.ك - دينار كويتي": {
        "ar": "د.ك - دينار كويتي",
        "en": "KWD - Kuwaiti Dinar",
        "zh": "KWD - 科威特第纳尔",
        "ko": "KWD - 쿠웨이트 디나르",
        "ja": "KWD - クウェートディナール",
        "id": "KWD - Dinar Kuwait",
        "ms": "KWD - Dinar Kuwait",
    },
    "ر.س - ريال سعودي": {
        "ar": "ر.س - ريال سعودي",
        "en": "SAR - Saudi Riyal",
        "zh": "SAR - 沙特里亚尔",
        "ko": "SAR - 사우디 리얄",
        "ja": "SAR - サウジリヤル",
        "id": "SAR - Riyal Saudi",
        "ms": "SAR - Riyal Saudi",
    },
    "د.إ - درهم إماراتي": {
        "ar": "د.إ - درهم إماراتي",
        "en": "AED - UAE Dirham",
        "zh": "AED - 阿联酋迪拉姆",
        "ko": "AED - UAE 디르함",
        "ja": "AED - UAEディルハム",
        "id": "AED - Dirham UEA",
        "ms": "AED - Dirham UEA",
    },
    "$ - دولار أمريكي": {
        "ar": "$ - دولار أمريكي",
        "en": "USD - US Dollar",
        "zh": "USD - 美元",
        "ko": "USD - 미국 달러",
        "ja": "USD - 米ドル",
        "id": "USD - Dolar AS",
        "ms": "USD - Dolar AS",
    },
    "€ - يورو": {
        "ar": "€ - يورو",
        "en": "EUR - Euro",
        "zh": "EUR - 欧元",
        "ko": "EUR - 유로",
        "ja": "EUR - ユーロ",
        "id": "EUR - Euro",
        "ms": "EUR - Euro",
    },
    "¥ - 人民币": {
        "ar": "¥ - يوان صيني",
        "en": "CNY - Chinese Yuan",
        "zh": "CNY - 人民币",
        "ko": "CNY - 중국 위안",
        "ja": "CNY - 中国人民元",
        "id": "CNY - Yuan Tiongkok",
        "ms": "CNY - Yuan Tiongkok",
    },
    "₩ - 원": {
        "ar": "₩ - وون كوري",
        "en": "KRW - Korean Won",
        "zh": "KRW - 韩元",
        "ko": "KRW - 대한민국 원",
        "ja": "KRW - 韓国ウォン",
        "id": "KRW - Won Korea",
        "ms": "KRW - Won Korea",
    },
    "¥ - 円": {
        "ar": "¥ - ين ياباني",
        "en": "JPY - Japanese Yen",
        "zh": "JPY - 日元",
        "ko": "JPY - 일본 엔",
        "ja": "JPY - 日本円",
        "id": "JPY - Yen Jepang",
        "ms": "JPY - Yen Jepang",
    },
    "Rp - Rupiah": {
        "ar": "Rp - روبية إندونيسية",
        "en": "IDR - Indonesian Rupiah",
        "zh": "IDR - 印尼盾",
        "ko": "IDR - 인도네시아 루피아",
        "ja": "IDR - インドネシアルピア",
        "id": "IDR - Rupiah Indonesia",
        "ms": "IDR - Rupiah Indonesia",
    },
    "S$ - SGD": {
        "ar": "S$ - دولار سنغافوري",
        "en": "SGD - Singapore Dollar",
        "zh": "SGD - 新加坡元",
        "ko": "SGD - 싱가포르 달러",
        "ja": "SGD - シンガポールドル",
        "id": "SGD - Dolar Singapura",
        "ms": "SGD - Dolar Singapura",
    },
}

CURRENCY_CODES: dict[str, str] = {
    "د.ك - دينار كويتي": "KWD",
    "ر.س - ريال سعودي": "SAR",
    "د.إ - درهم إماراتي": "AED",
    "$ - دولار أمريكي": "USD",
    "€ - يورو": "EUR",
    "¥ - 人民币": "CNY",
    "₩ - 원": "KRW",
    "¥ - 円": "JPY",
    "Rp - Rupiah": "IDR",
    "S$ - SGD": "SGD",
}

CURRENCY_SYMBOLS: dict[str, str] = {
    "د.ك - دينار كويتي": "د.ك",
    "ر.س - ريال سعودي": "ر.س",
    "د.إ - درهم إماراتي": "د.إ",
    "$ - دولار أمريكي": "$",
    "€ - يورو": "€",
    "¥ - 人民币": "¥",
    "₩ - 원": "₩",
    "¥ - 円": "¥",
    "Rp - Rupiah": "Rp",
    "S$ - SGD": "S$",
}

_SYMBOL_CODES: dict[str, str] = {
    "د.ك": "KWD",
    "ر.س": "SAR",
    "د.إ": "AED",
    "$": "USD",
    "€": "EUR",
    "¥": "CNY",
    "₩": "KRW",
    "Rp": "IDR",
    "S$": "SGD",
}

_LABEL_TO_CANONICAL: dict[str, str] = {}
for _canonical, _labels in CURRENCY_LABELS.items():
    _LABEL_TO_CANONICAL[_canonical] = _canonical
    _LABEL_TO_CANONICAL[CURRENCY_CODES[_canonical]] = _canonical
    _LABEL_TO_CANONICAL[CURRENCY_SYMBOLS[_canonical]] = _canonical
    for _label in _labels.values():
        _LABEL_TO_CANONICAL[_label] = _canonical

# A bare yen symbol is ambiguous.  Keep the historic CNY fallback for old rows,
# but exact stored options still display as CNY or JPY correctly.
_LABEL_TO_CANONICAL["¥"] = "¥ - 人民币"
_LABEL_TO_CANONICAL["JPY"] = "¥ - 円"
_LABEL_TO_CANONICAL["CNY"] = "¥ - 人民币"


def normalize_currency(value: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        return clean_value
    return _LABEL_TO_CANONICAL.get(clean_value, clean_value)


def currency_symbol(value: str) -> str:
    canonical = normalize_currency(value)
    if canonical in CURRENCY_SYMBOLS:
        return CURRENCY_SYMBOLS[canonical]
    if " - " in canonical:
        return canonical.split(" - ", 1)[0].strip()
    return canonical


def currency_code(value: str) -> str:
    canonical = normalize_currency(value)
    if canonical in CURRENCY_CODES:
        return CURRENCY_CODES[canonical]
    symbol = currency_symbol(canonical)
    return _SYMBOL_CODES.get(symbol, symbol)


def currency_matches(left: str, right: str) -> bool:
    if not str(right or "").strip():
        return True
    return currency_code(left) == currency_code(right)


def currency_option_label(value: str, lang_code: str) -> str:
    canonical = normalize_currency(value)
    labels = CURRENCY_LABELS.get(canonical)
    if not labels:
        return str(value or "").strip()
    code = str(lang_code or "ar").strip().lower()
    return labels.get(code, labels.get("en", canonical))


def currency_short_label(value: str, lang_code: str) -> str:
    code = str(lang_code or "ar").strip().lower()
    if code == "ar":
        return currency_symbol(value)
    return currency_code(value)


def currency_display_to_canonical_map(options: list[str], lang_code: str) -> dict[str, str]:
    display_map: dict[str, str] = {}
    symbol_counts: dict[str, int] = {}
    for option in options:
        symbol = currency_symbol(option)
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    for option in options:
        canonical = normalize_currency(option)
        symbol = currency_symbol(canonical)
        display_map[canonical] = canonical
        display_map[currency_option_label(canonical, lang_code)] = canonical
        display_map[currency_option_label(canonical, "ar")] = canonical
        display_map[currency_option_label(canonical, "en")] = canonical
        display_map[currency_code(canonical)] = canonical
        if symbol_counts.get(symbol, 0) <= 1:
            display_map[symbol] = canonical
        else:
            display_map.setdefault(symbol, normalize_currency(symbol))
    return display_map
