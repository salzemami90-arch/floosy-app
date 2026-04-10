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

By default the Playwright smoke test targets:

```text
http://127.0.0.1:8501
```

You can override it with:

```bash
FLOOSY_BASE_URL=http://127.0.0.1:8501 pytest -q e2e_tests
```

## 3. What the smoke test checks

- welcome gate appears
- English mode can start successfully
- sidebar loads
- Account page opens
- Add New Transaction expander is visible
- Transactions table is visible

## 4. Good next E2E scenarios

- add transaction and confirm it appears in Account
- switch language and confirm page labels update
- check Monthly Items panel opens and closes correctly
- verify responsive behavior on smaller viewports
- verify Documents add dialog remains scrollable on short screens
