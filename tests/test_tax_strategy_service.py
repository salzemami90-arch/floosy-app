import unittest
from datetime import date

from models.tax_profile import TaxProfile
from models.transaction import Transaction
from services.tax_strategy_service import TaxStrategyService


class TaxStrategyServiceTests(unittest.TestCase):
    def test_profile_normalizes_profit_alias_to_net_profit(self):
        profile = TaxProfile.from_dict({"tax_basis_mode": "profit"})
        self.assertEqual(profile.tax_basis_mode, "net_profit")

    def test_estimate_month_tax_uses_invoice_basis_by_default(self):
        profile = TaxProfile(default_tax_rate=5.0, tax_basis_mode="invoice", prices_include_tax=False)
        result = TaxStrategyService.estimate_month_tax(
            profile=profile,
            transactions=[],
            invoice_report={"totals": {"subtotal": 100.0, "tax": 5.0, "total": 105.0}},
            currency="د.ك",
        )

        self.assertEqual(result["basis_mode"], "invoice")
        self.assertAlmostEqual(result["basis_amount"], 100.0, places=3)
        self.assertAlmostEqual(result["estimated_tax"], 5.0, places=3)

    def test_estimate_month_tax_uses_positive_net_profit(self):
        profile = TaxProfile(default_tax_rate=10.0, tax_basis_mode="net_profit")
        txs = [
            Transaction(date=date(2026, 2, 1), tx_type="دخل", amount=500.0, currency="د.ك", category="راتب"),
            Transaction(date=date(2026, 2, 2), tx_type="مصروف", amount=120.0, currency="د.ك", category="إيجار"),
        ]
        result = TaxStrategyService.estimate_month_tax(
            profile=profile,
            transactions=txs,
            invoice_report={"totals": {"subtotal": 0.0, "tax": 0.0, "total": 0.0}},
            currency="د.ك",
        )

        self.assertEqual(result["basis_mode"], "net_profit")
        self.assertAlmostEqual(result["basis_amount"], 380.0, places=3)
        self.assertAlmostEqual(result["estimated_tax"], 38.0, places=3)


if __name__ == "__main__":
    unittest.main()
