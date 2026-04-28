
# 🎧 Customer Support Assistant

A full-stack AI agent that combines **Retrieval-Augmented Generation (RAG)** with real-world tool calling. It answers questions from a local knowledge base, schedules real Google Calendar meetings, and sends real emails via Gmail — all through a conversational Streamlit interface.

---

## What It Does

| Capability | Description |
|---|---|
| 💬 **Q&A** | Answers questions by searching a local vector knowledge base (ChromaDB) |
| 📅 **Calendar** | Creates real Google Calendar events with Google Meet links |
| 📧 **Email** | Sends real emails via Gmail OAuth2 |
| 📚 **KB Manager** | Browse, add, edit, search and export knowledge base documents in-app |
| 🧠 **Thought Chain** | Shows step-by-step reasoning: KB search → tool selection → execution |
| 🔗 **Citations** | Every answer links back to the source document chunk it used |

---

## How It Works

```
You (Streamlit UI)
       │
       ▼
  Agent Orchestrator
       ├── 1. Embed your query  →  ChromaDB vector search  →  retrieve top-k chunks
       ├── 2. LLM reasons over query + context  (GPT-4o or Claude)
       ├── 3. If action needed  →  call tool
       │         ├── create_calendar_event  →  Google Calendar API
       │         └── send_email             →  Gmail API
       └── 4. Return answer with citations + tool results
```

**Key components:**

- **ChromaDB** — local persistent vector database (no cloud required, stored in `./chroma_db/`)
- **OpenAI `text-embedding-3-small`** — embeds documents and queries for semantic search
- **GPT-4o / Claude 3.5 Sonnet** — reasoning and tool calling
- **SQLite** — document metadata registry (titles, tags, sources) stored alongside ChromaDB
- **Gmail + Calendar OAuth2** — real API calls using your personal Google account

---

## Project Structure

```
agentic_rag/
│
├── streamlit_app.py              ← Main app (chat UI + KB panel)
├── requirements.txt
├── pytest.ini                    ← Test configuration
├── .env.example                  ← Copy this to .env
│
├── app/
│   ├── agents/
│   │   ├── orchestrator.py       ← RAG + LLM reasoning loop
│   │   └── tools/
│   │       ├── base.py           ← Tool interface
│   │       ├── calendar_tool.py  ← Google Calendar integration
│   │       ├── email_tool.py     ← Gmail integration
│   │       └── registry.py       ← Tool dispatcher
│   │
│   ├── config/
│   │   ├── settings.py           ← Env-based configuration
│   │   ├── database.py           ← ChromaDB wrapper
│   │   ├── kb_registry.py        ← SQLite document metadata store
│   │   └── gmail_auth.py         ← OAuth2 auth for Gmail + Calendar
│   │
│   ├── data/
│   │   └── default_documents.py  ← Built-in knowledge base documents
│   │
│   ├── services/
│   │   ├── embedding.py          ← OpenAI embedding service
│   │   ├── chunker.py            ← Text chunking
│   │   └── rag.py                ← Seeding pipeline
│   │
│   └── schemas/
│       └── tool_schemas.py       ← LLM function-calling definitions
│
├── pages/
│   └── 1_📚_Knowledge_Base.py    ← Full KB management page
│
├── tests/
│   ├── conftest.py
│   ├── test_tier1_retrieval.py   ← RAG retrieval tests
│   ├── test_tier2_reasoning.py   ← LLM reasoning tests
│   └── test_tier3_tools.py       ← Tool execution tests
│
├── credentials/                  ← Google OAuth files (gitignored)
│   ├── SETUP.md                  ← Detailed Google setup guide
│   ├── oauth_credentials.json    ← You create this (Step 4 below)
│   └── gmail_token.json          ← Auto-created on first auth
│
└── chroma_db/                    ← Local vector store (auto-created)
```

---

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or higher** — check with `python --version`
- **An OpenAI API key** — get one at [platform.openai.com](https://platform.openai.com) (GPT-4o access required)
  - *Or* an **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)
- **A Google account** — for Gmail and Calendar features (optional but recommended)
- **Git** — to clone the repo

---

## Quick Start (Chat Only, No Google Tools)

