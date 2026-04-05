import os
import sys
import unittest
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.purchase_goal_service import PurchaseGoalService


class PurchaseGoalServiceTests(unittest.TestCase):
    def test_goal_metrics_calculates_monthly_needed(self):
        metrics = PurchaseGoalService.goal_metrics(
            {
                "name": "عطور",
                "target_amount": 1000.0,
                "saved_amount": 250.0,
                "target_date": "2026-06-30",
            },
            today=date(2026, 3, 3),
        )

        self.assertEqual(metrics["remaining_amount"], 750.0)
        self.assertEqual(metrics["months_left"], 4)
        self.assertAlmostEqual(metrics["monthly_needed"], 187.5, places=2)
        self.assertEqual(metrics["status"], "active")

    def test_goal_metrics_marks_overdue_when_date_passed(self):
        metrics = PurchaseGoalService.goal_metrics(
            {
                "name": "مكياج",
                "target_amount": 300.0,
                "saved_amount": 50.0,
                "target_date": "2026-02-01",
            },
            today=date(2026, 3, 3),
        )

        self.assertEqual(metrics["status"], "overdue")
        self.assertEqual(metrics["remaining_amount"], 250.0)
        self.assertEqual(metrics["monthly_needed"], 250.0)

    def test_goals_summary_totals_active_and_completed(self):
        summary = PurchaseGoalService.goals_summary(
            [
                {
                    "name": "ملابس",
                    "target_amount": 500.0,
                    "saved_amount": 200.0,
                    "target_date": "2026-05-01",
                    "active": True,
                },
                {
                    "name": "شنطة",
                    "target_amount": 200.0,
                    "saved_amount": 200.0,
                    "target_date": "2026-04-01",
                    "active": True,
                },
            ],
            today=date(2026, 3, 3),
        )

        self.assertEqual(summary["active_count"], 1)
        self.assertEqual(summary["completed_count"], 1)
        self.assertEqual(summary["total_remaining"], 300.0)
        self.assertAlmostEqual(summary["total_monthly_needed"], 100.0, places=2)


if __name__ == "__main__":
    unittest.main()
