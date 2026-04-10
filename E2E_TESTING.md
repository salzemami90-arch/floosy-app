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

## 4. What the Playwright suite checks

- English Account smoke flow
- Arabic Account smoke flow
- English Account add-transaction flow
- Arabic Account add-transaction flow
- English Documents add/delete flow
- Arabic Documents add/delete flow

## 5. Good next E2E scenarios

- add transaction and confirm it appears in Account
- switch language and confirm page labels update
- check Monthly Items panel opens and closes correctly
- verify responsive behavior on smaller viewports
- verify Documents add dialog remains scrollable on short screens