If you just want to run the Q&A assistant without Gmail or Calendar, this takes under 2 minutes.

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/agentic-rag.git
cd agentic-rag
```

### Step 2 — Create a virtual environment

**Mac / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⏱ This takes 1–3 minutes. ChromaDB has several sub-dependencies.

### Step 4 — Configure your API key

Copy the example environment file:

```bash
# Mac / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Open `.env` in any text editor and fill in your API key:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
```

> If you prefer Anthropic Claude instead:
> ```env
> AI_PROVIDER=anthropic
> ANTHROPIC_API_KEY=sk-ant-your-key-here
> ```
> Note: An OpenAI key is still needed for embeddings even when using Anthropic for chat.

### Step 5 — Run the app

```bash
python -m streamlit run streamlit_app.py
```

Open your browser at **http://localhost:8501**

The app will automatically detect your API key from `.env`, connect to the AI provider, seed the knowledge base with default documents, and be ready to chat — no extra steps needed.

---

## Setting Up Gmail & Google Calendar (Optional)

This enables the agent to send real emails from your Gmail and create real calendar events. The setup takes about 10 minutes and only needs to be done once.

### Overview

The app uses **OAuth 2.0** — the same login flow you see when apps ask "Sign in with Google". Your credentials are stored locally only and never sent anywhere else.

### Step 1 — Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** (top bar) → **New Project**
3. Give it any name (e.g. `cs-assistant`) → **Create**
4. Make sure the new project is selected in the top bar

### Step 2 — Enable the APIs

1. Go to **APIs & Services → Library**
2. Search for **Gmail API** → click it → click **Enable**
3. Go back to Library → search for **Google Calendar API** → click it → click **Enable**

### Step 3 — Configure the OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Select **External** → **Create**
3. Fill in the required fields:
   - **App name:** `Customer Support Assistant`
   - **User support email:** your Gmail address
   - **Developer contact email:** your Gmail address
4. Click **Save and Continue**
5. On the **Scopes** page — click **Save and Continue** (no changes needed)
6. On the **Test users** page → click **+ Add users** → enter your Gmail address → **Add**
7. Click **Save and Continue** → **Back to Dashboard**

> ⚠️ **Important:** You must add your own Gmail as a test user or you will get an `access_denied` error when authorising.

### Step 4 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: anything you like → **Create**
5. A dialog appears — click **Download JSON**
6. Rename the downloaded file to exactly `oauth_credentials.json`
7. Move it into the `credentials/` folder of this project:

```
credentials/
└── oauth_credentials.json   ← place it here
```

### Step 5 — Authorise (one-time only)

Run this command in your terminal (make sure your virtual environment is active):

```bash
python -m app.config.gmail_auth
```

- A browser tab will open automatically
- Sign in with your Google account
- Click **Allow** on the permissions screen
- Return to the terminal — you should see:

```
✅ Authenticated successfully!
   Sender  : your@gmail.com
   Token   : credentials/gmail_token.json
   Scopes  : gmail.send, calendar
```

**That's it.** The token refreshes automatically — you will never need to do this again unless you delete `gmail_token.json`.

### Step 6 — Restart the app

```bash
python -m streamlit run streamlit_app.py
```

The sidebar will now show **✓ Gmail authenticated** in green. The agent can now send real emails and create real calendar events.

---

## Using the App

### Connecting

1. Open the sidebar (click **›** if collapsed)
2. Choose your AI provider and paste your API key
3. Click **⚡ Connect** — the knowledge base loads automatically

> If you added your API key to `.env`, the app connects and loads automatically on launch with no manual steps required.

### Chatting

Type anything in the chat bar at the bottom. Examples:

**Knowledge Base Q&A:**
```
What's the return policy for items over $200?
What shipping options are available?
How long is a standard consultation?
```

**Schedule a Meeting:**
```
Schedule a product demo for May 20, 2026 at 2pm EST with client@example.com
Book a 30-minute consultation with john@company.com next Tuesday at 10am
```

**Send an Email:**
```
Send me an email summarising our return and shipping policies
Email alice@example.com to confirm the demo we just scheduled
```

### Understanding the Response

Each agent response shows:

- **Thought Chain** — the steps taken: KB search → reasoning → tool call → done
- **Source Chunks** — the exact document snippets used to generate the answer (click to expand)
- **Calendar Card** — for meeting bookings: shows date, time, attendees, and a Join Meeting link
- **Email Card** — for sent emails: shows recipient, subject, body preview, and sent confirmation
- **Citations** — `[chunk_id]` tags showing which KB documents were cited

### Managing the Knowledge Base

The **📚 Knowledge Base** panel on the right side of the screen lets you:

- **Browse** all documents with title, chunk count, tags and preview
- **Add** new documents — paste text, set a title, tags and source URL
- **Edit** existing documents — changes are re-embedded automatically
- **Delete** documents — removes from both ChromaDB and the metadata registry
- **Search** by keyword or vector similarity (semantic search)
- **Export** your entire knowledge base as a JSON file
- **Import** `.txt`, `.md`, or JSON files in bulk

---

## Environment Variables Reference

All configuration lives in `.env`. Copy `.env.example` to get started.

```env
# ── AI Provider (required) ────────────────────────────────────────
AI_PROVIDER=openai              # "openai" or "anthropic"
OPENAI_API_KEY=sk-proj-...      # Required for embeddings + GPT-4o
ANTHROPIC_API_KEY=sk-ant-...    # Required only if AI_PROVIDER=anthropic

