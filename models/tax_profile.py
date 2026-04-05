from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class TaxProfile:
    country_code: str = "KW"
    tax_mode_enabled: bool = False
    tax_name: str = "VAT"
    tax_basis_mode: str = "invoice"  # invoice, net_profit
    regime: str = "standard"
    default_tax_rate: float = 0.0
    prices_include_tax: bool = False
    registration_number: str = ""
    business_name: str = ""
    contact_email: str = ""
    reporting_basis: str = "cash"  # cash, accrual
    filing_frequency: str = "monthly"  # monthly, quarterly, yearly
    effective_from: date | None = None
    last_reviewed_on: date | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "country_code": self.country_code,
            "tax_mode_enabled": bool(self.tax_mode_enabled),
            "tax_name": self.tax_name,
            "tax_basis_mode": self.tax_basis_mode,
            "regime": self.regime,
            "default_tax_rate": float(self.default_tax_rate),
            "prices_include_tax": bool(self.prices_include_tax),
            "registration_number": self.registration_number,
            "business_name": self.business_name,
            "contact_email": self.contact_email,
            "reporting_basis": self.reporting_basis,
            "filing_frequency": self.filing_frequency,
            "effective_from": self.effective_from.strftime("%Y-%m-%d") if self.effective_from else "",
            "last_reviewed_on": self.last_reviewed_on.strftime("%Y-%m-%d") if self.last_reviewed_on else "",
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaxProfile":
        def _parse_date(raw_value):
            if isinstance(raw_value, date):
                return raw_value
            if not raw_value:
                return None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(str(raw_value), fmt).date()
                except ValueError:
                    continue
            return None

        def _to_float(raw_value, fallback=0.0):
            try:
                return float(raw_value)
            except (TypeError, ValueError):
                return float(fallback)

        def _normalize_basis_mode(raw_value):
            value = str(raw_value or "invoice").strip().lower()
            if value in {"profit", "net_profit", "net-profit"}:
                return "net_profit"
            return "invoice"

        return cls(
            country_code=str(data.get("country_code", "KW") or "KW"),
            tax_mode_enabled=bool(data.get("tax_mode_enabled", False)),
            tax_name=str(data.get("tax_name", "VAT") or "VAT").strip() or "VAT",
            tax_basis_mode=_normalize_basis_mode(data.get("tax_basis_mode", "invoice")),
            regime=str(data.get("regime", "standard") or "standard"),
            default_tax_rate=max(0.0, _to_float(data.get("default_tax_rate", 0.0))),
            prices_include_tax=bool(data.get("prices_include_tax", False)),
            registration_number=str(data.get("registration_number", "") or ""),
            business_name=str(data.get("business_name", "") or ""),
            contact_email=str(data.get("contact_email", "") or ""),
            reporting_basis=str(data.get("reporting_basis", "cash") or "cash"),
            filing_frequency=str(data.get("filing_frequency", "monthly") or "monthly"),
            effective_from=_parse_date(data.get("effective_from")),
            last_reviewed_on=_parse_date(data.get("last_reviewed_on")),
            notes=str(data.get("notes", "") or ""),
        )
