# Floosy Beta 2 Context

Last updated: 2026-05-04

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

### User Rule (2026-05-04)

This is now an explicit user rule:

- Any work we do on Floosy Beta 2 must be written in this file.
- Any bug that appears during testing must be written in this file.
- Do not leave important progress or bugs only inside chat messages.
- Treat this rule as mandatory project workflow, not a nice-to-have note.

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

### 2026-04-27

- Monthly Items management/confirmation UI is clearer now:
  - the add form shows a current-month entitlement example from the chosen due/expected day
  - the saved-items editor shows a current-month example plus last payment/receipt timing
  - the confirm payment/receipt form now shows entitlement date, actual payment/receipt date, and the month where the transaction will be recorded
- Fixed a small RTL readability issue in Monthly Items so ISO-style dates render in a stable left-to-right order inside Arabic UI text.
- Expected income that passes its expected day without being received now switches from the normal income-blue state to a warning palette instead of looking unchanged.

### 2026-04-28

- Hardened local-vs-cloud safety during Cloud sign-in and refresh restore:
  - Floosy no longer auto-imports cloud data over meaningful local data when the two copies differ.
  - If cloud data is different, local data stays on the device and auto-sync is paused until the user explicitly chooses `Load My Data` or `Save My Data`.
  - If no cloud copy exists yet, local data stays on the device and auto-upload remains paused until the user explicitly chooses `Save My Data`.
  - If cloud loading fails during sign-in/restore, local data stays on the device and auto-sync remains paused instead of risking an accidental overwrite.
- Added explicit in-app cloud notices so the user can understand when Floosy is keeping local data, waiting for manual save, or asking for a manual cloud load.
- Broadened hosted Remember Sign-In recovery logic so cookie/localStorage bootstrap now tries all accessible frame/window contexts, not only the immediate parent frame.
- Added regression coverage for the wider hosted frame-chain cookie/bootstrap behavior before more Safari testing on the deployed beta.
- Added a dedicated browser-storage bridge for hosted Remember Sign-In recovery, so Safari can return the remembered refresh token from browser local storage even when cookie restore is unreliable.
- Cloud sign-out / account deletion / non-remembered sign-in now explicitly request browser-storage clearing in addition to clearing the cookie.
- Improved first-login Remember Sign-In persistence flow:
  - after a remembered sign-in succeeds, Floosy now writes the browser auth token first and then reloads the page
  - this avoids losing the remembered refresh token because of an immediate server-side rerun before the browser had a chance to store it
  - verified by automated regression tests, but still needs final real-device/user confirmation before the open bug can be considered fully closed
- Added a localhost-only remembered-auth fallback:
  - on local runs, Floosy now keeps the remembered cloud refresh token in a separate local-only auth store on the same device
  - this protects localhost refresh persistence even if browser cookie/localStorage restoration is flaky
  - the fallback is local-only and separate from exported/cloud-synced app data
  - local detection now also respects Floosy's own local-persistence signal, so the localhost fallback still writes even if the browser URL is temporarily blank

### 2026-04-29

- Continued narrowing the Cloud Remember Sign-In difference between hosted beta and localhost:
  - hosted beta was restoring the remembered session correctly
  - localhost was still returning to the sign-in form after refresh even though the remembered auth fallback file was already being written
- Fixed the localhost restore flow so the cloud-auth restore check is reopened whenever the session is not truly logged in:
  - `init_session_state()` now clears the one-time restore guard when `cloud_auth` is missing a real access token
  - remembered sign-in also clears that restore guard just before the post-login reload
  - this targets the localhost case where a reused Streamlit session could keep the restore flag `True` and silently skip the actual restore attempt on refresh
- Fixed the localhost first sign-in flow with Remember Sign-In enabled:
  - localhost no longer forces a browser reload immediately after successful sign-in
  - instead, it saves the remembered auth locally and uses a normal Streamlit rerun
  - the hosted beta still keeps the browser reload path, while localhost avoids dropping back to the sign-in form right after the first successful login
- Refined the Documents page colors so renewal status is easier to read at a glance:
  - added soft status summary cards for expired / renew soon / valid
  - colored the status column inside the document table itself
  - kept the underlying document logic unchanged
- Added a dedicated Documents-only search and status filter:
  - search works inside Documents only
  - it can match document name, attachment name, date, or status
  - document actions now follow the filtered result set instead of the full unfiltered list
- Clarified a product rule for search and proof workflow:
  - Floosy should keep Account search and Documents search as two separate searches.
  - Documents should not be designed around salary/social-security-specific flows.
  - Salary/social security handling stays inside Account / Monthly Items, while Documents focuses on company papers and standalone admin files.
- Added one more localhost auth-restore fallback:
  - if the runtime URL is still blank during early app startup, Floosy now still trusts the local remembered-auth backup file when it already exists
  - this targets the specific localhost case where refresh returned the sign-in form with remembered email/password filled, while the hosted beta was restoring correctly
