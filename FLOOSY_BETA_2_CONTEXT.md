# Floosy Beta 2 Context

Last updated: 2026-04-25

Use this file as the official handoff/context file for Floosy Beta 2. If a conversation gets compressed or a new chat starts, read this file first.

## Operating Rule for Every New Conversation

This file is the source of truth for Floosy Beta 2.

For any new Codex/AI conversation:

- Read this file before planning or editing.
- Treat it as the baseline for product logic, tone, rules, and current bugs.
- If a feature is added, update this file.
- If a bug is found, add it under `Bugs Log > Open / Needs Review`.
- If a bug is fixed, move or copy it under `Bugs Log > Resolved Bugs`.
- If a product rule changes, update the relevant rule section.
- If a plan changes, update `Next Work Plan`.
- Do not rely only on chat memory; keep important decisions here.

In short: every meaningful change to Floosy should leave a trace in this context file.

### Context Capture Duty

Codex must proactively update this file when important Floosy context appears, even if the user does not explicitly ask or forgets to mention it.

- Add new context without deleting older notes.
- Capture meaningful code changes, product decisions, bugs, fixes, real-life scenarios, user testing notes, workflow discoveries, UI/design decisions, and cloud/data/security decisions.
- If a new bug appears, add it under `Bugs Log > Open / Needs Review`.
- If a bug is fixed, move or copy it under `Bugs Log > Resolved Bugs`.
- If a real-life scenario appears during testing, add it under the relevant `Things Still Needing Work` section.
- If the user mentions an idea, adjustment, concern, or "do this later" item that is not implemented immediately, capture it as a to-do/backlog item under `Things Still Needing Work`, `Next Work Plan`, or `Future Ideas`.
- Do not assume unimplemented ideas are rejected. If they are useful but not done now, preserve them for later review.
- If a plan changes, update `Next Work Plan`.
- If the correct section is unclear, add a short dated note in the closest relevant section instead of leaving it only in chat memory.
- Preserve the timeline. Do not remove history unless the user explicitly asks to create a cleaner Beta 3 context file.

## Timeline / Change History

Use this section to show how Floosy evolved over time and how much work each phase took.

When adding future updates:

- Add the date.
- Add the commit hash if available.
- Summarize the product change, not only the code change.
- Keep older entries. Do not delete history unless creating a cleaner Beta 3 context file.

### 2026-04-20

- Added an explicit Context Capture Duty so future Codex/AI conversations proactively append important changes, scenarios, bugs, fixes, testing notes, and product decisions to this file without deleting prior history.
- Added an explicit to-do/backlog capture rule so ideas and requested changes that are not implemented immediately are preserved for later review.

### 2026-04-25

- Added a localStorage bootstrap fallback for Remember Sign-In so a personal browser can restore the hosted auth token after refresh if the deployment loses the cookie.
- Real-world Safari testing on the hosted beta still showed Remember Sign-In failing after refresh, so this remains an open hosted-browser issue rather than a confirmed fix.
- Captured a product note from real usage: expected salary/income should not look "suspended" or "late" just because the entitlement day passed if nothing was received yet.
- Captured a Monthly Items design note: the model may need an explicit entitlement day/date field in addition to entitlement month and actual payment date.
- Added true editing support for My Account transactions after save, including moving the transaction to another month automatically if the edited date changes month.
- Real-world hosted testing confirmed that unsynced local transactions on the Streamlit beta can appear temporarily across visits, then disappear after app restart/reboot. This reinforces that hosted local persistence is not safe for real data and Cloud must be used for anything important.
- Captured two new product ideas from real use:
  - Documents may need a camera capture/scan flow so a paper can be turned into a saved document directly from mobile camera.
  - Floosy may need a universal search layer so records added in Account or elsewhere can still be found quickly by search even if the user forgot where they filed them.

### 2026-04-24

