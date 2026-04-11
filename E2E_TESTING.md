# Floosy E2E Testing

Floosy already has `pytest` unit tests in [`tests`](./tests). This file adds a lightweight Playwright path for real browser checks.

## 1. Install dev dependencies

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
```

## 2. Run Floosy locally

```bash
streamlit run app.py
```

By default the Playwright tests target:

```text
http://127.0.0.1:8501
```

You can override it with:

```bash
FLOOSY_BASE_URL=http://127.0.0.1:8501 pytest -q e2e_tests
```

## 3. Recommended clean E2E server

For deterministic browser tests, especially `Documents`, run a clean Streamlit server with local persistence disabled:

```bash
FLOOSY_ENABLE_LOCAL_PERSISTENCE=0 streamlit run app.py --server.headless true --server.port 8502
FLOOSY_BASE_URL=http://127.0.0.1:8502 pytest -q e2e_tests
```

This avoids inherited local `documents` / `transactions` state from earlier localhost sessions.

## 4. Cloud test environments

Use two server modes for Cloud coverage:

```bash
# Configured cloud flow (uses the real project secrets)
FLOOSY_ENABLE_LOCAL_PERSISTENCE=0 streamlit run app.py --server.headless true --server.port 8504
FLOOSY_BASE_URL=http://127.0.0.1:8504 pytest -q e2e_tests

# Setup-required cloud flow (run from a temp copy without .streamlit/secrets.toml)
cd /tmp/floosy-no-secrets
FLOOSY_ENABLE_LOCAL_PERSISTENCE=0 streamlit run app.py --server.headless true --server.port 8506
FLOOSY_BASE_URL=http://127.0.0.1:8506 FLOOSY_EXPECT_CLOUD_CONFIG=0 pytest -q e2e_tests -k requires_setup_without_secrets
```

Important:
- Run the no-secrets server from the temporary copy's own working directory.
- If it runs from the main repo `cwd`, Streamlit can still read the main project's secrets.

## 5. What the Playwright suite checks

- English Account smoke flow
- Arabic Account smoke flow
- English Account add-transaction flow
- Arabic Account add-transaction flow
- English Documents add/delete flow
- Arabic Documents add/delete flow
- Settings language switch flow across pages
- Cloud status flow from disabled to enabled/configured UI
- Cloud setup-required flow on a no-secrets server
- Documents modal usability on a short viewport

## 6. Good next E2E scenarios

- invoices and tax flows
- settings export/restore roundtrip
- check Monthly Items panel opens and closes correctly
- verify responsive behavior on smaller viewports
- validation errors and empty states
