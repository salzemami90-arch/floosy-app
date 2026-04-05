from dataclasses import dataclass


@dataclass
class RecurringItem:
    name: str
    tx_type: str
    amount: float
    currency: str
    due_day: int
    active: bool = True
    last_paid_month: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.tx_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "day": int(self.due_day),
            "active": bool(self.active),
            "last_paid_month": self.last_paid_month,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringItem":
        due_day = data.get("day", data.get("due_day", 1))
        try:
            day_int = int(due_day)
        except (TypeError, ValueError):
            day_int = 1
        day_int = max(1, min(31, day_int))

        return cls(
            name=str(data.get("name", "")),
            tx_type=str(data.get("type", data.get("tx_type", "مصروف"))),
            amount=float(data.get("amount", 0.0)),
            currency=str(data.get("currency", "")),
            due_day=day_int,
            active=bool(data.get("active", True)),
            last_paid_month=str(data.get("last_paid_month", "")),
        )