- Tightened localhost remembered-auth restore priority:
  - on local runs, Floosy now prefers the local remembered-auth backup over cookie/header payloads
  - this avoids stale localhost cookies overriding the fresh local backup after sign-in and refresh

### 2026-04-30

- Product naming direction for the app beta is now:
  - working beta name candidate: `Goush Money`
  - do not rename the app UI/codebase yet
  - keep the current Floosy/Floosy Beta naming in code until the app packaging / Apple submission phase gets closer
  - use the candidate name only as a planning/reference decision for now
- App beta packaging direction changed to a faster path:
  - no Capacitor / CocoaPods path for now because local macOS Ruby/CocoaPods setup became a time sink
  - use a simple native Xcode iOS shell with `WKWebView` instead
  - the shell now opens `https://goush-beta.streamlit.app`
  - the app shell injects light CSS/JS to hide some visible Streamlit chrome and feel less like a raw website
  - current goal is a private iPhone beta/test build first, not an App Store-ready native app yet

### 2026-05-01

- Built the first working iPhone beta shell outside the main repo using a native Xcode `WKWebView` wrapper:
  - the external shell project lives separately from the Floosy repo so the main Git history does not get mixed with Xcode/iOS files
  - the shell successfully opens the hosted beta inside both the simulator and a real iPhone
- Moved away from trying to control the Streamlit web sidebar directly on mobile:
  - the iPhone beta now uses a native Arabic drawer/menu instead of depending on the hosted web sidebar behavior
  - this is a deliberate mobile UX decision because the web sidebar was unreliable inside the wrapper
- Added hosted query-param page navigation support for the mobile shell:
  - Floosy now reads `page=...` from the URL and maps it to the matching internal section
  - the sidebar radio state is overridden by the requested page when needed so mobile navigation can take control
- Fixed a follow-up bug where Floosy's own browser-preference sync was overwriting the mobile `page=...` query param:
  - `f_w` / `f_lang` updates now preserve the current `page`
  - Floosy also re-stamps the active `page` query param after section selection so the link stays stable during reruns
- Real-world mobile beta status after these changes:
  - the shell, loading overlay, Arabic menu, and hosted page rendering are all working
  - navigation fallback-to-dashboard behavior was the key remaining mobile-shell issue under active test
  - latest live fixes were pushed specifically to stabilize `page=account` / `page=documents` routing from the native menu

### 2026-05-04

- Continued Beta 2 work on the iPhone shell and the hosted beta together instead of treating them as separate tracks:
  - reviewed how web language state is written in `app.py` / `config_floosy.py`
  - continued direct shell fixes in the external Xcode project file `ContentView.swift`
- Web/sidebar routing status improved:
  - localhost navigation is back to normal
  - hosted beta navigation is also behaving correctly again
  - `page`, `f_shell`, and `f_lang` preservation is now part of the expected shell/hosted behavior
- Mobile-shell language sync remains the main open app-wrapper issue:
  - in real testing, the web content can switch to Arabic while the native drawer/sidebar still shows English labels
  - this happens most clearly when the app starts in English and the user later changes language to Arabic inside Settings
- Latest shell-side engineering attempts for this bug:
  - the page sends explicit language hints through `data-floosy-language`, `window.__floosyShellLanguage`, and the `floosyBridge`
  - the shell watches DOM changes, history changes, and query-param changes
  - the latest patch changed the shell to trust visible page language and explicit DOM hints before trusting an older `f_lang` in the URL
  - native section navigation now also carries the currently detected language when opening a new section
- Regression note:
  - one later shell patch made the app behave worse in user testing
  - that last patch was rolled back so work can continue from the earlier working shell baseline instead of compounding the regression
- Follow-up shell patch after the rollback:
  - native section navigation now passes the currently detected language in `f_lang` when opening another page from the native drawer
  - the native drawer side now follows app language: Arabic drawer opens from the right, English drawer opens from the left
  - the loading/opening screen is now centered independently from drawer alignment, so the startup card no longer appears stuck near the top edge
- Latest verification status:
  - `xcodebuild` succeeded after the newest `ContentView.swift` changes
  - however, no final user confirmation exists yet that the Arabic native drawer issue is fully solved
- Devin/PR workflow note captured for future safety:
  - a Devin-generated PR (`PR #2`) was reviewed and should not be merged as-is because it is stale and far behind `main`
  - most of the claimed UI fixes were already present on `main`
  - the PR itself is not a safe source of truth for Beta 2 mobile work
- Context-process decision reinforced:
  - every meaningful Floosy Beta 2 change or bug must now be documented here as part of normal workflow, not only when a handoff happens