# ── Model overrides (optional) ────────────────────────────────────
OPENAI_CHAT_MODEL=gpt-4o                        # default
OPENAI_EMBED_MODEL=text-embedding-3-small       # default
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-20241022 # default

# ── Google (optional) ─────────────────────────────────────────────
GOOGLE_CALENDAR_EMAIL=                          # organiser email shown on invites
```

> Google OAuth credentials are stored as files in `credentials/` — not in `.env`.

---

## Troubleshooting

### `pip` or `streamlit` is not recognised

Your Python Scripts folder is not on your PATH. Use the full module syntax instead:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

### `ModuleNotFoundError: No module named 'google.oauth2'`

The Google packages are not installed. Run:

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### `access_denied` when authorising Google

You have not added your Gmail as a test user. Go to **Google Cloud Console → APIs & Services → OAuth consent screen → Test users**, add your email address, then run:

```bash
python -m app.config.gmail_auth
```

### `Insufficient Permission` error from Google Calendar

Your existing token does not have the Calendar scope (it was authorised before Calendar was added). Fix it by deleting the old token and re-authorising:

```bash
# Mac / Linux
rm credentials/gmail_token.json
python -m app.config.gmail_auth

# Windows
del credentials\gmail_token.json
python -m app.config.gmail_auth
```

### ChromaDB shows 0 vectors after connecting

Click **⚡ Connect** again — the knowledge base seeds automatically. If it still shows 0, check that your OpenAI API key is valid (embedding requires an active key with billing enabled).

### The app starts but the sidebar says "○ Agent disconnected"

Your API key was not loaded from `.env`. Make sure:
1. The file is named exactly `.env` (not `.env.txt` or `.env.example`)
2. There are no spaces around the `=` sign: `OPENAI_API_KEY=sk-...` ✅
3. You restarted the Streamlit app after editing `.env`

---

## Security & Privacy

- **Your API keys** are stored locally in `.env` only — never sent to any server other than OpenAI/Anthropic
- **`gmail_token.json`** contains a Google refresh token — keep it private and never commit it to git (already in `.gitignore`)
- **`oauth_credentials.json`** is your Google app's client secret — also gitignored
- The OAuth token grants only `gmail.send` + `calendar` scopes — it **cannot** read your emails or calendar entries
- ChromaDB data is stored locally in `./chroma_db/` — nothing leaves your machine

---

## Requirements

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.35 | Web UI |
| `openai` | ≥ 1.35 | Embeddings + GPT-4o |
| `anthropic` | ≥ 0.30 | Claude (optional) |
| `chromadb` | ≥ 0.5 | Local vector database |
| `pydantic` | ≥ 2.0 | Settings validation |
| `pydantic-settings` | ≥ 2.0 | `.env` loading |
| `google-api-python-client` | ≥ 2.100 | Gmail + Calendar APIs |
| `google-auth` | ≥ 2.22 | Google credential handling |
| `google-auth-oauthlib` | ≥ 1.1 | OAuth2 browser flow |
| `google-auth-httplib2` | ≥ 0.1 | HTTP transport for Google APIs |

---

## Running the Tests

The project ships with a tiered test suite under `tests/`:

```bash
pytest                          # run all tests
pytest tests/test_tier1_retrieval.py   # RAG retrieval only
pytest tests/test_tier2_reasoning.py   # LLM reasoning only
pytest tests/test_tier3_tools.py       # tool execution only
```

> Tier 2 and Tier 3 tests call real LLM and Google APIs by default. Make sure your `.env` and OAuth credentials are set up before running them, or skip with `pytest tests/test_tier1_retrieval.py` for offline checks.
