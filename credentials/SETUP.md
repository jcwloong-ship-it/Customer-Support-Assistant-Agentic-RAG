# Gmail OAuth2 Setup for jcw.loong@gmail.com

This guide connects the Customer Support Assistant agent to **jcw.loong@gmail.com** so it can
send real emails. The setup takes about 5 minutes and only needs to be done once.

---

## Step 1 — Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **Select a project** → **New Project**
3. Name it `agentic-rag` → **Create**

---

## Step 2 — Enable Gmail API and Calendar API

1. In the project, go to **APIs & Services → Library**
2. Search for **Gmail API** → click it → **Enable**
3. Go back to Library, search for **Google Calendar API** → click it → **Enable**

---

## Step 3 — Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** → **Create**
3. Fill in:
   - App name: `Customer Support Assistant`
   - User support email: `jcw.loong@gmail.com`
   - Developer contact: `jcw.loong@gmail.com`
4. Click **Save and Continue** through Scopes (no changes needed)
5. On **Test users** → **Add users** → add `jcw.loong@gmail.com`
6. **Save and Continue**

---

## Step 4 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: `Customer Support Assistant Desktop`
5. Click **Create**
6. Click **Download JSON**
7. Rename the downloaded file to **`oauth_credentials.json`**
8. Move it to: `credentials/oauth_credentials.json`

---

## Step 5 — Authorise (one-time browser consent)

```bash
python -m app.config.gmail_auth
```

- A browser tab opens asking you to sign in with Google
- Sign in as `jcw.loong@gmail.com`
- Click **Allow**
- The terminal prints: `✅ Authenticated! Sender address: jcw.loong@gmail.com`
- A token is saved at `credentials/gmail_token.json`

**After this step, no more browser popups** — the token refreshes automatically.

---

## File Checklist

```
credentials/
├── oauth_credentials.json   ← downloaded in Step 4
└── gmail_token.json         ← created automatically in Step 5
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `oauth_credentials.json not found` | Complete Steps 4 & 5 |
| `Access blocked: ... has not completed the Google verification process` | Add your email as a test user (Step 3, point 5) |
| `Token expired` | Delete `gmail_token.json` and run Step 5 again |
| App not in published state | This is normal for personal use — test users bypass it |

---

## Security Notes

- `gmail_token.json` contains a refresh token — keep it private
- Both credential files are excluded from git via `.gitignore`
- The token only grants `gmail.send` scope — it cannot read your email
