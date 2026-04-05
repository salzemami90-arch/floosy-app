import os
import sys
import unittest
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.invoice import Invoice
from models.tax_profile import TaxProfile
from services.cash_flow_engine import CashFlowEngine


class _FakeRepo:
    def __init__(self, invoices=None, documents=None):
        self._invoices = invoices or []
        self._documents = documents or []

    def list_invoices(self):
        return list(self._invoices)

    def list_documents(self):
        return list(self._documents)

    def list_transactions(self, month_key):
        return []

    def list_recurring_items(self):
        return []

    def get_tax_profile(self):
        return TaxProfile()


class CashFlowEngineTests(unittest.TestCase):
    def test_cash_flow_90d_separates_actual_projected_and_carry_over(self):
        repo = _FakeRepo(
            invoices=[
                Invoice.from_dict(
                    {
                        "invoice_id": "inv-open",
                        "invoice_number": "INV-OPEN",
                        "issue_date": "2026-02-10",
                        "due_date": "2026-02-18",
                        "total_amount": 300.0,
                        "subtotal": 300.0,
                        "currency": "د.ك",
                        "status": "sent",
                    }
                ),
                Invoice.from_dict(
                    {
                        "invoice_id": "inv-overdue",
                        "invoice_number": "INV-OLD",
                        "issue_date": "2026-01-25",
                        "due_date": "2026-02-05",
                        "total_amount": 200.0,
                        "subtotal": 200.0,
                        "currency": "د.ك",
                        "status": "sent",
                    }
                ),
            ],
            documents=[
                Document.from_dict(
                    {
                        "name": "رخصة",
                        "end_date": "2026-03-01",
                        "fee": 50.0,
                    }
                ),
                Document.from_dict(
                    {
                        "name": "اعتماد توقيع",
                        "end_date": "2026-02-01",
                        "fee": 40.0,
                    }
                ),
            ],
        )
        engine = CashFlowEngine(repo)
        session_state = {
            "transactions": {
                "2026-فبراير": [
                    {"date": "2026-02-08", "type": "دخل", "amount": 740.0, "currency": "د.ك - دينار كويتي", "category": "راتب"},
                    {"date": "2026-02-09", "type": "مصروف", "amount": 60.0, "currency": "د.ك - دينار كويتي", "category": "مشتريات"},
                ],
                "2025-أكتوبر": [
                    {"date": "2025-10-01", "type": "دخل", "amount": 999.0, "currency": "د.ك - دينار كويتي", "category": "قديم"},
                ],
            },
            "recurring": {
                "items": [
                    {"name": "راتب شرق", "type": "دخل", "amount": 500.0, "currency": "د.ك", "day": 15, "active": True, "last_paid_month": ""},
                    {"name": "زين", "type": "مصروف", "amount": 80.0, "currency": "د.ك", "day": 20, "active": True, "last_paid_month": ""},
                ]
            },
        }

        result = engine.cash_flow_90d(
            session_state,
            "د.ك - دينار كويتي",
            as_of=date(2026, 2, 10),
            horizon_days=90,
        )

        self.assertEqual(result["actual_last_90"]["income"], 740.0)
        self.assertEqual(result["actual_last_90"]["expense"], 60.0)
        self.assertEqual(result["actual_last_90"]["net"], 680.0)

        self.assertEqual(result["projected_next_90"]["income"], 1800.0)
        self.assertEqual(result["projected_next_90"]["expense"], 290.0)
        self.assertEqual(result["projected_next_90"]["net"], 1510.0)

        self.assertEqual(result["components"]["recurring_income"], 1500.0)
        self.assertEqual(result["components"]["recurring_expense"], 240.0)
        self.assertEqual(result["components"]["invoice_income"], 300.0)
        self.assertEqual(result["components"]["document_expense"], 50.0)

        self.assertEqual(result["carry_over"]["delayed_income"], 500.0)
        self.assertEqual(result["carry_over"]["overdue_commitments"], 80.0)
        self.assertEqual(result["carry_over"]["recurring_delayed_net"], 420.0)
        self.assertEqual(result["carry_over"]["overdue_open_invoice_total"], 200.0)
        self.assertEqual(result["carry_over"]["overdue_document_fee_total"], 40.0)

    def test_cash_flow_90d_builds_sorted_upcoming_items_and_monthly_projection(self):
        repo = _FakeRepo(
            invoices=[
                Invoice.from_dict(
                    {
                        "invoice_id": "inv-open",
                        "invoice_number": "INV-OPEN",
                        "issue_date": "2026-02-10",
                        "due_date": "2026-02-18",
                        "total_amount": 300.0,
                        "subtotal": 300.0,
                        "currency": "د.ك",
                        "status": "sent",
                    }
                )
            ],
            documents=[
                Document.from_dict(
                    {
                        "name": "رخصة",
                        "end_date": "2026-03-01",
                        "fee": 50.0,
                    }
                )
            ],
        )
        engine = CashFlowEngine(repo)
        session_state = {
            "transactions": {},
            "recurring": {
                "items": [
                    {"name": "راتب شرق", "type": "دخل", "amount": 500.0, "currency": "د.ك", "day": 15, "active": True, "last_paid_month": ""},
                    {"name": "زين", "type": "مصروف", "amount": 80.0, "currency": "د.ك", "day": 20, "active": True, "last_paid_month": ""},
                ]
            },
        }

        result = engine.cash_flow_90d(
            session_state,
            "د.ك",
            as_of=date(2026, 2, 10),
            horizon_days=90,
        )

        upcoming = result["upcoming_items"]
        self.assertTrue(upcoming)
        self.assertEqual(upcoming[0]["due_date_iso"], "2026-02-15")
        self.assertEqual(upcoming[0]["name"], "راتب شرق")

        monthly = result["monthly_projection"]
        self.assertEqual(len(monthly), 3)
        self.assertEqual(monthly[0]["period_key"], "2026-02")
        self.assertEqual(monthly[0]["income"], 800.0)
        self.assertEqual(monthly[0]["expense"], 80.0)
        self.assertEqual(monthly[1]["period_key"], "2026-03")
        self.assertEqual(monthly[1]["expense"], 130.0)


if __name__ == "__main__":
    unittest.main()
