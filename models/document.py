from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Document:
    name: str
    issue_date: date | None = None
    end_date: date | None = None
    remind_before_months: int = 1
    renewal_cycle_months: int = 12
    fee: float = 0.0
    attachment_name: str = ""
    attachment_bytes: bytes | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "issue_date": self.issue_date.strftime("%Y-%m-%d") if self.issue_date else "",
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else "",
            "remind_before_months": int(self.remind_before_months),
            "renewal_cycle_months": int(self.renewal_cycle_months),
            "fee": float(self.fee),
            "attachment_name": self.attachment_name,
            "attachment_bytes": self.attachment_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        def _parse_date(raw_value):
            if isinstance(raw_value, date):
                return raw_value
            if not raw_value:
                return None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(str(raw_value), fmt).date()
                except ValueError:
                    continue
            return None

        issue_date = _parse_date(data.get("issue_date"))
        end_date = _parse_date(data.get("end_date") or data.get("renewal_date"))

        fee_raw = data.get("fee", data.get("cost", 0.0))
        try:
            fee = float(fee_raw or 0.0)
        except (TypeError, ValueError):
            fee = 0.0

        remind_raw = data.get("remind_before_months", 1)
        try:
            remind_before_months = int(remind_raw)
        except (TypeError, ValueError):
            remind_before_months = 1

        cycle_raw = data.get("renewal_cycle_months", None)
        if cycle_raw in (None, ""):
            frequency = str(data.get("frequency", "") or "")
            cycle_raw = 48 if "4" in frequency else 12
        try:
            renewal_cycle_months = int(cycle_raw)
        except (TypeError, ValueError):
            renewal_cycle_months = 12

        raw_attachment = data.get("attachment_bytes")
        attachment_bytes = raw_attachment if isinstance(raw_attachment, (bytes, bytearray)) else None

        return cls(
            name=str(data.get("name", "")),
            issue_date=issue_date,
            end_date=end_date,
            remind_before_months=max(0, int(remind_before_months)),
            renewal_cycle_months=max(1, int(renewal_cycle_months)),
            fee=fee,
            attachment_name=str(data.get("attachment_name", "") or ""),
            attachment_bytes=attachment_bytes,
        )
