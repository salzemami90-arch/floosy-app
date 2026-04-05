import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.expense_tax_service import ExpenseTaxService


class ExpenseTaxServiceTests(unittest.TestCase):
    def test_expense_options_include_deductible_and_non_deductible(self):
        state = {"tax_tags": []}
        options = ExpenseTaxService.expense_options(state, is_en=False)
        codes = {item["code"] for item in options}
        self.assertIn(ExpenseTaxService.DEDUCTIBLE_CODE, codes)
        self.assertIn(ExpenseTaxService.NON_DEDUCTIBLE_CODE, codes)

    def test_normalize_income_transaction_marks_not_applicable(self):
        state = {"tax_tags": []}
        tx = {"type": "دخل", "amount": 100.0}
        normalized = ExpenseTaxService.normalize_transaction(state, tx)
        self.assertEqual(normalized["tax_classification"], "not_applicable")
        self.assertEqual(normalized["tax_tag_code"], "")
        self.assertFalse(normalized["tax_deductible"])

    def test_normalize_expense_with_selected_tag_keeps_tag(self):
        state = {
            "tax_tags": [
                {
                    "code": "expense_custom_non",
                    "name": "مصاريف شخصية",
                    "kind": "expense",
                    "deductible": False,
                    "tax_applicable": False,
                    "sort_order": 5,
                    "active": True,
                }
            ]
        }
        tx = {"type": "مصروف", "amount": 25.0, "tax_tag_code": "expense_custom_non"}
        normalized = ExpenseTaxService.normalize_transaction(state, tx)
        self.assertEqual(normalized["tax_tag_code"], "expense_custom_non")
        self.assertEqual(normalized["tax_classification"], "non_deductible")
        self.assertFalse(normalized["tax_deductible"])

    def test_normalize_expense_infers_non_deductible_for_personal(self):
        state = {"tax_tags": []}
        tx = {"type": "مصروف", "amount": 7.0, "category": "قهوة"}
        normalized = ExpenseTaxService.normalize_transaction(state, tx)
        self.assertEqual(normalized["tax_classification"], "non_deductible")
        self.assertFalse(normalized["tax_deductible"])

    def test_expense_breakdown_splits_totals(self):
        txs = [
            {"type": "مصروف", "amount": 100.0, "currency": "د.ك - دينار كويتي", "tax_deductible": True},
            {"type": "مصروف", "amount": 40.0, "currency": "د.ك - دينار كويتي", "tax_deductible": False},
            {"type": "دخل", "amount": 300.0, "currency": "د.ك - دينار كويتي", "tax_deductible": False},
        ]
        breakdown = ExpenseTaxService.expense_breakdown(txs, currency="د.ك - دينار كويتي")
        self.assertEqual(breakdown["deductible_amount"], 100.0)
        self.assertEqual(breakdown["non_deductible_amount"], 40.0)
        self.assertEqual(breakdown["total_expense"], 140.0)


if __name__ == "__main__":
    unittest.main()
