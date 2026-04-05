from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Transaction:
    """
    الشكل الموحد للمعاملة المالية داخل التطبيق.
    ملاحظة: هذا الموديل لا يغير الواجهة الحالية، فقط ينظم البيانات.
    """

    date: date
    tx_type: str
    amount: float
    currency: str
    category: str
    note: str = ""

    def to_dict(self) -> dict:
        """تحويل الموديل إلى dict بنفس الحقول الحالية في session_state."""
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "type": self.tx_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "category": self.category,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """إنشاء Transaction من dict موجود حالياً."""
        raw_date = data.get("date")
        if isinstance(raw_date, date):
            parsed_date = raw_date
        else:
            try:
                parsed_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
            except (TypeError, ValueError):
                parsed_date = date.today()

        raw_note = data.get("note", "")
        note = "" if raw_note is None else str(raw_note)

        return cls(
            date=parsed_date,
            tx_type=str(data.get("type", "")),
            amount=float(data.get("amount", 0.0)),
            currency=str(data.get("currency", "")),
            category=str(data.get("category", "")),
            note=note,
        )
