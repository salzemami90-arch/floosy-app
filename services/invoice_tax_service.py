from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import re
from uuid import uuid4

from models.invoice import Invoice
from repositories.base import FlossyRepository


ARABIC_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]


class InvoiceTaxService:
    """
    Business logic for invoices and tax reporting.
    Read/write through repository only; no UI code.
    """

    def __init__(self, repo: FlossyRepository):
        self.repo = repo

    @staticmethod
    def _to_float(raw_value, fallback=0.0) -> float:
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return float(fallback)

    @staticmethod
    def _round_money(value: float, decimals: int = 3) -> float:
        return round(float(value), decimals)

    @staticmethod
    def _parse_date(raw_value) -> date | None:
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

    @staticmethod
    def _normalize_status(raw_status: str) -> str:
        status = str(raw_status or "draft").strip().lower()
        return status if status in {"draft", "sent", "paid", "cancelled"} else "draft"

    @staticmethod
    def parse_month_key(month_key: str) -> tuple[int, int] | None:
        if not month_key or "-" not in month_key:
            return None
        year_txt, month_name = month_key.split("-", 1)
        if month_name not in ARABIC_MONTHS:
            return None
        try:
            year_value = int(year_txt)
        except ValueError:
            return None
        return year_value, ARABIC_MONTHS.index(month_name) + 1

    @classmethod
    def calculate_totals(
        cls,
        base_amount: float,
        tax_rate: float,
        prices_include_tax: bool = False,
        decimals: int = 3,
    ) -> dict:
        amount = max(0.0, cls._to_float(base_amount, 0.0))
        rate = max(0.0, cls._to_float(tax_rate, 0.0))

        # If prices_include_tax=True then `amount` is the gross amount and tax is extracted from it.
        if prices_include_tax and rate > 0:
            subtotal = amount / (1.0 + (rate / 100.0))
            tax_amount = amount - subtotal
            total = amount
        else:
            subtotal = amount
            tax_amount = subtotal * (rate / 100.0)
            total = subtotal + tax_amount

        return {
            "subtotal": cls._round_money(subtotal, decimals),
            "tax_rate": rate,
            "tax_amount": cls._round_money(tax_amount, decimals),
            "total_amount": cls._round_money(total, decimals),
        }

    def next_invoice_number(self, issue_date: date | None = None, prefix: str = "INV") -> str:
        issue = issue_date or date.today()
        ym = issue.strftime("%Y%m")
        pattern = re.compile(rf"^{re.escape(prefix)}-{ym}-(\d{{4}})$")

        max_serial = 0
        for inv in self.repo.list_invoices():
            match = pattern.match(str(inv.invoice_number or ""))
            if not match:
                continue
            serial = int(match.group(1))
            if serial > max_serial:
                max_serial = serial

        return f"{prefix}-{ym}-{max_serial + 1:04d}"

    def build_invoice(self, payload: dict) -> Invoice:
        profile = self.repo.get_tax_profile()

        issue_date = self._parse_date(payload.get("issue_date")) or date.today()
        due_date = self._parse_date(payload.get("due_date"))
        paid_date = self._parse_date(payload.get("paid_date"))

        tax_rate = self._to_float(payload.get("tax_rate", profile.default_tax_rate), profile.default_tax_rate)
        prices_include_tax = bool(payload.get("prices_include_tax", profile.prices_include_tax))

        tax_source = str(payload.get("tax_source", "") or "").strip().lower()
        if tax_source not in {"global", "project", "manual"}:
            tax_source = "global"

        raw_amount = payload.get("subtotal", payload.get("amount", 0.0))
        totals = self.calculate_totals(
            base_amount=raw_amount,
            tax_rate=tax_rate,
            prices_include_tax=prices_include_tax,
            decimals=3,
        )

        invoice_number = str(payload.get("invoice_number", "") or "").strip()
        if not invoice_number:
            invoice_number = self.next_invoice_number(issue_date=issue_date)

        status = self._normalize_status(str(payload.get("status", "draft") or "draft"))
        if status == "paid" and paid_date is None:
            paid_date = issue_date
        if status != "paid":
            paid_date = None

        line_items = payload.get("line_items", [])
        if isinstance(line_items, list):
            safe_line_items = [item for item in line_items if isinstance(item, dict)]
        else:
            safe_line_items = []

        return Invoice(
            invoice_id=str(payload.get("invoice_id", "") or "").strip() or str(uuid4()),
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            customer_name=str(payload.get("customer_name", "") or ""),
            customer_tax_no=str(payload.get("customer_tax_no", "") or ""),
            subtotal=totals["subtotal"],
            tax_rate=totals["tax_rate"],
            tax_amount=totals["tax_amount"],
            total_amount=totals["total_amount"],
            currency=str(payload.get("currency", "") or "").strip() or "د.ك",
            prices_include_tax=bool(prices_include_tax),
            tax_source=tax_source,
            status=status,
            notes=str(payload.get("notes", "") or ""),
            linked_project=str(payload.get("linked_project", "") or ""),
            paid_date=paid_date,
            line_items=safe_line_items,
        )

    def create_invoice(self, payload: dict) -> Invoice:
        invoice = self.build_invoice(payload)
        self.repo.add_invoice(invoice)
        return invoice

    def update_invoice(self, index: int, payload: dict) -> tuple[bool, Invoice | None]:
        invoices = self.repo.list_invoices()
        if index < 0 or index >= len(invoices):
            return False, None

        payload_copy = dict(payload)
        payload_copy.setdefault("invoice_id", invoices[index].invoice_id)
        payload_copy.setdefault("invoice_number", invoices[index].invoice_number)

        invoice = self.build_invoice(payload_copy)
        ok = self.repo.update_invoice(index, invoice)
        return ok, invoice if ok else None

    def set_invoice_status(self, index: int, status: str, paid_date: date | None = None) -> tuple[bool, Invoice | None]:
        invoices = self.repo.list_invoices()
        if index < 0 or index >= len(invoices):
            return False, None

        invoice = invoices[index]
        normalized = self._normalize_status(status)
        invoice.status = normalized
        if normalized == "paid":
            invoice.paid_date = paid_date or date.today()
        else:
            invoice.paid_date = None

        ok = self.repo.update_invoice(index, invoice)
        return ok, invoice if ok else None

    def mark_invoice_paid(self, index: int, paid_date: date | None = None) -> tuple[bool, Invoice | None]:
        return self.set_invoice_status(index=index, status="paid", paid_date=paid_date)

    def _invoice_is_in_period(self, inv: Invoice, year: int, month: int, basis: str) -> bool:
        basis_key = str(basis or "cash").strip().lower()

        if basis_key == "cash":
            if inv.status != "paid":
                return False
            ref_date = inv.paid_date or inv.issue_date
        else:
            ref_date = inv.issue_date

        return bool(ref_date and ref_date.year == year and ref_date.month == month)

    def monthly_tax_report(
        self,
        year: int,
        month: int,
        currency: str | None = None,
        basis: str | None = None,
    ) -> dict:
        profile = self.repo.get_tax_profile()
        basis_value = str(basis or profile.reporting_basis or "cash").strip().lower()
        if basis_value not in {"cash", "accrual"}:
            basis_value = "cash"

        selected: list[Invoice] = []
        overdue_count = 0
        outstanding_total = 0.0

        for inv in self.repo.list_invoices():
            if currency and inv.currency != currency:
                continue

            if inv.status in {"draft", "sent"}:
                outstanding_total += float(inv.total_amount)
                if inv.due_date and inv.due_date < date.today():
                    overdue_count += 1

            if self._invoice_is_in_period(inv, year, month, basis_value):
                selected.append(inv)

        status_counts: dict[str, int] = defaultdict(int)
        status_totals: dict[str, float] = defaultdict(float)
        rate_group: dict[float, dict] = defaultdict(lambda: {"count": 0, "subtotal": 0.0, "tax": 0.0, "total": 0.0})

        subtotal_total = 0.0
        tax_total = 0.0
        grand_total = 0.0

        for inv in selected:
            status = self._normalize_status(inv.status)
            status_counts[status] += 1
            status_totals[status] += float(inv.total_amount)

            subtotal_total += float(inv.subtotal)
            tax_total += float(inv.tax_amount)
            grand_total += float(inv.total_amount)

            rate_key = float(inv.tax_rate)
            row = rate_group[rate_key]
            row["count"] += 1
            row["subtotal"] += float(inv.subtotal)
            row["tax"] += float(inv.tax_amount)
            row["total"] += float(inv.total_amount)

        effective_rate = (tax_total / subtotal_total * 100.0) if subtotal_total > 0 else 0.0

        rates = []
        for rate in sorted(rate_group.keys()):
            row = rate_group[rate]
            rates.append(
                {
                    "tax_rate": float(rate),
                    "count": int(row["count"]),
                    "subtotal": self._round_money(row["subtotal"], 3),
                    "tax": self._round_money(row["tax"], 3),
                    "total": self._round_money(row["total"], 3),
                }
            )

        period_key = f"{int(year):04d}-{int(month):02d}"

        highlights: list[str] = []
        if grand_total == 0:
            highlights.append("no_invoice_activity")
        if overdue_count > 0:
            highlights.append("has_overdue_invoices")
        if tax_total > 0:
            highlights.append("tax_liability_detected")

        return {
            "period_key": period_key,
            "basis": basis_value,
            "currency_filter": currency or "",
            "profile": profile.to_dict(),
            "counts": {
                "total_invoices": len(selected),
                "draft": int(status_counts.get("draft", 0)),
                "sent": int(status_counts.get("sent", 0)),
                "paid": int(status_counts.get("paid", 0)),
                "cancelled": int(status_counts.get("cancelled", 0)),
                "overdue_open": int(overdue_count),
            },
            "totals": {
                "subtotal": self._round_money(subtotal_total, 3),
                "tax": self._round_money(tax_total, 3),
                "total": self._round_money(grand_total, 3),
                "effective_tax_rate": self._round_money(effective_rate, 4),
                "outstanding_open_total": self._round_money(outstanding_total, 3),
            },
            "status_totals": {k: self._round_money(v, 3) for k, v in status_totals.items()},
            "rates": rates,
            "highlights": highlights,
            "invoices": [inv.to_dict() for inv in selected],
        }

    def monthly_tax_report_from_month_key(
        self,
        month_key: str,
        currency: str | None = None,
        basis: str | None = None,
    ) -> dict:
        parsed = self.parse_month_key(month_key)
        if not parsed:
            today = date.today()
            year, month = today.year, today.month
        else:
            year, month = parsed
        return self.monthly_tax_report(year=year, month=month, currency=currency, basis=basis)
