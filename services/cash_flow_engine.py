from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta

from models.document import Document
from models.invoice import Invoice
from models.transaction import Transaction
from repositories.base import FlossyRepository
from services.financial_analyzer import ARABIC_MONTHS, FinancialAnalyzer


class CashFlowEngine:
    """
    Read-only 90-day cash flow engine.
    It compares actual recent movement with projected upcoming movement.
    """

    def __init__(self, repo: FlossyRepository):
        self.repo = repo
        self.analyzer = FinancialAnalyzer(repo)

    @staticmethod
    def _round_money(value: float, decimals: int = 3) -> float:
        return round(float(value), decimals)

    @staticmethod
    def _currency_symbol(raw_value: str) -> str:
        value = str(raw_value or "").strip()
        if " - " in value:
            return value.split(" - ", 1)[0].strip()
        return value

    @classmethod
    def _currency_matches(cls, item_currency: str, target_currency: str) -> bool:
        return cls._currency_symbol(item_currency) == cls._currency_symbol(target_currency)

    @staticmethod
    def _month_key_for(ref_date: date) -> str:
        return f"{ref_date.year}-{ARABIC_MONTHS[ref_date.month - 1]}"

    @staticmethod
    def _window_start(end_date: date, days: int) -> date:
        safe_days = max(1, int(days))
        return end_date - timedelta(days=safe_days - 1)

    @staticmethod
    def _forecast_end(start_date: date, days: int) -> date:
        safe_days = max(1, int(days))
        return start_date + timedelta(days=safe_days - 1)

    @staticmethod
    def _month_starts_between(start_date: date, end_date: date) -> list[date]:
        rows: list[date] = []
        current = date(start_date.year, start_date.month, 1)
        final = date(end_date.year, end_date.month, 1)

        while current <= final:
            rows.append(current)
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return rows

    @staticmethod
    def _safe_due_date(year_value: int, month_value: int, due_day: int) -> date:
        day_value = max(1, min(int(due_day or 1), calendar.monthrange(year_value, month_value)[1]))
        return date(year_value, month_value, day_value)

    @staticmethod
    def _entry(
        *,
        due_date: date,
        amount: float,
        entry_type: str,
        source: str,
        name: str,
        status: str = "",
        note: str = "",
    ) -> dict:
        safe_type = "income" if entry_type == "income" else "expense"
        return {
            "due_date": due_date,
            "due_date_iso": due_date.isoformat(),
            "amount": float(amount),
            "type": safe_type,
            "source": str(source or ""),
            "name": str(name or ""),
            "status": str(status or ""),
            "note": str(note or ""),
        }

    @staticmethod
    def _sum_entries(entries: list[dict]) -> dict:
        income = sum(float(item.get("amount", 0.0)) for item in entries if item.get("type") == "income")
        expense = sum(float(item.get("amount", 0.0)) for item in entries if item.get("type") == "expense")
        return {
            "income": float(income),
            "expense": float(expense),
            "net": float(income - expense),
            "count": len(entries),
        }

    def _iter_transactions(self, session_state) -> list[Transaction]:
        rows: list[Transaction] = []
        tx_by_month = session_state.get("transactions", {})
        if not isinstance(tx_by_month, dict):
            return rows

        for raw_items in tx_by_month.values():
            if not isinstance(raw_items, list):
                continue
            for item in raw_items:
                if isinstance(item, dict):
                    rows.append(Transaction.from_dict(item))
        return rows

    def actual_last_days(
        self,
        session_state,
        currency: str,
        *,
        as_of: date | None = None,
        days: int = 90,
    ) -> dict:
        end_date = as_of or date.today()
        start_date = self._window_start(end_date, days)
        matched_entries: list[dict] = []

        for tx in self._iter_transactions(session_state):
            if not self._currency_matches(tx.currency, currency):
                continue
            if not (start_date <= tx.date <= end_date):
                continue
            matched_entries.append(
                self._entry(
                    due_date=tx.date,
                    amount=float(tx.amount),
                    entry_type="income" if tx.tx_type == "دخل" else "expense",
                    source="transaction",
                    name=tx.category or tx.note or "Transaction",
                    note=tx.note,
                )
            )

        totals = self._sum_entries(matched_entries)
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "entries": sorted(matched_entries, key=lambda item: item["due_date"]),
            "income": self._round_money(totals["income"]),
            "expense": self._round_money(totals["expense"]),
            "net": self._round_money(totals["net"]),
            "count": totals["count"],
        }

    def _recurring_projection(
        self,
        session_state,
        currency: str,
        *,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        projected: list[dict] = []

        raw_items = session_state.get("recurring", {}).get("items", [])
        if not isinstance(raw_items, list):
            return projected

        active_items = [item for item in raw_items if isinstance(item, dict) and item.get("active", True)]
        for month_start in self._month_starts_between(start_date, end_date):
            for item in active_items:
                if not self._currency_matches(item.get("currency", ""), currency):
                    continue
                due_date = self._safe_due_date(month_start.year, month_start.month, item.get("day", 1))
                if not (start_date <= due_date <= end_date):
                    continue
                amount = float(item.get("amount", 0.0) or 0.0)
                if amount <= 0:
                    continue
                entry_type = "income" if item.get("type") == "دخل" else "expense"
                projected.append(
                    self._entry(
                        due_date=due_date,
                        amount=amount,
                        entry_type=entry_type,
                        source="recurring",
                        name=str(item.get("name", "") or "Recurring"),
                        status="scheduled",
                    )
                )

        return projected

    def _invoice_projection(
        self,
        currency: str,
        *,
        start_date: date,
        end_date: date,
    ) -> tuple[list[dict], dict]:
        projected: list[dict] = []
        overdue_total = 0.0
        overdue_count = 0

        for invoice in self.repo.list_invoices():
            if not isinstance(invoice, Invoice):
                continue
            if not self._currency_matches(invoice.currency, currency):
                continue
            if invoice.status in {"paid", "cancelled"}:
                continue

            due_date = invoice.due_date or invoice.issue_date
            if due_date < start_date:
                overdue_total += float(invoice.total_amount)
                overdue_count += 1
                continue
            if due_date > end_date:
                continue

            projected.append(
                self._entry(
                    due_date=due_date,
                    amount=float(invoice.total_amount),
                    entry_type="income",
                    source="invoice",
                    name=invoice.invoice_number or invoice.customer_name or "Invoice",
                    status=invoice.status,
                    note=invoice.customer_name,
                )
            )

        return projected, {
            "overdue_open_invoice_total": self._round_money(overdue_total),
            "overdue_open_invoice_count": int(overdue_count),
        }

    def _document_projection(
        self,
        currency: str,
        *,
        start_date: date,
        end_date: date,
    ) -> tuple[list[dict], dict]:
        projected: list[dict] = []
        overdue_total = 0.0
        overdue_count = 0

        for document in self.repo.list_documents():
            if not isinstance(document, Document):
                continue
            fee = float(document.fee or 0.0)
            if fee <= 0:
                continue

            due_date = document.end_date
            if due_date is None:
                continue

            if due_date < start_date:
                overdue_total += fee
                overdue_count += 1
                continue
            if due_date > end_date:
                continue

            projected.append(
                self._entry(
                    due_date=due_date,
                    amount=fee,
                    entry_type="expense",
                    source="document",
                    name=document.name or "Document",
                    status="upcoming",
                    note=document.attachment_name,
                )
            )

        return projected, {
            "overdue_document_fee_total": self._round_money(overdue_total),
            "overdue_document_count": int(overdue_count),
        }

    def _monthly_projection(self, entries: list[dict]) -> list[dict]:
        grouped: dict[str, dict] = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "count": 0, "year": 0, "month": 0})

        for item in entries:
            due = item["due_date"]
            period_key = f"{due.year:04d}-{due.month:02d}"
            bucket = grouped[period_key]
            bucket["year"] = due.year
            bucket["month"] = due.month
            bucket["count"] += 1
            if item.get("type") == "income":
                bucket["income"] += float(item.get("amount", 0.0))
            else:
                bucket["expense"] += float(item.get("amount", 0.0))

        rows = []
        for period_key, bucket in sorted(grouped.items()):
            income = float(bucket["income"])
            expense = float(bucket["expense"])
            rows.append(
                {
                    "period_key": period_key,
                    "year": int(bucket["year"]),
                    "month": int(bucket["month"]),
                    "income": self._round_money(income),
                    "expense": self._round_money(expense),
                    "net": self._round_money(income - expense),
                    "count": int(bucket["count"]),
                }
            )
        return rows

    def cash_flow_90d(
        self,
        session_state,
        currency: str,
        *,
        as_of: date | None = None,
        horizon_days: int = 90,
    ) -> dict:
        ref_date = as_of or date.today()
        forecast_start = ref_date
        forecast_end = self._forecast_end(forecast_start, horizon_days)

        actual = self.actual_last_days(
            session_state,
            currency,
            as_of=ref_date,
            days=horizon_days,
        )

        recurring_entries = self._recurring_projection(
            session_state,
            currency,
            start_date=forecast_start,
            end_date=forecast_end,
        )
        invoice_entries, invoice_meta = self._invoice_projection(
            currency,
            start_date=forecast_start,
            end_date=forecast_end,
        )
        document_entries, document_meta = self._document_projection(
            currency,
            start_date=forecast_start,
            end_date=forecast_end,
        )

        projected_entries = sorted(
            recurring_entries + invoice_entries + document_entries,
            key=lambda item: (item["due_date"], item["type"], item["source"], item["name"]),
        )
        projected_totals = self._sum_entries(projected_entries)

        current_month_key = self._month_key_for(ref_date)
        recurring_items = session_state.get("recurring", {}).get("items", [])
        if not isinstance(recurring_items, list):
            recurring_items = []
        active_items = [
            {
                **item,
                "currency": self._currency_symbol(item.get("currency", "")),
            }
            for item in recurring_items
            if isinstance(item, dict) and item.get("active", True)
        ]
        recurring_carry = self.analyzer.recurring_coverage(
            active_items,
            current_month_key,
            self._currency_symbol(currency),
        )

        comparison = {
            "income_delta": self._round_money(projected_totals["income"] - actual["income"]),
            "expense_delta": self._round_money(projected_totals["expense"] - actual["expense"]),
            "net_delta": self._round_money(projected_totals["net"] - actual["net"]),
        }

        carry_over = {
            "delayed_income": self._round_money(recurring_carry["expected_income"]),
            "overdue_commitments": self._round_money(recurring_carry["overdue_commitments"]),
            "recurring_delayed_net": self._round_money(recurring_carry["net_coverage"]),
            "delayed_income_count": int(recurring_carry["expected_count"]),
            "overdue_commitment_count": int(recurring_carry["overdue_count"]),
            "overdue_open_invoice_total": invoice_meta["overdue_open_invoice_total"],
            "overdue_open_invoice_count": invoice_meta["overdue_open_invoice_count"],
            "overdue_document_fee_total": document_meta["overdue_document_fee_total"],
            "overdue_document_count": document_meta["overdue_document_count"],
        }

        return {
            "as_of": ref_date.isoformat(),
            "forecast_until": forecast_end.isoformat(),
            "currency": self._currency_symbol(currency),
            "actual_last_90": actual,
            "projected_next_90": {
                "start_date": forecast_start.isoformat(),
                "end_date": forecast_end.isoformat(),
                "income": self._round_money(projected_totals["income"]),
                "expense": self._round_money(projected_totals["expense"]),
                "net": self._round_money(projected_totals["net"]),
                "count": projected_totals["count"],
            },
            "components": {
                "recurring_income": self._round_money(
                    sum(item["amount"] for item in recurring_entries if item["type"] == "income")
                ),
                "recurring_expense": self._round_money(
                    sum(item["amount"] for item in recurring_entries if item["type"] == "expense")
                ),
                "invoice_income": self._round_money(
                    sum(item["amount"] for item in invoice_entries if item["type"] == "income")
                ),
                "document_expense": self._round_money(
                    sum(item["amount"] for item in document_entries if item["type"] == "expense")
                ),
            },
            "comparison_vs_last_90": comparison,
            "carry_over": carry_over,
            "monthly_projection": self._monthly_projection(projected_entries),
            "upcoming_items": [
                {
                    **item,
                    "amount": self._round_money(item["amount"]),
                }
                for item in projected_entries[:12]
            ],
        }