- Improved hosted Remember Sign-In reliability by strengthening how the browser refresh token cookie is written for Streamlit deployments.
- Added targeted tests for cloud auth cookie encode/read/write behavior.
- Added a hosted cookie-header fallback so Remember Sign-In can still restore when the deployed runtime exposes the cookie in raw request headers instead of `st.context.cookies`.
- Added a localStorage bootstrap fallback for personal-device Remember Sign-In: if the hosted cookie is missing after refresh, the browser can restore it from localStorage and reload once.
- Clarified product behavior: shared hosted local persistence is intentionally non-durable, so real beta usage should rely on Cloud sync instead of hosted local storage.

### 2026-04-19

- `71abd4b` Reorganized this context file into a source-of-truth handoff with an explicit bugs log.
- `2aacb0c` Improved Monthly Items entitlement tracking:
  - Separated entitlement month from actual payment/receipt date.
  - Changed expected income language so salary/income does not look like overdue expenses.
  - Added tests for social security, delayed income, and expected income cases.
- `61fdc20` Created `FLOOSY_BETA_2_CONTEXT.md` as the official Beta 2 context file.
- `6d1b898` Added Remember Sign-In:
  - Stores a local browser refresh token.
  - Restores cloud sign-in after refresh.
  - Pulls cloud data before syncing to avoid overwriting with empty local state.
- `18153ac` Linked project funding to account transactions:
  - Project movements funded from My Account now deduct from My Account.
  - Deleting linked project movements removes linked account transactions.
- `9fc9167` Reset Account Add Transaction form after save.

### 2026-04-18

- `ba51ecc` Neutralized Arabic app copy so it is general for all users, not personally addressed.
- `c7310df` Hid Streamlit input instructions that overlapped with typing.
- `02e5683`, `1dd5f4d`, `ea21e4e` Improved cloud auth flow:
  - Removed enter-submit issues.
  - Refreshed auth mode fields immediately.
  - Added password recovery.
- `785c4aa` Replaced raw Supabase/Cloudflare HTML errors with friendly messages.
- `4127452` Documented auth and cloud strategy.
- `c8a1c4b` Ignored local backup/test data files.
- `cfcd0b2` Reopened Monthly Items after deleting generated transactions.
- `ce22d5c` Added transaction proof attachments.
- `a0ea269` Allowed full editing of monthly items.

### 2026-04-17

- `3c9d35f` Refined Smart Summary and transaction notes.
- `dbdf5ac` Fixed Dashboard quick add category maps.
- `e5fe001` Removed note placeholder examples that were too specific.

### 2026-04-15

- Multiple commits fixed Arabic sidebar/RTL behavior on web and mobile.
- `c869564` pinned Streamlit to `1.45.1` to keep sidebar behavior stable.

## Quick Handoff

Floosy is a real beta finance/admin app for a small business owner. It is not just an accounting demo.

Current working focus:

- Dashboard: make Smart Summary smarter and less dramatic when data is still new.
- Account: keep testing Monthly Items with real cases like salary, social security, and delayed income.
- Projects: keep validating that project transactions linked to the account deduct from My Account correctly.
- Documents: organize company papers, proofs, government documents, renewals, contracts, and sensitive evidence.

Most important product rule:

- My Account is the money truth.
- Projects measure project performance.
- Savings holds reserved money.
- Documents preserve proof.
- Monthly Items must separate entitlement month from actual payment/receipt date.

## 1. App Goal

Floosy helps a small business owner manage financial and administrative chaos in one place.

It helps answer:

- What was paid?
- What month was it for?
- When was it actually paid or received?
- Where is the proof?
- What is still pending?
- How did this affect the account balance?

The app should feel practical, calm, and protective. It is built from real daily use, not theoretical finance.

## 2. Money Model

Every amount must have a clear meaning.

### My Account

The daily money truth. Any money that actually enters or leaves the account should appear here.

Examples:

- Rent paid
- Salary received
- Government fee paid
- One-time income
- Personal expense
- Transfer from account into a project

### Savings

Reserved money. It is still money the user has, but it is mentally/operationally set aside.

Examples:

- Capital reserve
- Emergency reserve
- Future expansion
- Liability reserve

