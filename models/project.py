from dataclasses import dataclass


@dataclass
class Project:
    name: str
    target_amount: float
    current_amount: float
    status: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "target_amount": float(self.target_amount),
            "current_amount": float(self.current_amount),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            name=str(data.get("name", "")),
            target_amount=float(data.get("target_amount", 0.0)),
            current_amount=float(data.get("current_amount", 0.0)),
            status=str(data.get("status", "active")),
        )

