# GoushFi Beta 2 Context

Last updated: 2026-05-13 (GoushFi final polish / hosted UI sync)

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

---

## Change Log — 2026-05-13: GoushFi Final Polish, Cursor UI Fixes, Hosted Sync

### Current product baseline
- Final app name: **GoushFi**.
- Final tagline: **Flow · Control · Growth**.
- User explicitly confirmed: do not assume old bugs or old project problems unless they are reintroduced during current testing.
- Devin's heavy engineering work is considered the trusted baseline.
- Current Codex scope is only final polish, testing, and launch checklist support.
- Cursor/localhost work is treated as small UI polish and cleanup layered on top of Devin's baseline, not a full rebuild.

### Context from user
- Devin completed the major PRs and main bug work.
- Xcode work is considered complete for now.
- A new Xcode/mobile-related local folder exists, but it is not part of the current hosted Streamlit deploy unless explicitly requested.
- Cursor had done UI work on localhost, including logo/header polish, but some small adjustments were incomplete or visually off.
- User wants work handled one item at a time and only after confirming the exact intent.

### UI changes completed
1. Dashboard header brand layout:
   - Fixed the dashboard header so `GoushFi` and `Flow · Control · Growth` stay on the left side of the header band.
   - Kept the built-in GoushFi logo on the right side.
   - Forced the header's brand row to LTR so Arabic/RTL page direction does not reverse the brand composition.
   - Kept regular page text and sidebar behavior RTL where appropriate.

2. Header placement and logo size:
   - Raised the dashboard header upward for tighter first-screen spacing.
   - Increased the built-in header logo size further per user preference.
   - Current desktop header logo CSS uses an `80px` logo slot.
   - Current small-screen header logo CSS uses a `65px` logo slot.
   - User saw the logo and chose to keep the larger size for now, even though it appears visually strong.

3. Collapsed sidebar layout:
   - Fixed the collapsed sidebar state so it no longer reserves an empty column.
   - When `[data-testid="stSidebar"][aria-expanded="false"]`, the sidebar width is forced to zero with:
     - `min-width: 0`
     - `width: 0`
     - `max-width: 0`
     - `flex: 0 0 0`
     - `padding: 0`
     - `border: 0`
     - `overflow: hidden`
   - This is intended to let the main page expand when the sidebar is closed.

### Files changed for this polish
- `config_floosy.py`
  - Header LTR brand composition in `_apply_language_direction_theme()`.
  - Header title/tagline left alignment regardless of Arabic page direction.
  - Collapsed sidebar zero-width behavior.
  - Header margin and logo slot sizing.
- Prior Cursor polish already included changes in:
  - `app.py`
  - `goushfi_logo.png`
  - `pages_floosy/dashboard_page.py`
  - `pages_floosy/settings_page.py`
  - `requirements.txt`

### Hosted deploy / Git state
- Local polish branch: `cursor/ui-polish-header-logo-sidebar`.
- Final hosted branch pushed: `main`.
- GitHub remote: `origin https://github.com/salzemami90-arch/floosy-app.git`.
- Commit created for the final local header/sidebar polish:
  - `26ba297 Polish GoushFi header and sidebar layout`
- Merge commit pushed to hosted branch:
  - `f0e9939 Merge GoushFi UI polish for hosted`
- `origin/main` now points to `f0e9939`.
- Streamlit hosted URL checked with `curl -I https://goush-beta.streamlit.app/`; it returned HTTP `303` to Streamlit auth, meaning the hosted app endpoint is reachable but may require Streamlit auth/session.

### Merge/conflict note
- `origin/main` had Devin updates after the Cursor polish branch.
- Most important Devin update: removal of the old hosted data warning banner from `app.py`.
- During merge, `app.py` conflicted because the Cursor branch still had hosted warning helper code.
- Conflict was resolved in favor of Devin's latest behavior:
  - Do **not** restore the old hosted warning banner.
  - Keep Devin's removal of that warning.
  - Keep the Cursor/GoushFi UI polish.

