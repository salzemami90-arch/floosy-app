from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime

from repositories.base import FlossyRepository

ARABIC_MONTHS = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]


class FinancialAnalyzer:
    """
    Read-only analysis service.
    It never writes to storage; it only reads session/repository data and computes metrics.
    """

    def __init__(self, repo: FlossyRepository):
        self.repo = repo

    # -------- Transactions (repository-based) --------
    def monthly_totals(self, month_key: str) -> dict:
        txs = self.repo.list_transactions(month_key)
        income = sum(tx.amount for tx in txs if tx.tx_type == "دخل")
        expense = sum(tx.amount for tx in txs if tx.tx_type == "مصروف")
        return {
            "month_key": month_key,
            "income": float(income),
            "expense": float(expense),
            "net": float(income - expense),
            "count": len(txs),
        }

    def multi_month_totals(self, month_keys: list[str]) -> dict:
        total_income = 0.0
        total_expense = 0.0
        total_count = 0

        for month_key in month_keys:
            monthly = self.monthly_totals(month_key)
            total_income += monthly["income"]
            total_expense += monthly["expense"]
            total_count += monthly["count"]

        return {
            "months": month_keys,
            "income": float(total_income),
            "expense": float(total_expense),
            "net": float(total_income - total_expense),
            "count": total_count,
        }

    def category_breakdown(self, month_key: str, tx_type: str | None = None) -> list[dict]:
        txs = self.repo.list_transactions(month_key)
        grouped: dict[str, float] = defaultdict(float)

        for tx in txs:
            if tx_type and tx.tx_type != tx_type:
                continue
            grouped[tx.category] += tx.amount

        rows = [{"category": c, "amount": float(a)} for c, a in grouped.items()]
        rows.sort(key=lambda row: row["amount"], reverse=True)
        return rows

    def type_breakdown(self, month_key: str) -> dict:
        txs = self.repo.list_transactions(month_key)
        grouped: dict[str, float] = defaultdict(float)
        for tx in txs:
            grouped[tx.tx_type] += tx.amount
        return {k: float(v) for k, v in grouped.items()}

    # -------- Raw/session helpers (read-only) --------
    @staticmethod
    def _currency_symbol(raw_value: str) -> str:
        value = str(raw_value or "").strip()
        if " - " in value:
            return value.split(" - ", 1)[0].strip()
        return value

    @classmethod
    def _currency_display(cls, raw_value: str, is_en: bool = False) -> str:
        symbol = cls._currency_symbol(raw_value)
        if not is_en:
            return symbol
        return {
            "د.ك": "KWD",
            "ر.س": "SAR",
            "د.إ": "AED",
            "$": "USD",
            "€": "EUR",
        }.get(symbol, symbol)

    @classmethod
    def _currency_matches(cls, item_currency: str, target_currency: str) -> bool:
        return cls._currency_symbol(item_currency) == cls._currency_symbol(target_currency)

    @staticmethod
    def totals_by_currency(tx_list: list[dict], currency: str) -> dict:
        filtered = [
            tx
            for tx in tx_list
            if FinancialAnalyzer._currency_matches(tx.get("currency", ""), currency)
        ]
        income = sum(float(tx.get("amount", 0.0)) for tx in filtered if tx.get("type") == "دخل")
        expense = sum(float(tx.get("amount", 0.0)) for tx in filtered if tx.get("type") == "مصروف")
        return {
            "income": float(income),
            "expense": float(expense),
            "net": float(income - expense),
            "count": len(filtered),
        }

    @staticmethod
    def compare_totals(current: dict, previous: dict) -> dict:
        def _safe_percent(delta: float, base_value: float) -> float:
            if base_value == 0:
                return 0.0
            return (delta / base_value) * 100.0

        income_delta = float(current.get("income", 0.0) - previous.get("income", 0.0))
        expense_delta = float(current.get("expense", 0.0) - previous.get("expense", 0.0))
        net_delta = float(current.get("net", 0.0) - previous.get("net", 0.0))

        return {
            "income_delta": income_delta,
            "expense_delta": expense_delta,
            "net_delta": net_delta,
            "income_delta_pct": _safe_percent(income_delta, float(previous.get("income", 0.0))),
            "expense_delta_pct": _safe_percent(expense_delta, float(previous.get("expense", 0.0))),
            "net_delta_pct": _safe_percent(net_delta, float(previous.get("net", 0.0))),
        }

    @staticmethod
    def _parse_month_key(month_key: str) -> tuple[int, int] | None:
        if not month_key or "-" not in month_key:
            return None
        year_txt, month_name = month_key.split("-", 1)
        if month_name not in ARABIC_MONTHS:
            return None
        try:
            return int(year_txt), ARABIC_MONTHS.index(month_name) + 1
        except ValueError:
            return None

    def _months_diff(self, from_key: str, to_key: str) -> int:
        start = self._parse_month_key(from_key)
        end = self._parse_month_key(to_key)
        if not start or not end:
            return 0
        sy, sm = start
        ey, em = end
        return (ey - sy) * 12 + (em - sm)

    def recurring_coverage(self, recurring_items: list[dict], month_key: str, currency: str) -> dict:
        overdue_commitments = 0.0
        expected_income = 0.0
        overdue_count = 0
        expected_count = 0
        overdue_pending_months = 0
        expected_pending_months = 0

        for item in recurring_items:
            if not item.get("active", True):
                continue
            if not self._currency_matches(item.get("currency", ""), currency):
                continue

            amount = float(item.get("amount", 0.0))
            if amount <= 0:
                continue

            pending_months = item.get("pending_entitlements", [])
            if not isinstance(pending_months, list):
                pending_months = []
            valid_pending_months = [mk for mk in pending_months if isinstance(mk, str) and mk]
            pending_count = len(valid_pending_months)

            # Fallback for legacy data that does not store pending_entitlements.
            if pending_count == 0:
                last_paid = str(item.get("last_paid_month", "") or "")
                if last_paid == month_key:
                    continue

                pending_count = self._months_diff(last_paid, month_key) if last_paid else 1
                pending_count = max(1, pending_count)

            pending_amount = amount * pending_count

            if item.get("type") == "دخل":
                expected_income += pending_amount
                expected_count += 1
                expected_pending_months += pending_count
            elif item.get("type") == "مصروف":
                overdue_commitments += pending_amount
                overdue_count += 1
                overdue_pending_months += pending_count

        return {
            "overdue_commitments": float(overdue_commitments),
            "expected_income": float(expected_income),
            "net_coverage": float(expected_income - overdue_commitments),
            "overdue_count": overdue_count,
            "expected_count": expected_count,
            "overdue_pending_months": int(overdue_pending_months),
            "expected_pending_months": int(expected_pending_months),
        }


    @staticmethod
    def savings_summary(session_state, month_key: str) -> dict:
        savings = session_state.get("savings", {})
        month_obj = savings.get(month_key, {})
        txs = month_obj.get("transactions", [])

        month_in = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "إيداع")
        month_out = sum(float(t.get("amount", 0.0)) for t in txs if t.get("type") == "سحب")
        month_goal = float(month_obj.get("goal", 0.0))

        total_in = 0.0
        total_out = 0.0
        total_count = 0
        for _, s in savings.items():
            stxs = s.get("transactions", [])
            total_count += len(stxs)
            total_in += sum(float(t.get("amount", 0.0)) for t in stxs if t.get("type") == "إيداع")
            total_out += sum(float(t.get("amount", 0.0)) for t in stxs if t.get("type") == "سحب")

        month_net = month_in - month_out
        progress_pct = (month_net / month_goal * 100.0) if month_goal > 0 else 0.0

        return {
            "month_in": float(month_in),
            "month_out": float(month_out),
            "month_net": float(month_net),
            "month_goal": float(month_goal),
            "month_progress_pct": float(progress_pct),
            "all_in": float(total_in),
            "all_out": float(total_out),
            "all_net": float(total_in - total_out),
            "all_count": total_count,
        }

    @staticmethod
    def projects_summary(session_state, month_key: str) -> dict:
        project_data = session_state.get("project_data", {})

        def _collect_month_transactions(month_obj: dict) -> list[dict]:
            projects_map = month_obj.get("projects", {}) if isinstance(month_obj, dict) else {}
            if isinstance(projects_map, dict) and projects_map:
                txs: list[dict] = []
                for project_name, project_obj in projects_map.items():
                    for tx in project_obj.get("transactions", []):
                        tx_copy = dict(tx)
                        tx_copy.setdefault("project_name", project_name)
                        txs.append(tx_copy)
                return txs
            return list(month_obj.get("project_transactions", [])) if isinstance(month_obj, dict) else []

        month_txs = _collect_month_transactions(project_data.get(month_key, {}))
        month_income = sum(float(t.get("amount", 0.0)) for t in month_txs if t.get("type") == "دخل")
        month_expense = sum(float(t.get("amount", 0.0)) for t in month_txs if t.get("type") == "مصروف")

        all_income = 0.0
        all_expense = 0.0
        all_count = 0
        active_months = 0

        for _, month_obj in project_data.items():
            p_txs = _collect_month_transactions(month_obj)
            if p_txs:
                active_months += 1
            all_count += len(p_txs)
            all_income += sum(float(t.get("amount", 0.0)) for t in p_txs if t.get("type") == "دخل")
            all_expense += sum(float(t.get("amount", 0.0)) for t in p_txs if t.get("type") == "مصروف")

        return {
            "month_income": float(month_income),
            "month_expense": float(month_expense),
            "month_net": float(month_income - month_expense),
            "all_income": float(all_income),
            "all_expense": float(all_expense),
            "all_net": float(all_income - all_expense),
            "all_count": all_count,
            "active_months": active_months,
        }


    @staticmethod
    def documents_summary(session_state, today: date | None = None) -> dict:
        docs = session_state.get("documents")
        if docs is None:
            docs = session_state.get("mustndaty_documents", [])

        ref_date = today or date.today()
        upcoming_30 = 0
        upcoming_90 = 0
        expired = 0
        annual_fees_estimate = 0.0

        for doc in docs:
            fee_raw = doc.get("fee", doc.get("cost", 0.0))
            fee = float(fee_raw or 0.0)

            cycle_raw = doc.get("renewal_cycle_months", None)
            if cycle_raw in (None, ""):
                frequency = str(doc.get("frequency", "") or "")
                cycle_raw = 48 if "4" in frequency else 12

            try:
                cycle = int(cycle_raw or 12)
            except (TypeError, ValueError):
                cycle = 12
            cycle = max(1, cycle)
            annual_fees_estimate += fee * (12.0 / cycle)

            end_txt = str(doc.get("end_date") or doc.get("renewal_date") or "")
            end_dt = None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    end_dt = datetime.strptime(end_txt, fmt).date()
                    break
                except ValueError:
                    continue

            if end_dt is None:
                continue

            days_left = (end_dt - ref_date).days
            if days_left < 0:
                expired += 1
            if 0 <= days_left <= 30:
                upcoming_30 += 1
            if 0 <= days_left <= 90:
                upcoming_90 += 1

        return {
            "count": len(docs),
            "expired_count": expired,
            "upcoming_30_count": upcoming_30,
            "upcoming_90_count": upcoming_90,
            "annual_fees_estimate": float(annual_fees_estimate),
        }


    def seasonal_expense_summary(self, session_state, currency: str, limit_months: int = 6) -> dict:
        tx_by_month = session_state.get("transactions", {})

        monthly_rows = []
        for mk, txs in tx_by_month.items():
            parsed = self._parse_month_key(mk)
            if not parsed:
                continue
            year, month_idx = parsed
            expense = sum(
                float(tx.get("amount", 0.0))
                for tx in txs
                if tx.get("currency") == currency and tx.get("type") == "مصروف"
            )
            monthly_rows.append({
                "month_key": mk,
                "year": year,
                "month_idx": month_idx,
                "expense": float(expense),
            })

        monthly_rows.sort(key=lambda r: (r["year"], r["month_idx"]))
        if limit_months > 0:
            monthly_rows = monthly_rows[-limit_months:]

        if not monthly_rows:
            return {
                "months": [],
                "history_month_count": 0,
                "comparison_ready": False,
                "current_expense": 0.0,
                "average_expense": 0.0,
                "delta_from_avg": 0.0,
                "delta_pct": 0.0,
                "peak_month": "",
                "peak_expense": 0.0,
                "status": "normal",
            }

        current = monthly_rows[-1]["expense"]
        history_expenses = [r["expense"] for r in monthly_rows[:-1] if r["expense"] > 0]
        comparison_ready = len(history_expenses) >= 2
        average = sum(history_expenses) / len(history_expenses) if history_expenses else 0.0
        delta = current - average
        delta_pct = (delta / average * 100.0) if average > 0 else 0.0

        peak = max(monthly_rows, key=lambda r: r["expense"])
        status = "normal"
        if comparison_ready and average > 0 and delta_pct >= 15:
            status = "high"
        elif comparison_ready and average > 0 and delta_pct <= -15:
            status = "low"

        return {
            "months": monthly_rows,
            "history_month_count": len(history_expenses),
            "comparison_ready": bool(comparison_ready),
            "current_expense": float(current),
            "average_expense": float(average),
            "delta_from_avg": float(delta),
            "delta_pct": float(delta_pct),
            "peak_month": str(peak["month_key"]),
            "peak_expense": float(peak["expense"]),
            "status": status,
        }

    @staticmethod
    def _merchant_keyword_from_note(note: str) -> str:
        stopwords = {
            "paid", "payment", "spent", "buy", "bought", "for", "from", "the", "and", "at",
            "order", "online", "cash", "card", "note", "expense", "purchase",
            "دفعت", "دفع", "صرف", "مصروف", "شراء", "اشتريت", "طلب", "اونلاين",
            "أونلاين", "من", "في", "على", "عن", "حق", "هذا", "هذه",
        }
        for token in re.findall(r"[\w\u0600-\u06FF]+", str(note or "")):
            key = token.casefold().strip()
            if len(key) < 3 or key.isdigit() or key in stopwords:
                continue
            return token.strip()
        return ""

    def merchant_note_signal(self, session_state, month_key: str, currency: str) -> dict:
        txs = session_state.get("transactions", {}).get(month_key, [])
        grouped: dict[str, dict] = defaultdict(lambda: {"label": "", "amount": 0.0, "count": 0})
        total_expense = 0.0
        expense_count = 0

        for tx in txs:
            if tx.get("currency") != currency or tx.get("type") != "مصروف":
                continue
            amount = float(tx.get("amount", 0.0))
            total_expense += amount
            expense_count += 1
            keyword = self._merchant_keyword_from_note(str(tx.get("note", "") or ""))
            if not keyword:
                continue
            key = keyword.casefold()
            grouped[key]["label"] = grouped[key]["label"] or keyword
            grouped[key]["amount"] += amount
            grouped[key]["count"] += 1

        if not grouped:
            return {
                "status": "normal",
                "label": "",
                "amount": 0.0,
                "count": 0,
                "share": 0.0,
            }

        top = max(grouped.values(), key=lambda item: (float(item["amount"]), int(item["count"])))
        share = (float(top["amount"]) / total_expense) if total_expense > 0 else 0.0
        is_signal = int(top["count"]) >= 2 or (expense_count >= 2 and share >= 0.35)

        return {
            "status": "highlight" if is_signal else "normal",
            "label": str(top["label"]),
            "amount": float(top["amount"]),
            "count": int(top["count"]),
            "share": float(share),
        }

    def seasonal_category_signal(self, session_state, month_key: str, currency: str, history_months: int = 6) -> dict:
        tx_by_month = session_state.get("transactions", {})
        current_txs = tx_by_month.get(month_key, [])

        current_by_cat: dict[str, float] = defaultdict(float)
        for tx in current_txs:
            if tx.get("currency") != currency or tx.get("type") != "مصروف":
                continue
            current_by_cat[str(tx.get("category", "أخرى"))] += float(tx.get("amount", 0.0))

        if not current_by_cat:
            return {
                "top_category": "",
                "current_amount": 0.0,
                "avg_amount": 0.0,
                "delta_pct": 0.0,
                "status": "normal",
            }

        top_category = max(current_by_cat, key=current_by_cat.get)
        current_amount = float(current_by_cat[top_category])

        parsed_current = self._parse_month_key(month_key)
        if not parsed_current:
            return {
                "top_category": top_category,
                "current_amount": current_amount,
                "avg_amount": 0.0,
                "delta_pct": 0.0,
                "status": "normal",
            }

        month_rows = []
        for mk in tx_by_month.keys():
            parsed = self._parse_month_key(mk)
            if not parsed or mk == month_key:
                continue
            month_rows.append((parsed[0], parsed[1], mk))
        month_rows.sort()
        history_keys = [mk for _, _, mk in month_rows][-history_months:]

        history_amounts = []
        for mk in history_keys:
            amount = 0.0
            for tx in tx_by_month.get(mk, []):
                if tx.get("currency") != currency or tx.get("type") != "مصروف":
                    continue
                if str(tx.get("category", "أخرى")) == top_category:
                    amount += float(tx.get("amount", 0.0))
            history_amounts.append(float(amount))

        avg_amount = (sum(history_amounts) / len(history_amounts)) if history_amounts else 0.0
        delta_pct = ((current_amount - avg_amount) / avg_amount * 100.0) if avg_amount > 0 else 0.0

        status = "normal"
        if avg_amount > 0 and delta_pct >= 20:
            status = "high"
        elif avg_amount > 0 and delta_pct <= -20:
            status = "low"

        return {
            "top_category": top_category,
            "current_amount": float(current_amount),
            "avg_amount": float(avg_amount),
            "delta_pct": float(delta_pct),
            "status": status,
        }

    def project_impact_on_personal(self, session_state, month_key: str, currency: str) -> dict:
        personal_month_txs = session_state.get("transactions", {}).get(month_key, [])
        personal_income = sum(
            float(tx.get("amount", 0.0))
            for tx in personal_month_txs
            if tx.get("currency") == currency and tx.get("type") == "دخل"
        )
        personal_expense = sum(
            float(tx.get("amount", 0.0))
            for tx in personal_month_txs
            if tx.get("currency") == currency and tx.get("type") == "مصروف"
        )
        personal_net = personal_income - personal_expense

        projects = self.projects_summary(session_state, month_key)
        project_deficit_this_month = max(0.0, -projects["month_net"])

        # Approximation: deficit in project cashflow is the amount likely funded from personal account.
        estimated_personal_support = project_deficit_this_month
        personal_net_after_support = personal_net - estimated_personal_support

        project_data = session_state.get("project_data", {})
        month_rows = []
        for mk in project_data.keys():
            parsed = self._parse_month_key(mk)
            if not parsed:
                continue
            month_rows.append((parsed[0], parsed[1], mk))
        month_rows.sort()

        recent_keys = [mk for _, _, mk in month_rows][-3:]
        last_3m_deficit = 0.0
        deficit_months = 0
        for mk in recent_keys:
            p = self.projects_summary(session_state, mk)
            d = max(0.0, -p["month_net"])
            if d > 0:
                deficit_months += 1
            last_3m_deficit += d

        return {
            "personal_net": float(personal_net),
            "project_deficit_this_month": float(project_deficit_this_month),
            "estimated_personal_support": float(estimated_personal_support),
            "personal_net_after_support": float(personal_net_after_support),
            "last_3m_project_deficit": float(last_3m_deficit),
            "deficit_months_in_last_3": int(deficit_months),
        }

    def dashboard_brief(self, session_state, month_key: str, currency: str) -> dict:
        from services.cash_flow_engine import CashFlowEngine

        recurring_items = session_state.get("recurring", {}).get("items", [])
        active_items = [item for item in recurring_items if item.get("active", True)]
        coverage = self.recurring_coverage(active_items, month_key, currency)
        seasonal = self.seasonal_expense_summary(session_state, currency, limit_months=6)
        merchant_signal = self.merchant_note_signal(session_state, month_key, currency)
        savings = self.savings_summary(session_state, month_key)
        projects = self.projects_summary(session_state, month_key)
        project_impact = self.project_impact_on_personal(session_state, month_key, currency)
        docs = self.documents_summary(session_state)
        cash_flow = CashFlowEngine(self.repo).cash_flow_90d(session_state, currency)
        projected_90 = cash_flow["projected_next_90"]
        carry_over = cash_flow["carry_over"]
        comparison_90 = cash_flow["comparison_vs_last_90"]
        currency_symbol_ar = self._currency_display(currency, is_en=False)
        currency_symbol_en = self._currency_display(currency, is_en=True)
        follow_up_total = (
            float(carry_over["overdue_commitments"])
            + float(carry_over["overdue_open_invoice_total"])
            + float(carry_over["overdue_document_fee_total"])
        )

        status = "stable"
        message_ar = "الوضع المالي تحت السيطرة"
        message_en = "Financial position is under control"
        detail_ar = f"صافي 90 يوم المتوقعة {projected_90['net']:,.2f} {currency_symbol_ar}."
        detail_en = f"Projected 90-day net is {projected_90['net']:,.2f} {currency_symbol_en}."
        focus_label_ar = "صافي 90 يوم"
        focus_label_en = "90-Day Net"
        focus_value = float(projected_90["net"])
        support_label_ar = "يحتاج متابعة"
        support_label_en = "Needs Follow-up"
        support_value = float(follow_up_total)
        tx_by_month = session_state.get("transactions", {})
        tx_count = 0
        if isinstance(tx_by_month, dict):
            tx_count = sum(len(txs or []) for txs in tx_by_month.values())
        has_user_data = any(
            [
                int(tx_count) > 0,
                int(savings.get("all_count", 0)) > 0,
                int(projects.get("all_count", 0)) > 0,
                int(docs.get("count", 0)) > 0,
                int(coverage.get("overdue_count", 0)) > 0,
                int(coverage.get("expected_count", 0)) > 0,
            ]
        )

        if not has_user_data:
            return {
                "status": "empty",
                "message_ar": "إضافة أول حركة مالية",
                "message_en": "Add your first transaction",
                "detail_ar": "بمجرد إضافة دخل أو مصروف، سيظهر لك ملخص أوضح للوضع المالي.",
                "detail_en": "Once you add income or expenses, your financial summary will appear here.",
                "focus_label_ar": "صافي 90 يوم",
                "focus_label_en": "90-Day Net",
                "focus_value": 0.0,
                "support_label_ar": "يحتاج متابعة",
                "support_label_en": "Needs Follow-up",
                "support_value": 0.0,
            }

        if projected_90["net"] < 0:
            status = "cash_pressure_90"
            message_ar = "يوجد ضغط نقدي متوقع"
            message_en = "Expected cash pressure"
            detail_ar = (
                f"صافي 90 يوم المتوقعة {projected_90['net']:,.2f} {currency_symbol_ar}، "
                f"والفرق عن آخر 90 يوم {comparison_90['net_delta']:+,.2f}."
            )
            detail_en = (
                f"Projected 90-day net is {projected_90['net']:,.2f} {currency_symbol_en}, "
                f"with a {comparison_90['net_delta']:+,.2f} change versus the last 90 days."
            )
            support_label_ar = "متأخر ومفتوح"
            support_label_en = "Open + Overdue"
        elif coverage["net_coverage"] < 0 and coverage["overdue_commitments"] > 0:
            status = "coverage_gap"
            message_ar = "توجد فجوة تغطية حاليًا"
            message_en = "Coverage gap detected"
            detail_ar = "الالتزامات المتأخرة أعلى من المدخول المتوقع."
            detail_en = "Overdue commitments are higher than expected income."
            focus_label_ar = "صافي 90 يوم"
            focus_label_en = "90-Day Net"
            support_label_ar = "فجوة الاستحقاقات"
            support_label_en = "Entitlement Gap"
            support_value = float(abs(coverage["net_coverage"]))
        elif follow_up_total > 0:
            status = "needs_follow_up"
            message_ar = "توجد مبالغ تحتاج متابعة"
            message_en = "Amounts need follow-up"
            detail_ar = f"توجد عناصر مفتوحة أو متأخرة بقيمة {follow_up_total:,.2f} {currency_symbol_ar}."
            detail_en = f"Open or overdue items total {follow_up_total:,.2f} {currency_symbol_en}."
        elif project_impact["personal_net_after_support"] < 0:
            status = "project_pressure"
            message_ar = "المشاريع تضغط على الحساب الشخصي"
            message_en = "Projects are pressuring the personal account"
            detail_ar = "يؤثر عجز المشروع الحالي على صافي الحساب."
            detail_en = "Current project deficit is impacting the net balance."
        elif seasonal["status"] == "high":
            status = "spending_high"
            message_ar = "مصاريفك أعلى من المعتاد"
            message_en = "Your spending is above usual"
            detail_ar = "مصروف هذا الشهر أعلى من متوسط آخر 6 أشهر."
            detail_en = "This month expenses are above the 6-month average."
        elif merchant_signal["status"] == "highlight":
            status = "note_pattern"
            merchant_label = str(merchant_signal["label"])
            merchant_amount = float(merchant_signal["amount"])
            merchant_count = int(merchant_signal["count"])
            message_ar = f"{merchant_label} واضح في مصروفك"
            message_en = f"{merchant_label} stands out this month"
            detail_ar = (
                f"الملاحظات تظهر {merchant_count} حركة مرتبطة بـ {merchant_label} "
                f"بقيمة {merchant_amount:,.2f} {currency_symbol_ar}."
            )
            detail_en = (
                f"Your notes show {merchant_count} transactions linked to {merchant_label} "
                f"for {merchant_amount:,.2f} {currency_symbol_en}."
            )
        elif docs["expired_count"] > 0 or docs["upcoming_30_count"] > 0:
            status = "docs_due"
            message_ar = "توجد مستندات تحتاج متابعة"
            message_en = "Documents need follow-up"
            detail_ar = "في مستندات منتهية أو قرب موعد تجديدها."
            detail_en = "Some documents are expired or close to renewal."

        return {
            "status": status,
            "message_ar": message_ar,
            "message_en": message_en,
            "detail_ar": detail_ar,
            "detail_en": detail_en,
            "focus_label_ar": focus_label_ar,
            "focus_label_en": focus_label_en,
            "focus_value": float(focus_value),
            "support_label_ar": support_label_ar,
            "support_label_en": support_label_en,
            "support_value": float(support_value),
        }