### Projects

Used when the user wants to measure profit/loss for a specific activity.

Examples:

- Farm expansion
- A specific business activity
- A temporary project that needs separate tracking

Important:

- If money comes from outside directly into the project, it does not deduct from My Account.
- If money comes from My Account into the project, it must deduct from My Account.

### Documents

Proof and admin archive.

Examples:

- Licenses
- Contracts
- Resignations
- Government papers
- Payment screenshots
- PDFs
- Renewal documents

### Invoices & Tax

Invoices, tax classification, and separating business/personal/deductible expenses.

## 3. Page Responsibilities

### Dashboard

Shows the overall financial picture and Smart Summary.

Must not over-warn if data is too new or not enough history exists.

### My Account

Main transaction log and Monthly Items.

It should reflect reality:

- Money entered
- Money left
- What month the amount belongs to
- When it was actually paid/received
- Proof when available

### Monthly Items

Recurring commitments or expected income.

Examples:

- Rent
- Salary
- Social security
- Expected monthly income
- Delayed income from a client

Must distinguish income from expense. Income should not be treated like an overdue bill.

### Savings

Reserved funds and goals.

### Projects

Project-level tracking. Can optionally record the account effect when the project money comes from My Account.

### Documents

Company/admin proof center.

### Financial Analyzer

Explains financial position, but should be careful with warnings when there is limited data.

### Settings

Language, currency, cloud sync, privacy, backup/restore, cloud account.

## 4. Fixed Rules

- Any actual money movement must be visible in My Account.
- A project funded from My Account must deduct from My Account.
- External project income should not deduct from My Account.
- Rare/one-time income goes to My Account unless it is intentionally tracked as a project.
- Reserved money goes to Savings.
- Do not mix personal expenses with project expenses.
- Do not write app copy that sounds personally addressed to the developer.
- Arabic copy inside the app should be neutral and general.
- Avoid sensitive personal names/details in notes when they could create risk.
- Proof matters. Important or disputed payments should have screenshot/PDF proof.
- Arabic/English workflow text should not be mixed inside user flows.
- Brand/logo text can be bilingual if intentional.
- Do not touch `FLOOSY_PRICING_PLANS.md` if it is untracked unless explicitly requested.
- On shared hosted Streamlit deployments, local persistence is intentionally non-durable. Real beta usage should rely on Cloud sync.

## 5. Decision Rules

When deciding where a transaction belongs:

- If money actually entered or left the account: My Account.
- If it belongs to a project and we need project profit/loss: Projects.
- If project money came from My Account: Projects + enable account effect.
- If money is reserved for later: Savings.
- If there is proof: attach it to the transaction or add it in Documents.
- If payment date differs from entitlement month: record both.
- If the last paid month is unknown: leave it pending until papers are reviewed.

## 6. Critical Logic: Salary, Social Security, and Entitlement Month

Floosy must separate three concepts:

### Entitlement Month

The month the money belongs to.

Examples:

- March salary
- March social security
- February delayed income

### Actual Payment / Receipt Date

The real date money entered or left the account.

Examples:

- Paid social security on 2026-03-20
- Received February income on 2026-04-10

### Display / Accounting Month

The month being viewed in the app, or the month where the cash movement appears.

### Social Security Example

A user may pay social security twice in March:

- One payment for February entitlement
- One payment for March entitlement

Also, the system may only show March entitlement on April 1.

Therefore a payment needs:

- Payment date
- Entitlement month
- Type
- Category
- Proof

Example:

- Payment date: 2026-03-20
- Entitlement month: February 2026
- Type: Expense
- Category: Social Security
- Proof: Screenshot/PDF

### Salary / Expected Income Example

Expected income should not be labeled as "late" the same way expenses are.

Better labels:

- Expected income not received yet
- Waiting for receipt
- Not received

Avoid labels that sound like a bill is overdue.

### Delayed Income Example

If a client pays in April for February entitlement:

- Receipt date: April
- Entitlement month: February
- Status: received
- Search should find it by client name or entitlement month.