### Verification performed
- `python3 -m py_compile config_floosy.py pages_floosy/dashboard_page.py`
- `python3 -m py_compile config_floosy.py`
- `python3 -m py_compile app.py config_floosy.py pages_floosy/dashboard_page.py pages_floosy/settings_page.py`
- Browser visual verification on local Streamlit port `8502`:
  - Header text left, logo right.
  - Larger logo visible.
  - Header raised.
  - Sidebar still visible/open normally.
- Note: local port `8501` showed an import error during testing, likely because it was an older/running Streamlit process. Port `8502` rendered the current working copy correctly.

### Files intentionally NOT pushed
- `.streamlit/config.toml`
  - Has local-only changes:
    - `fileWatcherType = "auto"`
    - `runOnSave = true`
  - These were not included in the hosted merge because they are local development convenience settings.
- Untracked local paths were not pushed:
  - `FLOOSY_PRICING_PLANS.md`
  - `Goush Money Beta/`
  - `data/`
  - `mobile-beta/`
- These should not be assumed deployed or production-ready unless explicitly reviewed and committed later.

### Open follow-up
- User asked to keep writing everything important into this context file.
- Next assistant should read this file first before doing any GoushFi work.
- Continue final polish one item at a time, confirming exact intent before edits when the user is explaining visual/UI issues.

### Follow-up — 2026-05-14: Hosted Sidebar Width
- After Devin's Settings UX PR, user noticed the hosted sidebar looked wider than localhost.
- Root cause was not Devin touching sidebar code; `config_floosy.py` still allowed desktop sidebar width up to `21rem`, while smaller/local viewport states looked calmer at `15rem`.
- Fix direction:
  - Desktop/sidebar base width is now fixed at `16rem`.
  - RTL sidebar override is also fixed at `16rem`.
  - Medium breakpoint remains `15rem`.
  - Mobile breakpoint remains `13rem`.
- This is a style-only fix and should not affect Cloud/Settings data logic.

---

## UX Review — 2026-05-13: Settings / Device Data / Cloud Data

### Source
- Devin/Cursor-style review file downloaded locally:
  - `/Users/shougwaleedalzemami/Downloads/goushfi_settings_ux_review.md`
- User context:
  - Cloud data was deleted two days earlier.
  - Local/device data was not lost.
  - User is currently not signed into Cloud.
  - The app is saving locally, but Settings does not make "saved on this device/browser" obvious enough.
  - User noticed the Cloud options are visible, but the local-device saving status/option is not clear.

### Main UX diagnosis
The cloud system is not necessarily broken; the Settings UX does not clearly explain where data lives:
- Device/browser local save.
- Cloud backup/sync.
- Restore from Cloud.
- Upload current device data to Cloud.
- Delete Cloud copy.
- Clear this device/browser data.

### Critical issue
- The current "تحميل بياناتي / Load My Data" style action can restore from Cloud immediately.
- This is dangerous because restoring from Cloud can replace all local/device data.
- Before launch, restoring from Cloud should require a clear confirmation checkbox or equivalent confirmation UI.
- Suggested concept:
  - Arabic: `تنبيه: الاستعادة من السحابة ستستبدل كل البيانات على هذا الجهاز بالنسخة السحابية. أي بيانات محلية لم ترفعها للسحابة ستضيع.`
  - English: `Warning: Restoring from Cloud will replace all data on this device with the cloud copy. Any local data not uploaded to Cloud will be lost.`

### Settings structure recommendation
Recommended direction before launch:
- Keep `عام / General` mostly as-is.
- Merge current `Privacy` and `Cloud` concepts into a clearer data-focused tab such as:
  - Arabic: `بياناتي`
  - English: `My Data`
- The new data tab should contain:
  1. Large visual status card: where data is saved right now.
  2. Cloud section: enable Cloud, sign in/out, upload to Cloud, restore from Cloud.
  3. Device section: clear this device/browser data.
  4. Backup section: export JSON, restore/import JSON.
  5. Sensitive/Danger section: delete account / destructive actions.