- Product naming direction changed after later brand discussion:
  - approved app name is now `GoushFi`
  - this replaces `Goush Money` as the latest preferred name
  - approved tagline is now `Smart money, in your hands`
  - approved Arabic tagline direction is now `امسك زمام فلوسك بذكاء`
  - approved display format for splash/header is:
    - `GoushFi`
    - `Smart money, in your hands`
  - Arabic UI can use:
    - `GoushFi`
    - `امسك زمام فلوسك بذكاء`
  - the iPhone shell now applies this branding directly in the startup/loading card and the native drawer header
  - the iPhone shell app display name under the home-screen icon is now also set to `GoushFi`
  - visible hosted/web app branding has now also started switching from `Floosy / فلوسي` to `GoushFi` in the main page title, dashboard header, sidebar title, and Settings heading
  - the old Floosy image logo is no longer used in the dashboard header; it is replaced by a temporary simple `G` lettermark using the app theme colors until the final logo/icon is designed
  - the current logo can remain temporary for now
  - logo, splash, and icon polish can happen later without blocking engineering progress

### 2026-04-20

- Added an explicit Context Capture Duty so future Codex/AI conversations proactively append important changes, scenarios, bugs, fixes, testing notes, and product decisions to this file without deleting prior history.
- Added an explicit to-do/backlog capture rule so ideas and requested changes that are not implemented immediately are preserved for later review.

### 2026-04-26

- Unified the sidebar period controls across all pages so the user always sees and can navigate by day, month, and year from one place instead of losing track between sections.
- Monthly Items cards now show clearer real-life tracking data:
  - oldest pending entitlement month
  - calculated entitlement date from the due day
  - last confirmed payment/receipt date
  - confirmed entitlement month tied to that payment/receipt

### 2026-04-25

- Restored the Settings sidebar behavior to match the desktop backups exactly: Settings should not show Month/Year selectors or a Selected Month block.
- Refined the Arabic sidebar CSS to be visually closer to the older backups by removing the forced fixed width and page padding, while keeping right-side open/close animation support.
- Added a localStorage bootstrap fallback for Remember Sign-In so a personal browser can restore the hosted auth token after refresh if the deployment loses the cookie.
- Real-world Safari testing on the hosted beta still showed Remember Sign-In failing after refresh, so this remains an open hosted-browser issue rather than a confirmed fix.
- Captured a product note from real usage: expected salary/income should not look "suspended" or "late" just because the entitlement day passed if nothing was received yet.
- Captured a Monthly Items design note: the model may need an explicit entitlement day/date field in addition to entitlement month and actual payment date.
- Added true editing support for My Account transactions after save, including moving the transaction to another month automatically if the edited date changes month.
- Real-world hosted testing confirmed that unsynced local transactions on the Streamlit beta can appear temporarily across visits, then disappear after app restart/reboot. This reinforces that hosted local persistence is not safe for real data and Cloud must be used for anything important.
- Captured two new product ideas from real use:
  - Documents may need a camera capture/scan flow so a paper can be turned into a saved document directly from mobile camera.
  - Floosy may need a universal search layer so records added in Account or elsewhere can still be found quickly by search even if the user forgot where they filed them.
- Clarified proof-storage direction from real use:
  - Salary slips, social security receipts, and similar payment evidence should primarily live with the related Account transaction / Monthly Item, not only as standalone Documents.
  - Camera scan should also be usable from Account as a proof-attachment entry path, not only from Documents.
- Added a hosted-data safety warning so the shared Streamlit beta explicitly tells the user to sign in to Cloud before entering important data.
- Added a clear Done / Partially Done / Still Open snapshot in this file so current progress is easier to track without rereading the whole history.

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

## Current Delivery Status

### Done

- Monthly Items now separate entitlement month from actual payment/receipt month.
- Expected income language is no longer treated like an overdue expense.
- My Account transactions support real editing after save.
- Project movements funded from My Account deduct correctly from My Account.
- Transaction proofs can be attached and downloaded from the related transaction flow.

### Partially Done

- Dashboard Smart Summary improved, but still needs calmer logic when history is thin or the month is just starting.
- Documents workflow exists, but still needs better structure for company paper use.
- Hosted Remember Sign-In was improved technically, but real Safari testing still shows it as unreliable on the deployed beta.
- Monthly Items timing is clearer in the UI now, but may still need a fully separate entitlement due-date field if real-life testing shows the preview approach is not enough.
- iPhone beta shell is now real and working in simulator / device, and hosted/local web navigation is behaving correctly again.
- The remaining shell uncertainty is no longer basic routing; it is native drawer language sync after changing the app language inside Settings.

### Still Open

