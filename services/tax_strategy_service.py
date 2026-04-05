from __future__ import annotations

from models.tax_profile import TaxProfile


class TaxStrategyService:
    @staticmethod
    def normalize_basis_mode(raw_value: str) -> str:
        value = str(raw_value or "invoice").strip().lower()
        if value in {"profit", "net_profit", "net-profit"}:
            return "net_profit"
        return "invoice"

    @classmethod
    def basis_label(cls, basis_mode: str, is_en: bool = False) -> str:
        labels = {
            "invoice": ("الفواتير / المبيعات", "Invoices / Sales"),
            "net_profit": ("صافي الربح", "Net Profit"),
        }
        mode = cls.normalize_basis_mode(basis_mode)
        ar, en = labels.get(mode, labels["invoice"])
        return en if is_en else ar

    @staticmethod
    def _currency_symbol(raw_currency: str) -> str:
        value = str(raw_currency or "").strip()
        if " - " in value:
            return value.split(" - ", 1)[0].strip()
        return value

    @classmethod
    def _currency_matches(cls, left: str, right: str) -> bool:
        if not right:
            return True
        return cls._currency_symbol(left) == cls._currency_symbol(right)

    @staticmethod
    def _to_float(raw_value, fallback: float = 0.0) -> float:
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return float(fallback)

    @classmethod
    def estimate_month_tax(
        cls,
        profile: TaxProfile,
        transactions,
        invoice_report: dict | None = None,
        currency: str | None = None,
    ) -> dict:
        report = invoice_report or {}
        totals = report.get("totals", {}) if isinstance(report, dict) else {}
        rate = max(0.0, cls._to_float(getattr(profile, "default_tax_rate", 0.0), 0.0))
        basis_mode = cls.normalize_basis_mode(getattr(profile, "tax_basis_mode", "invoice"))

        income = 0.0
        expense = 0.0
        for tx in transactions or []:
            tx_currency = getattr(tx, "currency", "")
            if currency and not cls._currency_matches(tx_currency, currency):
                continue
            tx_type = str(getattr(tx, "tx_type", "") or "").strip()
            amount = cls._to_float(getattr(tx, "amount", 0.0), 0.0)
            if tx_type == "دخل":
                income += amount
            elif tx_type == "مصروف":
                expense += amount

        net_profit = income - expense
        taxable_profit = max(net_profit, 0.0)

        if basis_mode == "net_profit":
            return {
                "basis_mode": basis_mode,
                "basis_amount": round(taxable_profit, 3),
                "estimated_tax": round(taxable_profit * (rate / 100.0), 3),
                "income": round(income, 3),
                "expense": round(expense, 3),
                "net_profit": round(net_profit, 3),
                "invoice_subtotal": round(cls._to_float(totals.get("subtotal", 0.0), 0.0), 3),
                "invoice_total": round(cls._to_float(totals.get("total", 0.0), 0.0), 3),
                "invoice_tax": round(cls._to_float(totals.get("tax", 0.0), 0.0), 3),
            }

        base_amount = cls._to_float(
            totals.get("total" if getattr(profile, "prices_include_tax", False) else "subtotal", 0.0),
            0.0,
        )
        return {
            "basis_mode": basis_mode,
            "basis_amount": round(base_amount, 3),
            "estimated_tax": round(cls._to_float(totals.get("tax", 0.0), 0.0), 3),
            "income": round(income, 3),
            "expense": round(expense, 3),
            "net_profit": round(net_profit, 3),
            "invoice_subtotal": round(cls._to_float(totals.get("subtotal", 0.0), 0.0), 3),
            "invoice_total": round(cls._to_float(totals.get("total", 0.0), 0.0), 3),
            "invoice_tax": round(cls._to_float(totals.get("tax", 0.0), 0.0), 3),
        }