### Data status card recommendation
Add a prominent status card near the top of Settings/My Data:
- Device only:
  - Arabic: `بياناتك محفوظة على هذا الجهاز فقط. لو مسحت المتصفح أو غيرت جهاز قد تفقد البيانات.`
  - English: `Your data is saved on this device only. Clearing the browser or switching devices may lose it.`
- Device + Cloud:
  - Arabic: `بياناتك محفوظة على هذا الجهاز + نسخة بالسحابة.`
  - English: `Your data is saved on this device + a cloud copy.`
- Cloud enabled but not signed in:
  - Arabic: `السحابة مفعلة لكنك غير مسجل دخول. بياناتك محفوظة على هذا الجهاز حاليًا.`
  - English: `Cloud is enabled, but you are not signed in. Your data is currently saved on this device.`

### Suggested button label improvements
- `تحميل بياناتي` should become:
  - Arabic: `استعادة من السحابة`
  - English: `Restore from Cloud`
- `حفظ بياناتي` should become:
  - Arabic: `رفع للسحابة`
  - English: `Upload to Cloud`
- `حذف بياناتي السحابية` should become:
  - Arabic: `حذف النسخة السحابية`
  - English: `Delete Cloud Copy`
- `حذف بيانات هذا الجهاز` should become:
  - Arabic: `مسح بيانات هذا الجهاز`
  - English: `Clear This Device Data`
- `تسجيل خروج` should become:
  - Arabic: `تسجيل خروج من السحابة`
  - English: `Sign Out from Cloud`

### Things to preserve
- Keep deletion confirmation checkboxes.
- Keep "remember login on this device".
- Keep last sync timestamp.
- Keep JSON export/import.
- Keep forgot-password flow.
- Keep current main app sections.
- Keep current usage plan area.
- Keep destructive actions inside a danger/advanced area.
- Do not change auto-sync logic unless a concrete bug is proven.
- Preserve the existing pause/resume cloud sync safety behavior.

### Suggested implementation approach
- Do not rush a broad Settings rewrite.
- First implement the highest-risk safety fix:
  1. Add confirmation before restoring from Cloud.
- Then implement the clarity layer:
  2. Add a clear "where your data is saved" status card.
  3. Rename confusing buttons.
- Then consider reorganizing tabs:
  4. Merge Privacy + Cloud into `My Data / بياناتي` only after the smaller changes are verified.

---

## UX Proposal — 2026-05-13: My Data / بياناتي Tab Wireframe

### Source
- Downloaded local file:
  - `/Users/shougwaleedalzemami/Downloads/goushfi_my_data_tab_ux.md`

### Proposed full order
The proposed long-term Settings structure is:
1. `عام / General`
2. `بياناتي / My Data`
3. `حول / About`

The proposed `بياناتي / My Data` tab order from top to bottom:
1. Status card: `أين بياناتي؟ / Where is my data?`
2. Cloud section.
3. This device data section.
4. Backup JSON section.
5. Collapsed sensitive/danger zone.

### Status card states
The top status card should visually answer where the user's data is saved.

1. Device only:
   - Color concept: light yellow with orange accent.
   - Arabic message: device/browser is auto-saving; Cloud is not enabled; clearing browser data or switching device may lose data.
   - English message: data is auto-saved on this browser only; enable Cloud for a safe copy.

2. Cloud enabled but not signed in:
   - Color concept: light blue with blue accent.
   - Arabic message: device/browser is auto-saving; Cloud is enabled but user has not signed in yet.
   - English message: sign in below to start syncing.

3. Device + Cloud connected:
   - Color concept: light green with green accent.
   - Arabic message: device/browser auto-save is active; Cloud is connected with email and last sync timestamp.
   - English message: data is saved on device and Cloud.

### Proposed Cloud section
Cloud section should include:
- `تفعيل المزامنة السحابية (اختياري) / Enable Cloud Sync (Optional)`
- Sign in/sign up/forgot password flow when not signed in.
- When signed in:
  - Top action row:
    - `استعادة من السحابة / Restore from Cloud`
    - `رفع للسحابة / Upload to Cloud`
  - Secondary/destructive row:
    - `تسجيل خروج من السحابة / Sign Out from Cloud`
    - `حذف النسخة السحابية / Delete Cloud Copy`
