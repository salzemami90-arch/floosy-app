import unittest
from datetime import date

from models.invoice import Invoice


class InvoiceModelSmokeTests(unittest.TestCase):
    def test_from_dict_normalizes_invalid_tax_source(self):
        inv = Invoice.from_dict(
            {
                "invoice_id": "1",
                "invoice_number": "INV-1",
                "issue_date": "2026-02-22",
                "subtotal": 10,
                "tax_rate": 5,
                "tax_amount": 0.5,
                "total_amount": 10.5,
                "tax_source": "unknown-source",
            }
        )
        self.assertEqual(inv.tax_source, "global")

    def test_from_dict_fallback_issue_date(self):
        inv = Invoice.from_dict(
            {
                "invoice_id": "1",
                "invoice_number": "INV-1",
                "issue_date": "bad-date",
                "subtotal": 1,
                "tax_rate": 0,
                "tax_amount": 0,
                "total_amount": 1,
            }
        )
        self.assertIsInstance(inv.issue_date, date)


if __name__ == "__main__":
    unittest.main()
