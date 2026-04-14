import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.tax_profile import TaxProfile
from services.financial_analyzer import FinancialAnalyzer


class _FakeRepo:
    def list_transactions(self, month_key):
        return []

    def list_invoices(self):
        return []

    def list_documents(self):
        return []

    def get_tax_profile(self):
        return TaxProfile()


class FinancialAnalyzerTests(unittest.TestCase):
    def test_recurring_coverage_matches_currency_symbol_variants(self):
        analyzer = FinancialAnalyzer(_FakeRepo())
        recurring_items = [
            {
                "name": "راتب شرق",
                "type": "دخل",
                "amount": 500.0,
                "currency": "د.ك",
                "active": True,
                "last_paid_month": "",
            }
        ]

        coverage = analyzer.recurring_coverage(
            recurring_items,
            "2026-مارس",
            "د.ك - دينار كويتي",
        )

        self.assertEqual(coverage["expected_income"], 500.0)
        self.assertEqual(coverage["net_coverage"], 500.0)

    def test_dashboard_brief_reads_90_day_projection(self):
        analyzer = FinancialAnalyzer(_FakeRepo())
        session_state = {
            "transactions": {},
            "recurring": {
                "items": [
                    {
                        "name": "إيجار",
                        "type": "مصروف",
                        "amount": 400.0,
                        "currency": "د.ك",
                        "day": 5,
                        "active": True,
                        "last_paid_month": "",
                    }
                ]
            },
            "documents": [],
            "project_data": {},
        }

        brief = analyzer.dashboard_brief(
            session_state,
            "2026-مارس",
            "د.ك - دينار كويتي",
        )

        self.assertEqual(brief["status"], "cash_pressure_90")
        self.assertLess(brief["focus_value"], 0.0)
        self.assertGreaterEqual(brief["support_value"], 0.0)

    def test_dashboard_brief_uses_english_currency_code_in_english_detail(self):
        analyzer = FinancialAnalyzer(_FakeRepo())
        session_state = {
            "transactions": {
                "2026-مارس": [
                    {"type": "دخل", "amount": 150.0, "currency": "د.ك - دينار كويتي", "category": "راتب"}
                ]
            },
            "recurring": {"items": []},
            "documents": [],
            "project_data": {},
        }

        brief = analyzer.dashboard_brief(
            session_state,
            "2026-مارس",
            "د.ك - دينار كويتي",
        )

        self.assertIn("KWD", brief["detail_en"])
        self.assertNotIn("د.ك", brief["detail_en"])

    def test_dashboard_brief_returns_empty_state_when_no_data_exists(self):
        analyzer = FinancialAnalyzer(_FakeRepo())
        session_state = {
            "transactions": {},
            "recurring": {"items": []},
            "documents": [],
            "project_data": {},
            "savings": {},
        }

        brief = analyzer.dashboard_brief(
            session_state,
            "2026-مارس",
            "د.ك - دينار كويتي",
        )

        self.assertEqual(brief["status"], "empty")
        self.assertEqual(brief["focus_value"], 0.0)
        self.assertEqual(brief["support_value"], 0.0)
        self.assertIn("first", brief["message_en"].lower())


if __name__ == "__main__":
    unittest.main()