- Delete Cloud Copy remains protected by confirmation and should clarify that local data is not affected.

### Restore from Cloud safety
The proposal reinforces that Restore from Cloud must not run immediately.

Expected confirmation UI:
- Arabic: `الاستعادة ستستبدل كل بيانات هذا الجهاز بالنسخة السحابية. أي بيانات محلية لم ترفعها للسحابة ستضيع.`
- English: `Restoring will replace ALL data on this device with the cloud copy. Any local data not uploaded to cloud will be lost.`
- Add checkbox:
  - Arabic: `أفهم وأريد المتابعة`
  - English: `I understand and want to continue`
- Restore button should be disabled until confirmation is checked.

### Device section
`بيانات هذا الجهاز / This Device Data` should explain:
- It clears data from this browser/device only.
- Cloud copy, if any, is not affected.
- Existing confirmation should remain.

### Backup section
`نسخ احتياطي (JSON) / Backup (JSON)` should contain:
- Export JSON.
- Restore/import from JSON.
- Import from JSON should clearly warn that it replaces current device data and should require confirmation.

### Sensitive section
Keep as collapsed expander:
- `منطقة حساسة / Danger Zone`
- Account deletion remains separate and clearly permanent.
- Clarify account deletion removes Cloud account/data but does not necessarily clear local device data.

### Minimum pre-launch implementation from proposal
Recommended minimum now:
1. Add confirmation checkbox before Restore from Cloud.
2. Add top `Where is my data? / أين بياناتي؟` status card.
3. Rename confusing buttons:
   - `تحميل بياناتي` -> `استعادة من السحابة`
   - `حفظ بياناتي` -> `رفع للسحابة`
4. Move Cloud enable toggle into the Cloud area so users do not have to enable Cloud from Privacy and use it elsewhere.

Estimated scope from proposal: about 35 minutes, but still should be implemented carefully and tested because it touches data safety.

### Defer until after launch
- Full merge of Privacy + Cloud into one `My Data / بياناتي` tab.
- Direct conflict-resolution buttons for local-vs-cloud differences.
- New About tab.
- Larger structural movement of all delete actions into one area.

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

### 2026-05-06 (Devin Session 2 — Logo, Languages, Onboarding)

- **Rebranding complete:** Product is now GoushFi everywhere (logo, header, settings, splash screen).
- **Multi-language i18n system** added via `services/i18n.py`:
  - Centralized `make_t()` function replaces all lambda `t` definitions across 10+ files.
  - 450+ translated strings for 7 languages: Arabic, English, Chinese, Korean, Japanese, Indonesian, Malay (Singapore).
  - Backward-compatible `t(ar, en)` signature — all existing calls work unchanged.
  - Language lookup falls back to English when translation is missing.
- **7 supported languages:** العربية (ar), English (en), 中文 (zh), 한국어 (ko), 日本語 (ja), Bahasa Indonesia (id), Bahasa Melayu (ms).
- **RTL direction** only applies to Arabic. All other languages render LTR. Layout uses `is_ltr = _lc != "ar"` (separate from `is_en`).
- **New currencies added:** CNY (¥ - 人民币), KRW (₩ - 원), JPY (¥ - 円), IDR (Rp - Rupiah), SGD (S$ - SGD). All currency maps updated across all 7 page files.
- **Tagline updated** to "Flow · Control · Growth" (consistent across all languages).
- **GoushFi logo** (`goushfi_logo.png`, 256×256, transparent background):
  - Replaces the old "G" letter in the dashboard header with actual logo image.
  - Shows in Settings preview as default when no user-uploaded logo exists.
  - Used in splash screen on first app load.
