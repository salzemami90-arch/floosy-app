import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from config_floosy import arabic_months, english_months, get_saving_totals
from services.purchase_goal_service import PurchaseGoalService


def render(month_key: str, month: str, year: int):
    is_en = st.session_state.settings.get("language") == "English"
    t = (lambda ar, en: en if is_en else ar)
    month_display = english_months[arabic_months.index(month)] if (is_en and month in arabic_months) else month

    st.title(f"{t('التوفير', 'Savings')} - {month_display} {year}")

    s_data = st.session_state.savings[month_key]
    s_data.setdefault("goal", 0.0)
    s_data.setdefault("transactions", [])
    savings_meta = st.session_state.savings.setdefault("__meta__", {})
    if not isinstance(savings_meta, dict):
        st.session_state.savings["__meta__"] = {}
        savings_meta = st.session_state.savings["__meta__"]
    savings_meta.setdefault("purchase_goals", [])
    savings_meta["purchase_goals"] = PurchaseGoalService.normalize_goals(savings_meta.get("purchase_goals", []))

    currency = st.session_state.settings["default_currency"]
    currency_symbol = currency.split(" - ")[0] if " - " in currency else currency
    currency_map_en = {"د.ك": "KWD", "ر.س": "SAR", "د.إ": "AED", "$": "USD", "€": "EUR"}
    currency_view = currency_map_en.get(currency_symbol, currency_symbol) if is_en else currency_symbol

    s_data["goal"] = st.number_input(
        t("هدف التوفير الكلي", "Total Savings Goal"),
        min_value=0.0,
        step=50.0,
        value=float(s_data.get("goal", 0.0)),
    )

    with st.expander(t("إضافة معاملة التوفير", "Add Savings Transaction"), expanded=False):
        with st.form("add_saving_tx"):
            sd_date = st.date_input(t("التاريخ", "Date"), value=datetime.today())
            sd_type_lbl = st.selectbox(t("النوع", "Type"), [t("إيداع", "Deposit"), t("سحب", "Withdraw")])
            sd_amount = st.number_input(t("المبلغ", "Amount"), min_value=0.0, step=5.0)
            sd_note = st.text_input(t("ملاحظة (اختياري)", "Note (Optional)"), "")
            save_tx_btn = st.form_submit_button(t("حفظ", "Save"))

    if save_tx_btn and sd_amount > 0:
        s_data["transactions"].append(
            {
                "date": sd_date.strftime("%Y-%m-%d"),
                "type": "إيداع" if sd_type_lbl == t("إيداع", "Deposit") else "سحب",
                "amount": float(sd_amount),
                "note": sd_note,
            }
        )
        st.success(t("تم حفظ حركة التوفير.", "Savings transaction saved."))
        st.rerun()

    txs = s_data["transactions"]
    total_in_month = sum(t["amount"] for t in txs if t["type"] == "إيداع")
    total_out_month = sum(t["amount"] for t in txs if t["type"] == "سحب")
    balance_month = total_in_month - total_out_month
    progress_pct = (balance_month / s_data["goal"] * 100.0) if s_data["goal"] > 0 else 0.0

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(t("رصيد هذا الشهر", "This Month Balance"), f"{balance_month:,.0f} {currency_view}")
    with c2:
        st.metric(t("إيداعات هذا الشهر", "This Month Deposits"), f"{total_in_month:,.0f} {currency_view}")
    with c3:
        st.metric(t("سحوبات هذا الشهر", "This Month Withdrawals"), f"{total_out_month:,.0f} {currency_view}", delta_color="inverse")

    if s_data["goal"] > 0:
        st.progress(max(0.0, min(1.0, progress_pct / 100.0)))
        st.caption(t(f"نسبة تحقيق الهدف: {progress_pct:.1f}%", f"Goal progress: {progress_pct:.1f}%"))

    total_saved_all, total_withdraw_all = get_saving_totals()
    st.metric(t("إجمالي التوفير (كل الشهور)", "Total Savings (All Months)"), f"{(total_saved_all - total_withdraw_all):,.0f} {currency_view}")

    purchase_summary = PurchaseGoalService.goals_summary(savings_meta.get("purchase_goals", []))
    purchase_goals = purchase_summary["goals"]

    st.markdown("---")
    st.markdown(f"### {t('أهداف الشراء', 'Purchase Goals')}")
    st.caption(
        t(
            "يمكن توزيع هدف الشراء على الشهور ومتابعة المبلغ المطلوب شهريًا.",
            "Purchase goals can be spread across months to track the required monthly amount.",
        )
    )

    g1, g2, g3 = st.columns(3)
    with g1:
        st.metric(t("الأهداف النشطة", "Active Goals"), str(purchase_summary["active_count"]))
    with g2:
        st.metric(t("المتبقي على كل الأهداف", "Total Remaining"), f"{purchase_summary['total_remaining']:,.0f} {currency_view}")
    with g3:
        st.metric(
            t("المبلغ الشهري المقترح", "Suggested Monthly Amount"),
            f"{purchase_summary['total_monthly_needed']:,.0f} {currency_view}",
            delta=t(f"مكتمل {purchase_summary['completed_count']}", f"Completed {purchase_summary['completed_count']}"),
            delta_color="off",
        )

    default_target_date = (datetime.today() + timedelta(days=180)).date()
    with st.expander(t("إضافة هدف شراء", "Add Purchase Goal"), expanded=False):
        with st.form("add_purchase_goal_form", clear_on_submit=True):
            pg_name = st.text_input(t("اسم الهدف", "Goal Name"), placeholder=t("مثال: عطور", "Example: Perfumes"))
            pg_c1, pg_c2 = st.columns(2)
            with pg_c1:
                pg_target_amount = st.number_input(t("المبلغ المستهدف", "Target Amount"), min_value=0.0, step=10.0)
            with pg_c2:
                pg_saved_amount = st.number_input(t("المبلغ المدخر حاليًا", "Currently Saved"), min_value=0.0, step=10.0)
            pg_target_date = st.date_input(t("تاريخ الهدف", "Target Date"), value=default_target_date, key="purchase_goal_target_date")
            pg_note = st.text_input(t("ملاحظة (اختياري)", "Note (Optional)"), "")
            pg_submit = st.form_submit_button(t("حفظ الهدف", "Save Goal"), use_container_width=True)

        if pg_submit:
            if not pg_name.strip():
                st.warning(t("يرجى إدخال اسم الهدف أولًا.", "Please enter a goal name first."))
            elif pg_target_amount <= 0:
                st.warning(t("المبلغ المستهدف يجب أن يكون أكبر من صفر.", "Target amount must be greater than zero."))
            else:
                savings_meta["purchase_goals"].append(
                    PurchaseGoalService.normalize_goal(
                        {
                            "name": pg_name,
                            "target_amount": pg_target_amount,
                            "saved_amount": pg_saved_amount,
                            "target_date": pg_target_date.strftime("%Y-%m-%d"),
                            "note": pg_note,
                            "active": True,
                        }
                    )
                )
                savings_meta["purchase_goals"] = PurchaseGoalService.normalize_goals(savings_meta["purchase_goals"])
                st.success(t("تم حفظ الهدف.", "Goal saved."))
                st.rerun()

    if not purchase_goals:
        st.info(t("لا توجد أهداف شراء حالياً.", "No purchase goals yet."))
    else:
        for goal in purchase_goals:
            goal_id = goal["goal_id"]
            goal_name = goal["name"] or t("هدف بدون اسم", "Unnamed Goal")
            goal_status = goal["status"]
            if goal_status == "done":
                status_label = t("مكتمل", "Done")
            elif goal_status == "overdue":
                status_label = t("متأخر", "Overdue")
            else:
                status_label = t("نشط", "Active")

            expander_title = t(
                f"{goal_name} | المتبقي {goal['remaining_amount']:,.0f} {currency_view} | شهريًا {goal['monthly_needed']:,.0f} {currency_view}",
                f"{goal_name} | Remaining {goal['remaining_amount']:,.0f} {currency_view} | Monthly {goal['monthly_needed']:,.0f} {currency_view}",
            )
            with st.expander(expander_title, expanded=False):
                pgm1, pgm2, pgm3, pgm4 = st.columns(4)
                with pgm1:
                    st.metric(t("المستهدف", "Target"), f"{goal['target_amount']:,.0f} {currency_view}")
                with pgm2:
                    st.metric(t("المخصص", "Allocated"), f"{goal['saved_amount']:,.0f} {currency_view}")
                with pgm3:
                    st.metric(t("المتبقي", "Remaining"), f"{goal['remaining_amount']:,.0f} {currency_view}")
                with pgm4:
                    st.metric(
                        t("المبلغ الشهري", "Monthly Amount"),
                        f"{goal['monthly_needed']:,.0f} {currency_view}",
                        delta=status_label,
                        delta_color="off",
                    )

                st.progress(max(0.0, min(1.0, goal["progress_pct"] / 100.0)))
                st.caption(
                    t(
                        f"نسبة الإنجاز {goal['progress_pct']:.1f}% | الشهور المتبقية {goal['months_left']}",
                        f"Progress {goal['progress_pct']:.1f}% | Months left {goal['months_left']}",
                    )
                )
                if goal.get("note"):
                    st.caption(goal["note"])

                with st.form(f"edit_purchase_goal_{goal_id}", clear_on_submit=False):
                    eg_name = st.text_input(t("اسم الهدف", "Goal Name"), value=goal_name)
                    eg_c1, eg_c2 = st.columns(2)
                    with eg_c1:
                        eg_target_amount = st.number_input(
                            t("المبلغ المستهدف", "Target Amount"),
                            min_value=0.0,
                            step=10.0,
                            value=float(goal["target_amount"]),
                            key=f"eg_target_amount_{goal_id}",
                        )
                    with eg_c2:
                        eg_saved_amount = st.number_input(
                        t("المبلغ المدخر حاليًا", "Currently Saved"),
                            min_value=0.0,
                            step=10.0,
                            value=float(goal["saved_amount"]),
                            key=f"eg_saved_amount_{goal_id}",
                        )
                    eg_target_date = st.date_input(
                        t("تاريخ الهدف", "Target Date"),
                        value=datetime.strptime(goal["target_date"], "%Y-%m-%d").date(),
                        key=f"eg_target_date_{goal_id}",
                    )
                    eg_note = st.text_input(
                        t("ملاحظة", "Note"),
                        value=str(goal.get("note", "") or ""),
                        key=f"eg_note_{goal_id}",
                    )
                    eg_active = st.checkbox(
                        t("نشط", "Active"),
                        value=bool(goal.get("active", True)),
                        key=f"eg_active_{goal_id}",
                    )
                    eg_c1, eg_c2 = st.columns(2)
                    with eg_c1:
                        save_goal_btn = st.form_submit_button(t("حفظ التعديل", "Save Changes"), use_container_width=True)
                    with eg_c2:
                        delete_goal_btn = st.form_submit_button(t("حذف الهدف", "Delete Goal"), use_container_width=True)

                if save_goal_btn:
                    for idx, item in enumerate(savings_meta["purchase_goals"]):
                        if item.get("goal_id") != goal_id:
                            continue
                        savings_meta["purchase_goals"][idx] = PurchaseGoalService.normalize_goal(
                            {
                                "goal_id": goal_id,
                                "name": eg_name,
                                "target_amount": eg_target_amount,
                                "saved_amount": eg_saved_amount,
                                "target_date": eg_target_date.strftime("%Y-%m-%d"),
                                "note": eg_note,
                                "active": eg_active,
                            }
                        )
                        break
                    savings_meta["purchase_goals"] = PurchaseGoalService.normalize_goals(savings_meta["purchase_goals"])
                    st.success(t("تم تحديث الهدف.", "Goal updated."))
                    st.rerun()

                if delete_goal_btn:
                    savings_meta["purchase_goals"] = [
                        item for item in savings_meta["purchase_goals"] if item.get("goal_id") != goal_id
                    ]
                    st.success(t("تم حذف الهدف.", "Goal deleted."))
                    st.rerun()

    st.markdown(f"### {t('سجل حركات التوفير', 'Savings Transactions')}")
    if not txs:
        st.info(t("لا توجد حركات لهذا الشهر.", "No transactions for this month."))
        return

    df_s = pd.DataFrame(txs).copy()
    df_s.insert(0, "رقم", range(1, len(df_s) + 1))
    df_s["حذف"] = False
    date_col = t("التاريخ", "Date")
    type_col = t("النوع", "Type")
    amount_col = t("المبلغ", "Amount")
    note_col = t("ملاحظة", "Note")

    edited = st.data_editor(
        df_s.rename(columns={"date": date_col, "type": type_col, "amount": amount_col, "note": note_col}),
        use_container_width=True,
        hide_index=True,
        disabled=["رقم", date_col, type_col, amount_col, note_col],
        key="saving_tx_editor",
    )

    selected = edited[edited["حذف"]]["رقم"].tolist()
    if st.button(t("حذف المحدد من التوفير", "Delete Selected Savings Transactions"), use_container_width=True):
        if not selected:
            st.warning(t("يرجى اختيار حركة واحدة على الأقل.", "Select at least one transaction."))
        else:
            for row_num in sorted(selected, reverse=True):
                tx_index = int(row_num) - 1
                if 0 <= tx_index < len(txs):
                    txs.pop(tx_index)
            st.success(t(f"تم حذف {len(selected)} حركة.", f"Deleted {len(selected)} transaction(s)."))
            st.rerun()
