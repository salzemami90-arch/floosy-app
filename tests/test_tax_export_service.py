import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.tax_export_service import TaxExportService


class TaxExportServiceTests(unittest.TestCase):
    def _sample_report(self):
        return {
            "period_key": "2026-02",
            "basis": "cash",
            "counts": {
                "total_invoices": 2,
                "draft": 0,
                "sent": 1,
                "paid": 1,
                "cancelled": 0,
                "overdue_open": 0,
            },
            "totals": {
                "subtotal": 100.0,
                "tax": 5.0,
                "total": 105.0,
                "effective_tax_rate": 5.0,
                "outstanding_open_total": 50.0,
            },
            "status_totals": {
                "sent": 50.0,
                "paid": 55.0,
            },
            "rates": [
                {"tax_rate": 5.0, "count": 2, "subtotal": 100.0, "tax": 5.0, "total": 105.0},
            ],
            "invoices": [
                {
                    "invoice_number": "INV-202602-0001",
                    "customer_name": "Client A",
                    "linked_project": "Project 1",
                    "status": "paid",
                    "issue_date": "2026-02-10",
                    "due_date": "2026-02-15",
                    "tax_rate": 5.0,
                    "tax_amount": 2.5,
                    "total_amount": 52.5,
                },
                {
                    "invoice_number": "INV-202602-0002",
                    "customer_name": "Client B",
                    "linked_project": "",
                    "status": "sent",
                    "issue_date": "2026-02-11",
                    "due_date": "2026-02-20",
                    "tax_rate": 5.0,
                    "tax_amount": 2.5,
                    "total_amount": 52.5,
                },
            ],
        }

    def test_csv_export_contains_summary_and_invoice_rows(self):
        csv_bytes = TaxExportService.report_to_csv_bytes(self._sample_report(), currency_view="KWD", is_en=True)
        csv_text = csv_bytes.decode("utf-8-sig")
        self.assertIn("Summary", csv_text)
        self.assertIn("Invoices", csv_text)
        self.assertIn("INV-202602-0001", csv_text)

    def test_pdf_export_returns_pdf_bytes(self):
        pdf_bytes = TaxExportService.report_to_pdf_bytes(self._sample_report(), currency_view="KWD", is_en=True)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 500)


if __name__ == "__main__":
    unittest.main()
