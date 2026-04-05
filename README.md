# Floosy

Floosy is a bilingual Streamlit beta for personal finance, projects, invoices, documents, savings, and optional cloud sync.

## Local Run

1. Create and activate a Python 3.12 environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add local secrets in `.streamlit/secrets.toml` if you want cloud sync.
4. Start the app:

```bash
streamlit run app.py
```

## Beta Deploy

Recommended path: Streamlit Community Cloud.

### Before you deploy

- Push this project to GitHub.
- Keep `.streamlit/secrets.toml` local only. It is ignored by git.
- Add your Supabase values in the deployment platform's secrets manager.
- App entrypoint: `app.py`
- Python runtime: `3.12.3`

### Required secrets for cloud sync

Use these keys in Streamlit Community Cloud secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-supabase-anon-key"
SUPABASE_DATA_TABLE = "user_app_data"
```

### Important beta note

This app uses local SQLite/JSON persistence for local runs. On hosted Streamlit deployments, local filesystem storage should be treated as non-durable. For real beta usage, users should enable cloud sync and sign in so their data is stored in Supabase.

## Streamlit Community Cloud Checklist

1. Create a new app from your GitHub repo.
2. Set the main file path to `app.py`.
3. Add the three Supabase secrets above in the app settings.
4. Deploy and test:
   - open app
   - sign up / sign in
   - enable cloud sync
   - save and load user data

## Files Added For Deployment

- `requirements.txt`: pinned Python dependencies
- `runtime.txt`: Python version
- `.streamlit/config.toml`: hosted-friendly Streamlit config
- `.streamlit/secrets.example.toml`: secrets template
- `.gitignore`: protects local secrets and local data files

