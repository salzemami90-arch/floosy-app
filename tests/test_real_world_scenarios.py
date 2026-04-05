import os
import sys
import unittest
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.document import Document
from models.invoice import Invoice
from models.tax_profile import TaxProfile
from services.cash_flow_engine import CashFlowEngine
from services.invoice_tax_service import InvoiceTaxService


class _ScenarioRepo:
    def __init__(self, invoices=None, documents=None, tax_profile=None):
        self._invoices = invoices or []
        self._documents = documents or []
        self._tax_profile = tax_profile or TaxProfile()

    def list_transactions(self, month_key):
        return []

    def list_recurring_items(self):
        return []

    def list_invoices(self):
        return list(self._invoices)

    def list_documents(self):
        return list(self._documents)

    def get_tax_profile(self):
        return self._tax_profile


class RealWorldScenarioTests(unittest.TestCase):
    def test_delayed_salary_and_stacked_commitments_stay_outside_actual(self):
        repo = _ScenarioRepo(
            invoices=[
                Invoice.from_dict(
                    {
                        "invoice_id": "invoice-apr",
                        "invoice_number": "INV-APR-01",
                        "issue_date": "2026-04-10",
                        "due_date": "2026-04-18",
                        "subtotal": 1200.0,
                        "tax_amount": 0.0,
                        "total_amount": 1200.0,
                        "currency": "د.ك",
                        "status": "sent",
                    }
                )
            ],
            documents=[
                Document.from_dict(
                    {
                        "name": "رخصة تجارية",
                        "end_date": "2026-05-01",
                        "fee": 50.0,
                    }
                )
            ],
        )
        engine = CashFlowEngine(repo)
        session_state = {
            "transactions": {
                "2026-أبريل": [
                    {"date": "2026-04-02", "type": "دخل", "amount": 740.0, "currency": "د.ك - دينار كويتي", "category": "راتب"},
                    {"date": "2026-04-03", "type": "مصروف", "amount": 20.0, "currency": "د.ك - دينار كويتي", "category": "بقالة"},
                ]
            },
            "recurring": {
                "items": [
                    {
                        "name": "راتب شرق",
                        "type": "دخل",
                        "amount": 500.0,
                        "currency": "د.ك",
                        "day": 15,
                        "active": True,
                        "pending_entitlements": ["2026-فبراير", "2026-مارس"],
                    },
                    {
                        "name": "إيجار",
                        "type": "مصروف",
                        "amount": 300.0,
                        "currency": "د.ك",
                        "day": 1,
                        "active": True,
                        "pending_entitlements": ["2026-مارس", "2026-أبريل"],
                    },
                    {
                        "name": "تأمينات",
                        "type": "مصروف",
                        "amount": 75.0,
                        "currency": "د.ك",
                        "day": 5,
                        "active": True,
                        "pending_entitlements": ["2026-مارس"],
                    },
                    {
                        "name": "زين",
                        "type": "مصروف",
                        "amount": 80.0,
                        "currency": "د.ك",
                        "day": 20,
                        "active": True,
                        "pending_entitlements": ["2026-أبريل"],
                    },
                ]
            },
        }

        result = engine.cash_flow_90d(
            session_state,
            "د.ك - دينار كويتي",
            as_of=date(2026, 4, 10),
            horizon_days=90,
        )

        self.assertEqual(result["actual_last_90"]["income"], 740.0)
        self.assertEqual(result["actual_last_90"]["expense"], 20.0)
        self.assertEqual(result["actual_last_90"]["net"], 720.0)

        self.assertEqual(result["carry_over"]["delayed_income"], 1000.0)
        self.assertEqual(result["carry_over"]["overdue_commitments"], 755.0)
        self.assertEqual(result["carry_over"]["recurring_delayed_net"], 245.0)

        self.assertEqual(result["components"]["invoice_income"], 1200.0)
        self.assertEqual(result["components"]["document_expense"], 50.0)
        self.assertEqual(result["projected_next_90"]["income"], 2700.0)
        self.assertEqual(result["projected_next_90"]["expense"], 1415.0)
        self.assertEqual(result["projected_next_90"]["net"], 1285.0)

    def test_projection_breakdown_spans_four_calendar_months_cleanly(self):
        repo = _ScenarioRepo(
            invoices=[
                Invoice.from_dict(
                    {
                        "invoice_id": "invoice-apr",
                        "invoice_number": "INV-APR-01",
                        "issue_date": "2026-04-10",
                        "due_date": "2026-04-18",
                        "subtotal": 1200.0,
                        "tax_amount": 0.0,
                        "total_amount": 1200.0,
                        "currency": "د.ك",
                        "status": "sent",
                    }
                )
            ],
            documents=[
                Document.from_dict(
                    {
                        "name": "رخصة تجارية",
                        "end_date": "2026-05-01",
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
                    {"name": "راتب شرق", "type": "دخل", "amount": 500.0, "currency": "د.ك", "day": 15, "active": True},
                    {"name": "إيجار", "type": "مصروف", "amount": 300.0, "currency": "د.ك", "day": 1, "active": True},
                    {"name": "تأمينات", "type": "مصروف", "amount": 75.0, "currency": "د.ك", "day": 5, "active": True},
                    {"name": "زين", "type": "مصروف", "amount": 80.0, "currency": "د.ك", "day": 20, "active": True},
                ]
            },
        }

        result = engine.cash_flow_90d(
            session_state,
            "د.ك",
            as_of=date(2026, 4, 10),
            horizon_days=90,
        )

        monthly = result["monthly_projection"]
        self.assertEqual([row["period_key"] for row in monthly], ["2026-04", "2026-05", "2026-06", "2026-07"])
        self.assertEqual(monthly[0]["income"], 1700.0)
        self.assertEqual(monthly[0]["expense"], 80.0)
        self.assertEqual(monthly[1]["income"], 500.0)
        self.assertEqual(monthly[1]["expense"], 505.0)
        self.assertEqual(monthly[3]["net"], -375.0)

    def test_invoice_reporting_changes_between_cash_and_accrual_basis(self):
        repo = _ScenarioRepo(
            invoices=[
                Invoice.from_dict(
                    {
                        "invoice_id": "apr-paid-may",
                        "invoice_number": "INV-APR-PAID-MAY",
                        "issue_date": "2026-04-01",
                        "due_date": "2026-04-10",
                        "paid_date": "2026-05-02",
                        "status": "paid",
                        "subtotal": 500.0,
                        "tax_rate": 5.0,
                        "tax_amount": 25.0,
                        "total_amount": 525.0,
                        "currency": "د.ك",
                    }
                ),
                Invoice.from_dict(
                    {
                        "invoice_id": "apr-open",
                        "invoice_number": "INV-APR-OPEN",
                        "issue_date": "2026-04-12",
                        "due_date": "2026-04-20",
                        "status": "sent",
                        "subtotal": 200.0,
                        "tax_rate": 5.0,
                        "tax_amount": 10.0,
                        "total_amount": 210.0,
                        "currency": "د.ك",
                    }
                ),
                Invoice.from_dict(
                    {
                        "invoice_id": "mar-paid-apr",
                        "invoice_number": "INV-MAR-PAID-APR",
                        "issue_date": "2026-03-25",
                        "due_date": "2026-04-05",
                        "paid_date": "2026-04-05",
                        "status": "paid",
                        "subtotal": 100.0,
                        "tax_rate": 5.0,
                        "tax_amount": 5.0,
                        "total_amount": 105.0,
                        "currency": "د.ك",
                    }
                ),
            ],
            tax_profile=TaxProfile(default_tax_rate=5.0, reporting_basis="cash"),
        )
        service = InvoiceTaxService(repo)

        cash_report = service.monthly_tax_report(year=2026, month=4, currency="د.ك", basis="cash")
        accrual_report = service.monthly_tax_report(year=2026, month=4, currency="د.ك", basis="accrual")

        self.assertEqual(cash_report["counts"]["total_invoices"], 1)
        self.assertEqual(cash_report["totals"]["total"], 105.0)
        self.assertEqual(cash_report["counts"]["paid"], 1)

        self.assertEqual(accrual_report["counts"]["total_invoices"], 2)
        self.assertEqual(accrual_report["totals"]["total"], 735.0)
        self.assertEqual(accrual_report["counts"]["sent"], 1)
        self.assertEqual(accrual_report["counts"]["paid"], 1)
        self.assertEqual(accrual_report["totals"]["outstanding_open_total"], 210.0)


if __name__ == "__main__":
    unittest.main()
