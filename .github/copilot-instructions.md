```instructions
# Copilot Instructions (Floosy)

This project uses Arabic and English UI labels. The app is a single-process Streamlit application whose runtime state is stored in `st.session_state` and persisted to `data/floosy_data.json`.

Keep these core rules front-and-center when editing or generating code for this repo:
- Keep UI changes bilingual (Arabic + English). Pages use a tiny helper t(ar, en) decided from `st.session_state.settings['language']` — preserve both strings.
- Never create automatic financial transactions without an explicit UI action and user confirmation. Financial writes must use repository APIs (`repositories/session_repo.py`).
- Make small, incremental edits. If a session key or persisted shape changes, add an explicit migration in `config_floosy.import_app_state_payload()`.
- Preserve CSS and Streamlit lifecycle assumptions in `config_floosy.py` — UI relies on styles injected at init.

Quick map (what to open first):
- Entry / routing: `app.py` (page selection, month selection, cloud sync trigger)
- Session & persistence: `config_floosy.py` (PERSIST_KEYS, init_session_state, save/load helpers)
- Concrete storage interface: `repositories/session_repo.py` (reads/writes `st.session_state`)
- Repository protocol: `repositories/base.py` (FlossyRepository) — used by services
- Read-only analysis: `services/financial_analyzer.py` (accepts a FlossyRepository)
- Cloud sync: `services/supabase_sync.py` (Supabase REST helpers; optional)
- UI pages: `pages_floosy/*.py` (each exposes a `render(...)` entrypoint the app calls)

Run & debug
- Install deps: pip install -r requirements.txt
- Run: streamlit run app.py
- Secrets for Supabase (optional): provide `SUPABASE_URL` and `SUPABASE_ANON_KEY` either via Streamlit `secrets` or environment variables. `SupabaseSyncClient.from_runtime(getattr(st, 'secrets', None))` reads these.

Data model & persistence details (must-follow)
- Runtime state: `st.session_state` holds keys listed in `config_floosy.PERSIST_KEYS`: `settings`, `transactions`, `savings`, `project_data`, `recurring`, `documents`, `plan_info`.
- Persisted snapshot: `data/floosy_data.json`. Use `save_persistent_state()` and `load_persistent_state()` to read/write. These functions create a compact snapshot and avoid unnecessary writes by comparing snapshots.
- Binary blobs (profile images) are encoded as {"__bytes_b64__": "..."} via `_encode_for_json` / `_decode_from_json`. Use `export_app_state_payload()` / `import_app_state_payload()` for cloud sync compatibility.

Conventions and patterns to follow
- Bilingual labels: always provide both Arabic and English text where present. See `app.py` and `pages_floosy/dashboard_page.py` for examples.
- UI entrypoints: pages expose `render(month_key, month, year)` except settings/documents which may just `render()` and call `save_persistent_state()` afterwards.
- Repository usage: code that changes state should call into `SessionStateRepository` (see `repositories/session_repo.py`) rather than mutating `st.session_state` directly. This centralizes shape, migrations and legacy handling (e.g., `mustndaty_documents`).
- Analysis services are read-only: `FinancialAnalyzer` must not write state — it expects a `FlossyRepository`.
- Recurring templates are stored under `st.session_state['recurring']['items']` and must remain separate from monthly `transactions` entries.

Integration points
- Supabase sync (optional): `services/supabase_sync.py` supports signup/signin/upsert/fetch/delete. Cloud sync in `app.py` is gated by `settings['cloud_sync_enabled']` and `cloud_auth.logged_in`.
- No other external DBs; all persistent data is local JSON unless Supabase is configured.

Concrete examples (copyable patterns)
- Read transactions for a month (use repo):
  repo = SessionStateRepository()
  txs = repo.list_transactions(month_key)

- Add a transaction (UI action required):
  repo.add_transaction(month_key, tx)  # tx should be a Transaction model or dict converted with Transaction.from_dict/to_dict

- Export payload for cloud sync:
  payload = export_app_state_payload()
  client.upsert_user_data(user_id, access_token, payload)

AI editing rules (do not change silently)
- Avoid module-level side-effects that mutate `st.session_state` during import. Streamlit re-runs top-to-bottom; heavy imports or writes at import time break the app flow.
- When changing persisted data shapes, update `import_app_state_payload()` to migrate legacy keys (examples exist for documents/mustndaty_documents and project legacy shapes).
- Tests & build: there are no unit tests in the repo now — if adding tests, prefer small, fast pytest tests focused on services (FinancialAnalyzer) and repository logic.
- Keep changes incremental and reversible. If a UI change adds new session keys, initialize them in `config_floosy.init_session_state()`.

Files to inspect for idiomatic patterns
- `app.py` — main router, month selection, cloud sync safety checks
- `config_floosy.py` — session lifecycle, encoding helpers, CSS and persistence gates
- `repositories/session_repo.py` — canonical read/write patterns for Transaction, Document, Project, RecurringItem
- `services/financial_analyzer.py` — many real-world data-shaping helpers and examples of safe read-only computations
- `services/supabase_sync.py` — how Supabase is called and how responses are handled
- `pages_floosy/dashboard_page.py` — a practical page showing repo + analyzer + UI interactions and bilingual patterns

If anything is unclear or you want this shortened into a checklist for PR reviews or for generating PR templates, tell me which format you prefer and I'll iterate.
```

