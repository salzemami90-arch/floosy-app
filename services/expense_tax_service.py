from __future__ import annotations

from services.tax_readiness import ensure_tax_state


class ExpenseTaxService:
    """Read/write helper to attach tax classification to expense transactions."""

    DEDUCTIBLE_CODE = "expense_deductible_generic"
    NON_DEDUCTIBLE_CODE = "expense_non_deductible_generic"

    @staticmethod
    def _as_bool(value, fallback: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on", "نعم"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", "لا"}:
                return False
        return bool(fallback)

    @classmethod
    def _fallback_tag(cls, deductible: bool) -> dict:
        if deductible:
            return {
                "code": cls.DEDUCTIBLE_CODE,
                "name": "مصروف قابل للخصم",
                "kind": "expense",
                "deductible": True,
                "tax_applicable": False,
                "sort_order": 90,
                "active": True,
            }
        return {
            "code": cls.NON_DEDUCTIBLE_CODE,
            "name": "مصروف غير قابل للخصم",
            "kind": "expense",
            "deductible": False,
            "tax_applicable": False,
            "sort_order": 91,
            "active": True,
        }

    @classmethod
    def _collect_tags(cls, session_state, include_inactive: bool = True) -> list[dict]:
        ensure_tax_state(session_state)
        raw_tags = session_state.get("tax_tags", [])
        if not isinstance(raw_tags, list):
            raw_tags = []

        tags = []
        for item in raw_tags:
            if not isinstance(item, dict):
                continue

            code = str(item.get("code", "") or "").strip()
            if not code:
                continue

            kind = str(item.get("kind", "expense") or "expense").strip().lower()
            if kind not in {"income", "expense", "both"}:
                kind = "expense"

            active = cls._as_bool(item.get("active", True), True)
            if not include_inactive and not active:
                continue

            tags.append(
                {
                    "code": code,
                    "name": str(item.get("name", "") or code),
                    "kind": kind,
                    "deductible": cls._as_bool(item.get("deductible", True), True),
                    "tax_applicable": cls._as_bool(item.get("tax_applicable", True), True),
                    "sort_order": int(item.get("sort_order", 0) or 0),
                    "active": active,
                }
            )

        if not any(t["code"] == cls.DEDUCTIBLE_CODE for t in tags):
            tags.append(cls._fallback_tag(True))
        if not any(t["code"] == cls.NON_DEDUCTIBLE_CODE for t in tags):
            tags.append(cls._fallback_tag(False))

        return tags

    @classmethod
    def expense_options(cls, session_state, is_en: bool = False) -> list[dict]:
        tags = [
            tag
            for tag in cls._collect_tags(session_state, include_inactive=False)
            if tag.get("kind") in {"expense", "both"}
        ]
        tags.sort(key=lambda tag: (int(tag.get("sort_order", 0)), str(tag.get("name", "")).lower()))

        options = []
        for tag in tags:
            deductible = bool(tag.get("deductible", False))
            suffix_ar = "قابل للخصم" if deductible else "غير قابل للخصم"
            suffix_en = "Deductible" if deductible else "Non-deductible"
            label = f"{tag['name']} ({suffix_en})" if is_en else f"{tag['name']} ({suffix_ar})"
            options.append(
                {
                    "code": str(tag.get("code", "")),
                    "name": str(tag.get("name", "")),
                    "deductible": deductible,
                    "label": label,
                }
            )
        return options

    @classmethod
    def _infer_deductible_from_text(cls, tx: dict) -> bool:
        category = str(tx.get("category", "") or "").strip().lower()
        note = str(tx.get("note", "") or "").strip().lower()
        combined = f"{category} {note}"

        deductible_keywords = [
            "إيجار", "قسط", "فاتورة", "فواتير", "اتصالات", "اشتراك", "تأمين",
            "رسوم", "رواتب", "rent", "installment", "bill", "telecom",
            "subscription", "insurance", "salary", "fee",
        ]
        non_deductible_keywords = [
            "شخصي", "قهوة", "طلعة", "هدايا", "تسوق", "مطاعم",
            "personal", "coffee", "outing", "gift", "shopping", "restaurant",
        ]

        if any(token.lower() in combined for token in non_deductible_keywords):
            return False
        if any(token.lower() in combined for token in deductible_keywords):
            return True
        return False

    @classmethod
    def resolve_tag(cls, session_state, code: str | None, fallback_deductible: bool = False) -> dict:
        wanted = str(code or "").strip()
        tags = cls._collect_tags(session_state, include_inactive=True)
        by_code = {str(tag.get("code", "")): tag for tag in tags}

        if wanted and wanted in by_code:
            tag = by_code[wanted]
        else:
            fallback_code = cls.DEDUCTIBLE_CODE if fallback_deductible else cls.NON_DEDUCTIBLE_CODE
            tag = by_code.get(fallback_code, cls._fallback_tag(bool(fallback_deductible)))

        return {
            "code": str(tag.get("code", "")),
            "name": str(tag.get("name", "")),
            "deductible": bool(tag.get("deductible", False)),
            "classification": "deductible" if bool(tag.get("deductible", False)) else "non_deductible",
        }

    @classmethod
    def normalize_transaction(cls, session_state, tx: dict) -> dict:
        if not isinstance(tx, dict):
            return {}

        normalized = dict(tx)
        raw_type = str(normalized.get("type", "") or "").strip()
        is_expense = raw_type == "مصروف" or raw_type.lower() == "expense"

        if not is_expense:
            normalized["tax_tag_code"] = ""
            normalized["tax_tag_name"] = ""
            normalized["tax_deductible"] = False
            normalized["tax_classification"] = "not_applicable"
            return normalized

        raw_classification = str(normalized.get("tax_classification", "") or "").strip().lower()
        has_non_deductible_hint = raw_classification in {"non_deductible", "غير قابل للخصم", "non-deductible"}
        has_deductible_hint = raw_classification in {"deductible", "قابل للخصم"}
        has_bool_hint = "tax_deductible" in normalized

        fallback_deductible = cls._infer_deductible_from_text(normalized)
        if has_non_deductible_hint:
            fallback_deductible = False
        elif has_deductible_hint:
            fallback_deductible = True
        elif has_bool_hint:
            fallback_deductible = cls._as_bool(normalized.get("tax_deductible", False), False)

        selected_code = str(
            normalized.get("tax_tag_code")
            or normalized.get("expense_tax_tag_code")
            or ""
        ).strip()
        resolved = cls.resolve_tag(session_state, selected_code, fallback_deductible=fallback_deductible)
        normalized["tax_tag_code"] = resolved["code"]
        normalized["tax_tag_name"] = resolved["name"]
        normalized["tax_deductible"] = bool(resolved["deductible"])
        normalized["tax_classification"] = str(resolved["classification"])
        return normalized

    @classmethod
    def expense_breakdown(cls, transactions: list[dict], currency: str | None = None) -> dict:
        deductible_amount = 0.0
        non_deductible_amount = 0.0
        deductible_count = 0
        non_deductible_count = 0

        for tx in transactions:
            if not isinstance(tx, dict):
                continue
            if str(tx.get("type", "") or "").strip() != "مصروف":
                continue
            if currency and str(tx.get("currency", "") or "").strip() != str(currency).strip():
                continue

            amount = float(tx.get("amount", 0.0) or 0.0)
            if cls._as_bool(tx.get("tax_deductible", False), False):
                deductible_amount += amount
                deductible_count += 1
            else:
                non_deductible_amount += amount
                non_deductible_count += 1

        return {
            "deductible_amount": float(deductible_amount),
            "non_deductible_amount": float(non_deductible_amount),
            "deductible_count": int(deductible_count),
            "non_deductible_count": int(non_deductible_count),
            "total_expense": float(deductible_amount + non_deductible_amount),
        }
