from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4


class PurchaseGoalService:
    @staticmethod
    def _parse_date(raw_value, fallback: date | None = None) -> date:
        if isinstance(raw_value, date):
            return raw_value
        if raw_value:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(str(raw_value), fmt).date()
                except ValueError:
                    continue
        return fallback or date.today()

    @staticmethod
    def _to_float(raw_value, fallback: float = 0.0) -> float:
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return float(fallback)

    @staticmethod
    def _months_left(ref_date: date, target_date: date) -> int:
        if target_date < ref_date:
            return 0
        return ((target_date.year - ref_date.year) * 12) + (target_date.month - ref_date.month) + 1

    @classmethod
    def normalize_goal(cls, raw_goal: dict, *, today: date | None = None) -> dict:
        ref_date = today or date.today()
        goal = dict(raw_goal) if isinstance(raw_goal, dict) else {}

        target_amount = max(0.0, cls._to_float(goal.get("target_amount", 0.0)))
        saved_amount = max(0.0, cls._to_float(goal.get("saved_amount", 0.0)))
        start_date = cls._parse_date(goal.get("start_date"), fallback=ref_date)
        target_date = cls._parse_date(goal.get("target_date"), fallback=ref_date)

        return {
            "goal_id": str(goal.get("goal_id", "") or "").strip() or str(uuid4()),
            "name": str(goal.get("name", "") or "").strip(),
            "target_amount": float(target_amount),
            "saved_amount": float(saved_amount),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "target_date": target_date.strftime("%Y-%m-%d"),
            "note": str(goal.get("note", "") or ""),
            "active": bool(goal.get("active", True)),
        }

    @classmethod
    def normalize_goals(cls, raw_goals: list[dict] | None, *, today: date | None = None) -> list[dict]:
        if not isinstance(raw_goals, list):
            return []
        goals = [cls.normalize_goal(item, today=today) for item in raw_goals if isinstance(item, dict)]
        goals.sort(key=lambda item: (item.get("active", True) is False, item.get("target_date", ""), item.get("name", "")))
        return goals

    @classmethod
    def goal_metrics(cls, goal: dict, *, today: date | None = None) -> dict:
        ref_date = today or date.today()
        normalized = cls.normalize_goal(goal, today=ref_date)

        target_amount = float(normalized["target_amount"])
        saved_amount = float(normalized["saved_amount"])
        target_date = cls._parse_date(normalized["target_date"], fallback=ref_date)
        remaining_amount = max(0.0, target_amount - saved_amount)
        months_left = cls._months_left(ref_date, target_date)

        if remaining_amount == 0.0 and target_amount > 0:
            status = "done"
            monthly_needed = 0.0
        elif target_date < ref_date:
            status = "overdue"
            monthly_needed = remaining_amount
        else:
            status = "active"
            monthly_needed = (remaining_amount / months_left) if months_left > 0 else remaining_amount

        progress_pct = (saved_amount / target_amount * 100.0) if target_amount > 0 else 0.0

        return {
            **normalized,
            "remaining_amount": float(remaining_amount),
            "months_left": int(months_left),
            "monthly_needed": float(monthly_needed),
            "progress_pct": float(progress_pct),
            "status": status,
        }

    @classmethod
    def goals_summary(cls, goals: list[dict] | None, *, today: date | None = None) -> dict:
        metrics = [cls.goal_metrics(item, today=today) for item in cls.normalize_goals(goals, today=today)]
        active_goals = [item for item in metrics if item.get("active", True) and item["status"] != "done"]
        completed_goals = [item for item in metrics if item["status"] == "done"]
        overdue_goals = [item for item in metrics if item["status"] == "overdue" and item.get("active", True)]

        return {
            "goals": metrics,
            "active_count": len(active_goals),
            "completed_count": len(completed_goals),
            "overdue_count": len(overdue_goals),
            "total_target": float(sum(item["target_amount"] for item in metrics if item.get("active", True))),
            "total_saved": float(sum(item["saved_amount"] for item in metrics if item.get("active", True))),
            "total_remaining": float(sum(item["remaining_amount"] for item in active_goals)),
            "total_monthly_needed": float(sum(item["monthly_needed"] for item in active_goals)),
        }
