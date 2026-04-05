from dataclasses import dataclass


@dataclass
class TaxTag:
    code: str
    name: str
    kind: str = "expense"  # income, expense, both
    deductible: bool = True
    tax_applicable: bool = True
    default_rate: float = 0.0
    sort_order: int = 0
    active: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "kind": self.kind,
            "deductible": bool(self.deductible),
            "tax_applicable": bool(self.tax_applicable),
            "default_rate": float(self.default_rate),
            "sort_order": int(self.sort_order),
            "active": bool(self.active),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaxTag":
        def _to_float(raw_value, fallback=0.0):
            try:
                return float(raw_value)
            except (TypeError, ValueError):
                return float(fallback)

        def _to_int(raw_value, fallback=0):
            try:
                return int(raw_value)
            except (TypeError, ValueError):
                return int(fallback)

        return cls(
            code=str(data.get("code", "") or ""),
            name=str(data.get("name", "") or ""),
            kind=str(data.get("kind", "expense") or "expense"),
            deductible=bool(data.get("deductible", True)),
            tax_applicable=bool(data.get("tax_applicable", True)),
            default_rate=max(0.0, _to_float(data.get("default_rate", 0.0))),
            sort_order=max(0, _to_int(data.get("sort_order", 0))),
            active=bool(data.get("active", True)),
            description=str(data.get("description", "") or ""),
        )
