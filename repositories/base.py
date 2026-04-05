from typing import Protocol

from models.document import Document
from models.invoice import Invoice
from models.project import Project
from models.recurring_item import RecurringItem
from models.tax_profile import TaxProfile
from models.tax_tag import TaxTag
from models.transaction import Transaction


class FlossyRepository(Protocol):
    # Transactions
    def list_transactions(self, month_key: str) -> list[Transaction]:
        ...

    def add_transaction(self, month_key: str, tx: Transaction) -> None:
        ...

    def update_transaction(self, month_key: str, index: int, tx: Transaction) -> bool:
        ...

    def delete_transaction(self, month_key: str, index: int) -> bool:
        ...

    # Recurring templates
    def list_recurring_items(self) -> list[RecurringItem]:
        ...

    def add_recurring_item(self, item: RecurringItem) -> None:
        ...

    def update_recurring_item(self, index: int, item: RecurringItem) -> bool:
        ...

    def delete_recurring_item(self, index: int) -> bool:
        ...

    # Documents
    def list_documents(self) -> list[Document]:
        ...

    def add_document(self, doc: Document) -> None:
        ...

    def update_document(self, index: int, doc: Document) -> bool:
        ...

    def delete_document(self, index: int) -> bool:
        ...

    # Projects
    def list_projects(self) -> list[Project]:
        ...

    def add_project(self, project: Project) -> None:
        ...

    def update_project(self, index: int, project: Project) -> bool:
        ...

    def delete_project(self, index: int) -> bool:
        ...

    # Invoices
    def list_invoices(self) -> list[Invoice]:
        ...

    def add_invoice(self, invoice: Invoice) -> None:
        ...

    def update_invoice(self, index: int, invoice: Invoice) -> bool:
        ...

    def delete_invoice(self, index: int) -> bool:
        ...

    # Tax profile and tax tags
    def get_tax_profile(self) -> TaxProfile:
        ...

    def save_tax_profile(self, profile: TaxProfile) -> None:
        ...

    def list_tax_tags(self) -> list[TaxTag]:
        ...

    def add_tax_tag(self, tag: TaxTag) -> None:
        ...

    def update_tax_tag(self, index: int, tag: TaxTag) -> bool:
        ...

    def delete_tax_tag(self, index: int) -> bool:
        ...
