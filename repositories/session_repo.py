from datetime import datetime

import streamlit as st

from config_floosy import arabic_months
from models.document import Document
from models.project import Project
from models.recurring_item import RecurringItem
from models.transaction import Transaction
from models.invoice import Invoice
from models.tax_profile import TaxProfile
from models.tax_tag import TaxTag
from services.expense_tax_service import ExpenseTaxService


class SessionStateRepository:
    """
    Repository over st.session_state only.
    This is read/write storage, but does not touch UI files.
    """

    def __init__(self):
        self._ensure_keys()

    def _ensure_keys(self) -> None:
        st.session_state.setdefault("transactions", {})
        st.session_state.setdefault("recurring", {"items": []})

        st.session_state.setdefault("documents", [])
        legacy_docs = st.session_state.get("mustndaty_documents")
        if isinstance(legacy_docs, list) and not st.session_state["documents"]:
            st.session_state["documents"] = legacy_docs
        st.session_state["mustndaty_documents"] = st.session_state["documents"]

        st.session_state.setdefault("project_data", {})
        st.session_state.setdefault("projects", [])
        st.session_state.setdefault("invoices", [])
        st.session_state.setdefault("tax_profile", {})
        st.session_state.setdefault("tax_tags", [])

    # -------------------- Transactions --------------------
    def list_transactions(self, month_key: str) -> list[Transaction]:
        self._ensure_keys()
        raw_items = st.session_state["transactions"].get(month_key, [])
        normalized_items = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            normalized_items.append(ExpenseTaxService.normalize_transaction(st.session_state, item))
        st.session_state["transactions"][month_key] = normalized_items
        return [Transaction.from_dict(item) for item in normalized_items]

    def add_transaction(self, month_key: str, tx: Transaction) -> None:
        self._ensure_keys()
        st.session_state["transactions"].setdefault(month_key, [])
        tx_payload = ExpenseTaxService.normalize_transaction(st.session_state, tx.to_dict())
        st.session_state["transactions"][month_key].append(tx_payload)

    def update_transaction(self, month_key: str, index: int, tx: Transaction) -> bool:
        self._ensure_keys()
        st.session_state["transactions"].setdefault(month_key, [])
        items = st.session_state["transactions"][month_key]
        if index < 0 or index >= len(items):
            return False
        items[index] = ExpenseTaxService.normalize_transaction(st.session_state, tx.to_dict())
        return True

    def delete_transaction(self, month_key: str, index: int) -> bool:
        self._ensure_keys()
        st.session_state["transactions"].setdefault(month_key, [])
        items = st.session_state["transactions"][month_key]
        if index < 0 or index >= len(items):
            return False
        items.pop(index)
        return True

    # -------------------- Recurring templates --------------------
    def list_recurring_items(self) -> list[RecurringItem]:
        self._ensure_keys()
        raw_items = st.session_state["recurring"].get("items", [])
        return [RecurringItem.from_dict(item) for item in raw_items]

    def add_recurring_item(self, item: RecurringItem) -> None:
        self._ensure_keys()
        st.session_state["recurring"].setdefault("items", [])
        st.session_state["recurring"]["items"].append(item.to_dict())

    def update_recurring_item(self, index: int, item: RecurringItem) -> bool:
        self._ensure_keys()
        st.session_state["recurring"].setdefault("items", [])
        items = st.session_state["recurring"]["items"]
        if index < 0 or index >= len(items):
            return False
        items[index] = item.to_dict()
        return True

    def delete_recurring_item(self, index: int) -> bool:
        self._ensure_keys()
        st.session_state["recurring"].setdefault("items", [])
        items = st.session_state["recurring"]["items"]
        if index < 0 or index >= len(items):
            return False
        items.pop(index)
        return True

    # -------------------- Documents --------------------
    def list_documents(self) -> list[Document]:
        self._ensure_keys()
        raw_docs = st.session_state["documents"]
        return [Document.from_dict(item) for item in raw_docs]

    def add_document(self, doc: Document) -> None:
        self._ensure_keys()
        st.session_state["documents"].append(doc.to_dict())

    def update_document(self, index: int, doc: Document) -> bool:
        self._ensure_keys()
        docs = st.session_state["documents"]
        if index < 0 or index >= len(docs):
            return False
        docs[index] = doc.to_dict()
        return True

    def delete_document(self, index: int) -> bool:
        self._ensure_keys()
        docs = st.session_state["documents"]
        if index < 0 or index >= len(docs):
            return False
        docs.pop(index)
        return True

    # -------------------- Projects --------------------
    @staticmethod
    def _default_month_project_obj() -> dict:
        return {
            "project_name": "",
            "licenses": [],
            "budget_expected_income": 0.0,
            "budget_expected_operating": 0.0,
            "budget_note": "",
            "project_transactions": [],
            "assets": [],
            "projects": {},
            "selected_project": "",
        }

    def _current_project_month_key(self) -> str:
        now = datetime.now()
        return f"{now.year}-{arabic_months[now.month - 1]}"

    def _ensure_project_month(self, month_key: str) -> dict:
        project_data = st.session_state["project_data"]
        month_obj = project_data.setdefault(month_key, self._default_month_project_obj())
        month_obj.setdefault("projects", {})
        month_obj.setdefault("selected_project", "")
        return month_obj

    @staticmethod
    def _sync_project_legacy(month_obj: dict) -> None:
        projects_map = month_obj.get("projects", {})
        selected_name = month_obj.get("selected_project", "")

        selected_obj = projects_map.get(selected_name, {}) if isinstance(projects_map, dict) else {}
        if selected_obj:
            month_obj["project_name"] = selected_name
            month_obj["budget_expected_income"] = float(selected_obj.get("expected_income", 0.0))
            month_obj["budget_expected_operating"] = float(selected_obj.get("expected_expense", 0.0))
            month_obj["budget_note"] = selected_obj.get("note", "")
        else:
            month_obj["project_name"] = ""
            month_obj["budget_expected_income"] = 0.0
            month_obj["budget_expected_operating"] = 0.0
            month_obj["budget_note"] = ""

        all_txs = []
        if isinstance(projects_map, dict):
            for name, project_obj in projects_map.items():
                for tx in project_obj.get("transactions", []):
                    tx_copy = dict(tx)
                    tx_copy.setdefault("project_name", name)
                    all_txs.append(tx_copy)
        month_obj["project_transactions"] = all_txs

    def list_projects(self) -> list[Project]:
        self._ensure_keys()

        project_data = st.session_state.get("project_data", {})
        aggregated: dict[str, dict] = {}

        for _, month_obj in project_data.items():
            projects_map = month_obj.get("projects", {})

            if isinstance(projects_map, dict) and projects_map:
                for name, project_obj in projects_map.items():
                    txs = project_obj.get("transactions", [])
                    income = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "دخل")
                    expense = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "مصروف")
                    current_amount = income - expense
                    target_amount = float(project_obj.get("expected_income", 0.0)) - float(project_obj.get("expected_expense", 0.0))

                    bucket = aggregated.setdefault(
                        name,
                        {
                            "target_amount": 0.0,
                            "current_amount": 0.0,
                            "active": False,
                        },
                    )
                    bucket["current_amount"] += float(current_amount)
                    if abs(float(target_amount)) > abs(float(bucket["target_amount"])):
                        bucket["target_amount"] = float(target_amount)
                    bucket["active"] = bool(bucket["active"] or bool(txs))
            else:
                legacy_name = str(month_obj.get("project_name", "") or "").strip()
                if not legacy_name:
                    continue
                txs = month_obj.get("project_transactions", [])
                income = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "دخل")
                expense = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "مصروف")
                current_amount = income - expense
                target_amount = float(month_obj.get("budget_expected_income", 0.0)) - float(month_obj.get("budget_expected_operating", 0.0))

                bucket = aggregated.setdefault(
                    legacy_name,
                    {
                        "target_amount": 0.0,
                        "current_amount": 0.0,
                        "active": False,
                    },
                )
                bucket["current_amount"] += float(current_amount)
                if abs(float(target_amount)) > abs(float(bucket["target_amount"])):
                    bucket["target_amount"] = float(target_amount)
                bucket["active"] = bool(bucket["active"] or bool(txs))

        if aggregated:
            return [
                Project(
                    name=name,
                    target_amount=float(vals["target_amount"]),
                    current_amount=float(vals["current_amount"]),
                    status="active" if vals["active"] else "planning",
                )
                for name, vals in sorted(aggregated.items(), key=lambda item: item[0].lower())
            ]

        raw_projects = st.session_state["projects"]
        return [Project.from_dict(item) for item in raw_projects]

    def add_project(self, project: Project) -> None:
        self._ensure_keys()
        month_key = self._current_project_month_key()
        month_obj = self._ensure_project_month(month_key)

        project_name = (project.name or "").strip()
        if not project_name:
            return

        projects_map = month_obj.setdefault("projects", {})
        if project_name not in projects_map:
            target = float(project.target_amount)
            projects_map[project_name] = {
                "project_type": "أخرى",
                "expected_income": max(target, 0.0),
                "expected_expense": max(-target, 0.0),
                "note": "",
                "transactions": [],
            }

        if not month_obj.get("selected_project"):
            month_obj["selected_project"] = project_name

        self._sync_project_legacy(month_obj)

    def update_project(self, index: int, project: Project) -> bool:
        self._ensure_keys()
        listed = self.list_projects()
        if index < 0 or index >= len(listed):
            return False

        old_name = listed[index].name
        new_name = (project.name or "").strip() or old_name
        target = float(project.target_amount)

        changed = False
        for _, month_obj in st.session_state["project_data"].items():
            projects_map = month_obj.get("projects", {})
            if not isinstance(projects_map, dict) or old_name not in projects_map:
                continue

            proj_obj = projects_map.pop(old_name)
            key_name = new_name if (new_name == old_name or new_name not in projects_map) else old_name
            projects_map[key_name] = proj_obj

            proj_obj["expected_income"] = max(target, 0.0)
            proj_obj["expected_expense"] = max(-target, 0.0)

            if month_obj.get("selected_project") == old_name:
                month_obj["selected_project"] = key_name

            self._sync_project_legacy(month_obj)
            changed = True

        if changed:
            return True

        projects = st.session_state["projects"]
        if index < 0 or index >= len(projects):
            return False
        projects[index] = project.to_dict()
        return True

    def delete_project(self, index: int) -> bool:
        self._ensure_keys()
        listed = self.list_projects()
        if index < 0 or index >= len(listed):
            return False

        target_name = listed[index].name
        changed = False

        for _, month_obj in st.session_state["project_data"].items():
            projects_map = month_obj.get("projects", {})
            if not isinstance(projects_map, dict) or target_name not in projects_map:
                continue

            projects_map.pop(target_name, None)
            if month_obj.get("selected_project") == target_name:
                month_obj["selected_project"] = next(iter(projects_map.keys()), "")

            self._sync_project_legacy(month_obj)
            changed = True

        if changed:
            return True

        projects = st.session_state["projects"]
        if index < 0 or index >= len(projects):
            return False
        projects.pop(index)
        return True

    # -------------------- Invoices --------------------
    def list_invoices(self) -> list[Invoice]:
        self._ensure_keys()
        raw_items = st.session_state.get("invoices", [])
        return [Invoice.from_dict(item) for item in raw_items if isinstance(item, dict)]

    def add_invoice(self, invoice: Invoice) -> None:
        self._ensure_keys()
        st.session_state.setdefault("invoices", [])
        st.session_state["invoices"].append(invoice.to_dict())

    def update_invoice(self, index: int, invoice: Invoice) -> bool:
        self._ensure_keys()
        items = st.session_state.get("invoices", [])
        if index < 0 or index >= len(items):
            return False
        items[index] = invoice.to_dict()
        return True

    def delete_invoice(self, index: int) -> bool:
        self._ensure_keys()
        items = st.session_state.get("invoices", [])
        if index < 0 or index >= len(items):
            return False
        items.pop(index)
        return True

    # -------------------- Tax profile and tags --------------------
    def get_tax_profile(self) -> TaxProfile:
        self._ensure_keys()
        raw_profile = st.session_state.get("tax_profile", {})
        if not isinstance(raw_profile, dict):
            raw_profile = {}
        return TaxProfile.from_dict(raw_profile)

    def save_tax_profile(self, profile: TaxProfile) -> None:
        self._ensure_keys()
        st.session_state["tax_profile"] = profile.to_dict()

    def list_tax_tags(self) -> list[TaxTag]:
        self._ensure_keys()
        raw_tags = st.session_state.get("tax_tags", [])
        return [TaxTag.from_dict(item) for item in raw_tags if isinstance(item, dict)]

    def add_tax_tag(self, tag: TaxTag) -> None:
        self._ensure_keys()
        st.session_state.setdefault("tax_tags", [])
        st.session_state["tax_tags"].append(tag.to_dict())

    def update_tax_tag(self, index: int, tag: TaxTag) -> bool:
        self._ensure_keys()
        items = st.session_state.get("tax_tags", [])
        if index < 0 or index >= len(items):
            return False
        items[index] = tag.to_dict()
        return True

    def delete_tax_tag(self, index: int) -> bool:
        self._ensure_keys()
        items = st.session_state.get("tax_tags", [])
        if index < 0 or index >= len(items):
            return False
        items.pop(index)
        return True
