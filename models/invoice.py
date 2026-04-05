from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4


@dataclass
class Invoice:
    invoice_id: str
    invoice_number: str
    issue_date: date
    due_date: date | None = None
    customer_name: str = ""
    customer_tax_no: str = ""
    subtotal: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "د.ك"
    prices_include_tax: bool = False
    tax_source: str = "global"  # global, project, manual
    status: str = "draft"  # draft, sent, paid, cancelled
    notes: str = ""
    linked_project: str = ""
    paid_date: date | None = None
    line_items: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "issue_date": self.issue_date.strftime("%Y-%m-%d"),
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else "",
            "customer_name": self.customer_name,
            "customer_tax_no": self.customer_tax_no,
            "subtotal": float(self.subtotal),
            "tax_rate": float(self.tax_rate),
            "tax_amount": float(self.tax_amount),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "prices_include_tax": bool(self.prices_include_tax),
            "tax_source": self.tax_source,
            "status": self.status,
            "notes": self.notes,
            "linked_project": self.linked_project,
            "paid_date": self.paid_date.strftime("%Y-%m-%d") if self.paid_date else "",
            "line_items": list(self.line_items),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
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

        def _normalize_tax_source(raw_value):
            source = str(raw_value or "global").strip().lower()
            if source not in {"global", "project", "manual"}:
                return "global"
            return source

        issue_date = _parse_date(data.get("issue_date")) or date.today()
        due_date = _parse_date(data.get("due_date"))
        paid_date = _parse_date(data.get("paid_date"))

        subtotal = _to_float(data.get("subtotal", 0.0))
        tax_rate = _to_float(data.get("tax_rate", 0.0))
        tax_amount_raw = data.get("tax_amount", None)
        tax_amount = _to_float(tax_amount_raw, (subtotal * tax_rate / 100.0))
        total_raw = data.get("total_amount", None)
        total_amount = _to_float(total_raw, (subtotal + tax_amount))

        raw_line_items = data.get("line_items", [])
        if isinstance(raw_line_items, list):
            line_items = [item for item in raw_line_items if isinstance(item, dict)]
        else:
            line_items = []

        invoice_id = str(data.get("invoice_id", "") or "").strip() or str(uuid4())
        invoice_number = str(data.get("invoice_number", "") or "").strip()
        if not invoice_number:
            invoice_number = f"INV-{issue_date.strftime('%Y%m%d')}"

        return cls(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            customer_name=str(data.get("customer_name", "") or ""),
            customer_tax_no=str(data.get("customer_tax_no", "") or ""),
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=str(data.get("currency", "د.ك") or "د.ك"),
            prices_include_tax=bool(data.get("prices_include_tax", False)),
            tax_source=_normalize_tax_source(data.get("tax_source", "global")),
            status=str(data.get("status", "draft") or "draft"),
            notes=str(data.get("notes", "") or ""),
            linked_project=str(data.get("linked_project", "") or ""),
            paid_date=paid_date,
            line_items=line_items,
        )