- Monthly Items still need real-life testing with salary/social security edge cases.
- Monthly Items may still need an explicit entitlement due date field beyond entitlement month + actual payment date.
- Universal Search is still a planned idea, not an implemented feature yet.
- Camera capture / mobile scan is still a planned idea, not an implemented feature yet.
- Cloud first-login behavior now preserves local data safely, but still needs real-world testing across localhost vs hosted beta to confirm the user experience feels clear and not confusing.
- The iPhone beta shell still needs mobile-app polish:
  - reduce leftover Streamlit chrome where possible
  - keep confirming final section routing from the native drawer after more real-device testing
  - decide how much of the current web UI should stay visible in the beta wrapper
- The iPhone beta shell still has one active bug under direct testing:
  - if the app starts in English and the user changes language to Arabic inside Settings, the web content can become Arabic while the native drawer/sidebar remains English
  - this is currently the top active mobile-shell bug

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
- Salary slips, social security screenshots, invoices, and payment proofs should ideally be attachable directly to the related transaction so the user can find them later from Account search.

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

Best for:

- Long-lived company papers
- Government documents
- Licenses
- Contracts
- Renewals

Not every proof must start here. Short-term/payment proof can begin inside Account and still remain searchable later.

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
- Keep Account search and Documents search separate; do not merge them into one cross-section search by default.
- Documents should stay focused on company/admin papers, not be modeled around salary or social-security workflows.

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
  Latest engineering attempts on 2026-04-28:
  - widened frame-chain cookie/localStorage bootstrap
  - added a dedicated browser-storage bridge fallback
  - changed remembered sign-in success flow to persist browser auth first, then reload instead of depending on an immediate rerun
  - added a localhost-only remembered-auth fallback so local development can persist sign-in separately from hosted browser behavior
  Both still need real deployed Safari verification.
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

- iPhone beta shell native drawer language can remain English after switching the app language to Arabic from inside Settings.
  Current status: still open after multiple shell-side language-detection patches.
  What is confirmed so far:
  - localhost web navigation is fixed
  - hosted beta web navigation is fixed
  - the remaining issue is specifically in the native iPhone drawer language sync, not the hosted web sidebar itself
  Latest engineering attempts on 2026-05-04:
  - preserved `page`, `f_shell`, and `f_lang` more carefully for shell navigation
  - posted explicit language messages from the page through `floosyBridge`
  - watched DOM mutations, history changes, and `f_lang` URL changes from the shell
  - changed the shell to prefer visible/explicit page language before stale query-param language
  - carried the detected live language into native section navigation URLs
  - one later attempt regressed the app and was rolled back immediately
  - a smaller follow-up patch then reapplied only two behaviors:
    - carry the detected live language during native section navigation
    - switch native drawer side based on the current app language
  Latest verification:
  - build succeeded after the newest `ContentView.swift` update
  - final real-device/user confirmation is still pending

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
- Search quickly inside Documents only
- Add renewal dates
- Add categories
- Attach proof
- Add mobile camera capture / scan so the user can create a document directly from camera without separate manual upload first
- Do not design Documents around salary slips or social security receipts; those belong to Account / Monthly Items flow and its own search

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

### iPhone Beta Shell

Keep documenting mobile-wrapper behavior separately from general web bugs:

- Confirm native drawer language follows the currently visible page language every time
- Confirm first app launch language is correct
- Confirm language change from Settings updates both page content and native drawer labels
- Reduce leftover Streamlit chrome only after the language-sync bug is solved

## 10. Next Work Plan

Recommended order:

1. Finish the iPhone beta shell native drawer language bug so Arabic page state and Arabic drawer labels stay in sync.
2. Confirm the shell behavior on first launch, after Settings language changes, and after opening/closing the drawer repeatedly.
3. Test Monthly Items with real social security/salary/delayed income examples.
4. Fix Dashboard Smart Summary based on the new entitlement logic.
5. Organize Documents for company papers.
6. Review Projects linked-account edge cases.
7. Do light UI polish only after behavior is stable.
8. Keep `GoushFi` as the approved current app name, but delay any full logo/identity polish until app packaging / pre-Apple preparation.

## 11. Future Ideas

### Case Folder / ملف حالة

A future feature that groups:

- Related transactions
- Documents
- Important dates
- Notes
- Proofs

Useful for company/admin cases where the user needs to quickly answer: "Where is my proof?"

### Search Strategy / استراتيجية البحث

Preferred direction now:

- Keep a dedicated search inside Account for transactions, Monthly Items, proofs, names, and payment clues related to money activity.
- Account category filtering should show the full canonical category list, not only categories already used in the currently visible month.
- Keep a separate search inside Documents for company papers, document titles, renewal files, and admin records.
- Do not merge both searches into one universal cross-section search by default.

### Camera Capture / تصوير أو سكان مباشر

A future feature that lets the user scan or photograph a paper directly from mobile camera and save it into Floosy without a separate manual upload flow first.

Preferred use:

- As an attachment flow inside Account transactions and Monthly Items
- Also usable from Documents for long-lived company papers

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