## 7. Recently Added Features

- Cloud Sync through Supabase with per-user data separation by `user_id`.
- Remember Sign-In on device using a local browser refresh token, not password storage.
- Cloud Auth with Sign Up, Sign In, Confirm Password, and Forgot Password.
- Project to Account Link: project movements can create automatic My Account expenses when the money comes from the account.
- Deleting linked project transactions also removes linked account transactions.
- Transaction Proofs: account transactions can include screenshot/PDF proof and download later.
- Monthly Item Confirmation Proof: proof can be attached when confirming monthly items.
- Monthly Item Reopen: deleting a generated transaction can return the monthly item to confirmation.
- Monthly Entitlement Tracking: stores `payment_month_key` and `entitlement_month_key`.
- Income Monthly Status Language: income is expected/not received/received, not "overdue" like expenses.
- Account Form Reset: account add transaction form clears after saving.
- Neutral Arabic Messaging: no personal Arabic copy aimed at the developer.
- Streamlit Input Hint Fix: hides "Press Enter to apply/submit" instruction overlay.
- Friendly Supabase Errors: HTML/Cloudflare errors are converted to user-friendly messages.

## 8. Bugs Log

Keep this section as a running log. Add new bugs under "Open / Needs Review" first, then move to "Resolved" after fixing.

### Resolved Bugs

- Project transaction did not deduct from My Account when the project was funded from the account.
  Fixed by adding linked account transactions for project movements with account effect.

- Deleting a linked project transaction could leave the account transaction behind.
  Fixed by deleting linked account transactions using `account_link_id` / `project_link_id`.

- Account Add Transaction form kept old values after save.
  Fixed by using a form nonce so the form resets after saving.

- Monthly item stayed completed even after deleting its generated transaction.
  Fixed by reopening the related monthly item when the transaction is deleted.

- Monthly items mixed payment date and entitlement month.
  Fixed by storing separate payment and entitlement month keys.

- Expected income was worded like an overdue expense.
  Fixed by changing income wording to expected/not received/received.

- Supabase Cloudflare/HTML errors appeared raw in the UI.
  Fixed by sanitizing/friendly formatting Supabase errors.

- Sign-in was lost after refresh.
  Fixed by Remember Sign-In using local refresh token and session refresh.

- Streamlit showed "Press Enter to apply/submit" over input fields.
  Fixed by hiding Streamlit input instructions.

- Arabic user-facing copy included personal wording like "راجعي/ارفعي/تقدرين".
  Fixed by neutralizing Arabic copy.

- Project/account linked behavior did not reflect the real balance.
  Fixed so project funding from account creates the correct My Account expense.

- RTL/sidebar behavior had deployment/mobile differences earlier.
  Fixed enough for current beta after CSS/Streamlit version handling.

- Local Playwright smoke test data appeared in local transactions.
  Identified as test data, cleaned locally, and local data backup files were ignored.

- My Account transactions could not be edited after saving.
  Fixed by enabling direct transaction editing in the Account table and saving changes back to the correct month.

### Open / Needs Review

- Dashboard Smart Summary may over-warn when there is not enough history or when the month is just starting.

- Hosted Safari Remember Sign-In still fails after refresh on `floosy-beta.streamlit.app` even after cookie, header, and localStorage fallback attempts.
  Current status: unresolved on deployed Safari/browser behavior.
  Practical workaround for now: sign in manually and rely on browser password autofill until auth persistence is redesigned or replaced.

- Monthly Items need real-life testing with:
  - Social security February paid in March
  - Social security March paid in March/April
  - Expected salary not received yet
  - Delayed income received in April for February

- Documents need better organization for company papers.

- Documents may need categories such as:
  - Government
  - License
  - Contract
  - Resignation
  - Payment proof
  - Renewal
  - Sensitive

- Documents may need linking to transactions or cases.

- Project linked transaction edit behavior needs review.
  Current behavior is mainly safe for add/delete, but editing linked transactions may need rules later.