- **Splash screen** added: Shows GoushFi logo + name + tagline on first visit, fades out after ~2 seconds. Only shows once per session.
- **Welcome Guide** added to dashboard: Shows on first visit if user hasn't set name or added transactions. Guides through 3 steps: set name/currency, add first transaction, view Financial Analyzer. Auto-dismisses when steps completed, or user can click "Skip guide". Translated in all 7 languages.
- **Bug sweep (PR #15):**
  - Removed old Floosy logo (blue F) from Settings.
  - Changed backup filename from `floosy_backup` to `goushfi_backup`.
  - Extracted 3 duplicated auth helpers to shared `services/cloud_state_helpers.py`.
  - Fixed stale `_cloud_sync_last_error` not cleared on account switch.
  - Updated E2E test selectors from "Floosy Settings" to "GoushFi Settings".
- **Language detection** from browser `Accept-Language` header now supports all 7 language codes (ar, en, zh, ko, ja, id, ms).
- **Localized month names** added for all languages (used in sidebar month selector).

### 2026-05-06

- Cloud/data-safety hardening for 1.0 readiness (3 blocker fixes + 1 low-cost improvement):
  - Auto-sync now refreshes the Supabase access token if the current one is older than 50 minutes, preventing silent sync failures after token expiry. If refresh fails, auto-sync pauses and the user is notified.
  - "Save My Data" now checks for meaningful local data before pushing to cloud. If local state is empty or minimal (e.g. after "Delete This Device Data"), the user sees a warning instead of silently overwriting the cloud copy with nothing.
  - Auto-sync failures are no longer silently swallowed. A lightweight caption appears on the Cloud settings tab when the last sync attempt failed, and token refresh failures show a clear warning with recovery instructions.
  - Cloud payloads now include `_schema_version: 1` to future-proof data migrations when the schema evolves.

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

---

## Change Log — 2026-05-06: Financial Analyzer Insight-First Redesign

### What changed
`pages_floosy/assistant_page.py` was restructured from metric-dump (7 collapsed expanders) to insight-first layout.

### New page structure (top to bottom)
1. **Zone A — AI Quick Take:** Hero card powered by `dashboard_brief()`. Shows the single most important financial signal with colored severity, headline, detail sentence, and two summary pills (90-Day Net + Needs Follow-up). Includes `show_spending_note_on_good` override (same as Dashboard). No LLM — pure rule-based cascade.
2. **Thin-data caption:** When `tx_count > 0 and < 5` and `history_month_count < 2`, shows "Limited data — insights will improve as you add more transactions." UI-only guard.
3. **Zone B — 3 Action Cards:** Always visible, never collapsed. This Month (net + delta vs previous), Entitlements (coverage net + overdue/expected counts), 90-Day Outlook (projected net + delta vs last 90 days). Color-coded green/amber/red by value.
4. **Zone C — Upcoming Items table:** Promoted from inside the 90-Day Cash Flow expander to be visible without clicking.
5. **Zone D — Detail expanders:** All 6 original sections (This Month Overview, Entitlements and Coverage, 90-Day Cash Flow, Savings and Projects, Seasonal Expense Behavior, Documents) moved below the fold, collapsed, content unchanged internally. The upcoming-items table was removed from inside the 90-Day expander since it now lives in Zone C.
6. **Zone E — Footer:** Unchanged timestamp.

### New helper functions added
- `_quick_take_theme(status)` — color mapping for Quick Take card (identical to `dashboard_page._summary_theme`)
- `_card_colors(value)` — green/amber/red color set based on numeric value sign
- `_render_action_card(title, value_text, delta_text, net_value, is_en)` — renders a single styled HTML action card

### What was NOT changed
- No service/model/config changes
- No new backend functions
- No LLM integration
- No pricing file changes
- All existing expander content preserved verbatim (just relocated below the fold)
- Bilingual AR/EN behavior preserved including RTL/LTR card alignment

---

## Change Log — 2026-05-06: Monthly Items Edge-Case Fixes

### What changed
Three targeted fixes for Monthly Items, identified during a read-only edge-case audit.

### Fix 1 — 90-day projection no longer double-counts pending recurring items
`services/cash_flow_engine.py` — `_recurring_projection()` now skips months that are already in the item's `pending_entitlements` list. Previously, pending months were counted both in the projected 90-day totals AND in carry_over (via `recurring_coverage()`), causing the same money to appear twice in the Financial Analyzer.

### Fix 2 — "Due Day" label split for income vs expense
`pages_floosy/account_page.py` — The add form and edit form now show "Expected Receipt Day" (`يوم الاستلام المتوقع`) for income items and "Due Payment Day" (`يوم الاستحقاق`) for expense items, instead of the ambiguous "Due/Expected Day" for both.

### Fix 3 — Multi-month pending guidance
`pages_floosy/account_page.py` — When a Monthly Item has more than one pending entitlement month, a calm caption now appears: "X months pending — confirm each separately" (`X أشهر بانتظار التأكيد — أكد كل شهر على حدة`). This prevents users from confirming one month and assuming all are handled.

### What was NOT changed
- No service/model/config architecture changes
- No new data fields or structures
- No pricing file changes
- No changes to Monthly Items confirmation logic or transaction recording
- Bilingual AR/EN behavior preserved

---

## Change Log — 2026-05-06: Monthly Items Historical Backfill (1.0)

### What changed
Added an optional "Last confirmed month" dropdown to the Monthly Items add and edit forms. This fixes a real-life gap where items with unknown history showed only the current month as pending.

### Problem
`_ensure_pending_month()` falls through to `start_key = month_key` when `last_paid_month` is empty, generating only the current month as pending. For pre-existing obligations (salary, rent, subscriptions) added to GoushFi for the first time, this hid all historical missed months.

### Solution — "Last confirmed month" dropdown
- **Add form:** New `st.selectbox` with options: "Starts this month" (default, preserves current behavior) + last 12 months. If user selects a month, it becomes `last_paid_month`, and `_ensure_pending_month()` auto-fills all following months as pending.
- **Edit form:** Same dropdown for existing items. Shows current `last_paid_month` if set, or "Not set" if empty. Changing the value clears `pending_entitlements` so they regenerate correctly on next render.
- **12-month lookback cap:** The dropdown only offers the last 12 months for safety.
- **Bilingual help text:** Both forms include a caption explaining the field's purpose.

### How it works with existing logic
No service/engine changes needed. `_ensure_pending_month(item, month_key)` already checks `last_paid_month` first (line 623–625). If set, `start_key = _shift_month_key(last_paid_month, 1)` generates all months from `last_paid_month + 1` through the current month. The dropdown simply provides a way to set `last_paid_month` at creation time or retroactively.

### What was NOT changed
- No service/model/config changes
- No auto-detection from transaction history
- No guided wizard or multi-step flow
- No pricing file changes
- Bilingual AR/EN behavior preserved

---

## Change Log — 2026-05-11: Cloud Payload Metadata Conflict Fix

### What changed
Cloud conflict snapshots now ignore top-level underscore-prefixed metadata keys such as `_schema_version`.

### Problem
After `_schema_version: 1` was added to exported cloud payloads, older cloud copies without that metadata key could compare differently from an otherwise identical local payload. This could pause auto-import with a false local-vs-cloud conflict even though the user's finance data was the same.

### Solution
`services/cloud_sync_guard.py` now normalizes payloads before snapshot comparison by excluding top-level metadata keys that start with `_`.

### Verification
- Added a regression test proving `_schema_version` alone does not trigger cloud conflict.
- Targeted cloud sync guard tests passed.
- Full test suite passed: `94 passed, 1 skipped`.

---

## Change Log — 2026-05-11: Manual Cloud Token Refresh Fix

### What changed
Manual Cloud actions now refresh the Supabase session before using the stored access token.

### Problem
The auto-sync path already refreshed an expired Supabase access token, but the manual Cloud buttons still used the old `cloud_auth["access_token"]` directly. After the token expired, pressing `Save My Data` could fail with `JWT expired` even though the user was still signed in and the Cloud status looked connected.

### Solution
`pages_floosy/settings_page.py` now refreshes `cloud_auth` before manual Cloud actions:
- `Load My Data`
- `Save My Data`
- `Delete My Cloud Data`
- `Delete Account Permanently`

The refreshed access token and refresh token are written back to session state and the remembered auth cookie when applicable.

### Verification
- Added regression tests for successful manual token refresh and refresh failure handling.
- Targeted cloud tests passed: `13 passed`.

---

## Change Log — 2026-05-11: Settings UX Cleanup

### What changed
Settings kept the same General / Privacy / Cloud structure, but the top area was simplified for 1.0.

### Problem
The Settings page repeated cloud state several times before the user reached the tabs: a status bar, two metric cards, a warning/CTA block, and another storage-location card inside Privacy. The Cloud tab also exposed developer terminology such as Supabase in user-facing headings and messages.

### Solution
- Removed the two top `st.metric` cards and moved Last Sync into the single Cloud Status card.
- Removed the redundant Privacy storage-location card and replaced it with one short caption.
- Changed the Cloud tab heading from "Cloud Account (Supabase)" to "Cloud Account".
- Moved deployment details such as `SUPABASE_URL` and `SUPABASE_ANON_KEY` behind an Advanced setup expander.
- Replaced user-facing Supabase/Auth wording with plain Cloud/account wording.

### What was NOT changed
- No redesign of the tab structure.
- No changes to Load / Save / Sign Out / Delete button layout.
- No changes to the sign-in/sign-up flow.
- No cloud service logic changes.

---

## Change Log — 2026-05-11: Hosted Stale Page Query Fix

### What changed
Regular hosted web links no longer keep a stale `page=...` query parameter forever after it is used as an entry link.

### Problem
During hosted testing, refreshing `goush-beta.streamlit.app` could reopen `Invoices & Tax` instead of Home, while localhost reopened Home. The hosted browser had previously carried a `page=tax` query parameter, and the app correctly treated it as an entry/deep link. However, because the parameter stayed in the URL state, every future refresh kept reopening Tax.

### Solution
- `app.py` still honors a valid `page` query parameter once on first load.
- After a regular web load uses that parameter, `clear_regular_web_page_query_param()` removes it so future refreshes start cleanly.
- Mobile shell links that include `f_shell` still preserve `page`, so native drawer/deep-link behavior is not broken.
- `sync_browser_preferences_state()` no longer preserves stale `page` query params on regular web sessions.

### Verification
- Added regression tests proving regular web clears stale `page` while shell links keep it.
- `python3 -m py_compile app.py config_floosy.py` passed.

---

## Change Log — Bug Sweep & Branding Cleanup

### What changed
1. **Removed old Floosy logo fallback** — `get_logo_bytes()` no longer falls back to `floosy_logo.png`. If the user hasn't uploaded a logo, the preview section shows "No uploaded logo" instead of the old blue F logo.
2. **Renamed backup file** — export filename changed from `floosy_backup_*.json` to `goushfi_backup_*.json`. Metadata source changed from `floosy_settings_backup` to `goushfi_settings_backup`.
3. **Extracted duplicated auth/state functions** — `_set_cloud_auth`, `_set_scope_owner`, `_clear_scoped_finance_state` moved to `services/cloud_state_helpers.py`. Both `app.py` and `settings_page.py` now import from the same source. Eliminates risk of silent divergence.
4. **Fixed `_cloud_sync_last_error` not cleared on account switch** — `clear_scoped_finance_state()` now resets `_cloud_sync_last_error` to `""`, preventing stale error banners after switching cloud accounts.
5. **Updated E2E tests** — `test_smoke_playwright.py` now expects "GoushFi Settings" instead of "Floosy Settings".

### Files changed
- `config_floosy.py` — removed `floosy_logo.png` fallback in `get_logo_bytes()`
- `pages_floosy/settings_page.py` — renamed backup identifiers, replaced local function definitions with imports from shared module
- `services/cloud_state_helpers.py` — new shared module for auth/state helpers
- `app.py` — replaced local function definitions with imports from shared module
- `e2e_tests/test_smoke_playwright.py` — updated branding expectation
- `tests/test_settings_cloud_manual_refresh.py` — updated monkeypatch for shared module

### Verification
- 100/100 tests pass.
- `py_compile` clean on all changed files.
