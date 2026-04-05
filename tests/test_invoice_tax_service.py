import unittest

from services.invoice_tax_service import InvoiceTaxService


class InvoiceTaxServiceSmokeTests(unittest.TestCase):
    def test_calculate_totals_when_price_includes_tax_extracts_tax(self):
        totals = InvoiceTaxService.calculate_totals(
            base_amount=100.0,
            tax_rate=5.0,
            prices_include_tax=True,
            decimals=3,
        )

        self.assertAlmostEqual(totals["subtotal"], 95.238, places=3)
        self.assertAlmostEqual(totals["tax_amount"], 4.762, places=3)
        self.assertAlmostEqual(totals["total_amount"], 100.0, places=3)

    def test_calculate_totals_when_price_excludes_tax_adds_tax(self):
        totals = InvoiceTaxService.calculate_totals(
            base_amount=100.0,
            tax_rate=5.0,
            prices_include_tax=False,
            decimals=3,
        )

        self.assertAlmostEqual(totals["subtotal"], 100.0, places=3)
        self.assertAlmostEqual(totals["tax_amount"], 5.0, places=3)
        self.assertAlmostEqual(totals["total_amount"], 105.0, places=3)

    def test_parse_month_key_handles_arabic_month(self):
        parsed = InvoiceTaxService.parse_month_key("2026-فبراير")
        self.assertEqual(parsed, (2026, 2))


if __name__ == "__main__":
    unittest.main()