- Cloud sync UX may need clearer wording around Save My Data / Load My Data / auto-sync.

- Dashboard colors and summary tone still need final polish after logic stabilizes.

### Bug Entry Template

Use this when adding new bugs:

```text
- Bug:
  Where:
  What happened:
  Expected:
  Status:
  Notes:
```

## 9. Things Still Needing Work

### Dashboard Smart Summary

Make it smarter and calmer:

- Do not compare with previous month if there is no meaningful previous month.
- Do not over-warn when the user just started entering data.
- Show neutral empty/new-user states.
- Use good/warning/critical only when data supports it.

### Account / Monthly Items

Continue testing real workflows after entitlement tracking:

- Social security
- Salary
- Delayed income
- Rent
- Unknown last-paid month
- Expected income should not look overdue/suspended just because the due day passed if no receipt happened yet.
- Monthly Items may need one more field for `entitlement day/date` so the UI can show:
  - entitlement month
  - due day/date
  - actual payment/receipt date
  - accounting month where the transaction was recorded

- Scenario:
  Description: Social security for February was paid in March.
  Input: Entitlement month = February, payment date = a date in March.
  Expected behavior: The transaction appears by the March payment date, but remains searchable and understandable as February entitlement.

- Scenario:
  Description: Delayed income for February was received in April.
  Input: Entitlement month = February, receipt date = a date in April, customer/client name is included.
  Expected behavior: The receipt appears by the April receipt date, remains linked and understandable as February entitlement, is searchable by customer/client name or entitlement month, and does not look like normal April income.

- Scenario:
  Description: Expected salary for March has not been received yet.
  Input: Entitlement month = March, no actual receipt date yet.
  Expected behavior: The item appears as expected/not received income, does not affect account balance, and is clearly shown as pending without being treated like an overdue expense.

### Documents

Build a better company paper workflow:

- Upload company papers
- Search quickly
- Add renewal dates
- Add categories
- Attach proof
- Possibly link documents to transactions later
- Add mobile camera capture / scan so the user can create a document directly from camera without separate manual upload first

### Projects

Validate:

- Add project income from outside
- Add project funding from account
- Delete linked project movement
- Confirm account balance stays correct

### UI Polish

Only after behavior is stable:

- Light spacing cleanup
- Dashboard summary visuals
- Card hierarchy
- Document page organization

## 10. Next Work Plan

Recommended order:

1. Test Monthly Items with real social security/salary/delayed income examples.
2. Fix Dashboard Smart Summary based on the new entitlement logic.
3. Organize Documents for company papers.
4. Review Projects linked-account edge cases.
5. Do light UI polish only after behavior is stable.

## 11. Future Ideas

### Case Folder / ملف حالة

A future feature that groups:

- Related transactions
- Documents
- Important dates
- Notes
- Proofs

Useful for company/admin cases where the user needs to quickly answer: "Where is my proof?"

### Universal Search / البحث الشامل

A future feature that lets the user find important records even if they do not remember which section they saved them in.

Possible sources:

- Account transactions
- Notes
- Customer/client names
- Proof labels
- Document titles
- Related months or entitlement months

Goal:

- If the user searches for a known word, name, or clue, Floosy should surface the related result even if it was saved under a different section than expected.

## 12. Collaboration Style

The user prefers Kuwaiti/Gulf Arabic with a warm, practical tone.

Codex should:

- Be a thinking partner, not just a code writer.
- Explain decisions simply.
- Be direct but kind.
- Execute when the task is clear.
- Read files before editing.
- Use `apply_patch` for manual edits.
- Run tests after code changes.
- Commit and push after successful verification.
- Keep final answers concise.
- Preserve user work and avoid reverting unrelated changes.
- Keep app copy professional and general.

If context is compressed or unclear:

1. Read this file.
2. Check latest git status/log if needed.
3. Continue from the current plan.

## 13. One-Line Reminder

Floosy should reduce financial/admin confusion by showing what happened, when it happened, what month it belongs to, and where the proof is.
