"""
Customer Support Assistant — Warm Light UI
Palette: cream parchment bg · warm gray text · coral/orange accent · teal tool highlights
"""
import os, sys, json
from datetime import datetime
import streamlit as st

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(page_title="Customer Support Assistant", page_icon="🎧",
                   layout="wide", initial_sidebar_state="expanded")

# ════════════════════════════════════════════════════════════════════
# CSS  —  warm parchment palette
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Google+Sans+Text:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── tokens ── */
:root {
  --bg:        #f8f5ef;
  --bg2:       #f2ede4;
  --bg3:       #ebe4d8;
  --surface:   #ffffff;
  --border:    #ddd5c5;
  --border2:   #c9bfad;
  --txt:       #2d2a24;
  --txt2:      #6b6456;
  --txt3:      #9e9080;
  --accent:    #e8572a;
  --accent2:   #f07848;
  --teal:      #1a7f6e;
  --teal2:     #24a896;
  --teal-bg:   #eaf6f4;
  --blue:      #3b6fd4;
  --blue-bg:   #eef2fb;
  --gold:      #c9860a;
  --gold-bg:   #fef7e8;
  --radius:    14px;
  --shadow:    0 2px 12px rgba(80,60,30,.10);
  --shadow-lg: 0 8px 32px rgba(80,60,30,.14);
}

/* ── reset ── */
*, *::before, *::after { box-sizing: border-box; }
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: var(--bg) !important;
  font-family: 'Inter', 'Google Sans Text', sans-serif !important;
  color: var(--txt) !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: var(--shadow) !important;
}
[data-testid="stSidebar"] .stMarkdown p { font-size:.82rem; color:var(--txt2); }

/* ── typography ── */
h1,h2,h3 { font-family:'Inter',sans-serif; letter-spacing:-.02em; color:var(--txt); }
p,li      { line-height:1.65; color:var(--txt); }

/* ── chat bubbles ── */
.user-bubble {
  background: var(--accent);
  background: linear-gradient(135deg, #e8572a, #d44420);
  border-radius: 20px 20px 4px 20px;
  padding: 13px 18px;
  margin: 10px 0 10px 10%;
  color: #fff;
  font-size: .93rem;
  line-height: 1.65;
  box-shadow: 0 4px 16px rgba(232,87,42,.25);
  max-width: 90%;
}
.agent-bubble {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px 20px 20px 4px;
  padding: 16px 20px;
  margin: 10px 10% 10px 0;
  color: var(--txt);
  font-size: .93rem;
  line-height: 1.65;
  box-shadow: var(--shadow);
  max-width: 90%;
}

/* ── thought chain ── */
.thought-chain {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  margin: 8px 0;
  font-size: .82rem;
}
.thought-step {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 5px 0; border-bottom: 1px solid var(--border);
}
.thought-step:last-child { border-bottom: none; }
.step-icon {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px;
}
.step-done   { background: #d4f0ec; color: var(--teal); }
.step-skip   { background: var(--bg3); color: var(--txt3); }
.step-label  { color: var(--txt2); font-size: .80rem; line-height:1.4; }
.step-detail { color: var(--teal); font-size: .76rem; font-family: monospace; margin-top:1px; }

/* ── calendar card ── */
.cal-card {
  background: var(--blue-bg);
  border: 1px solid #c5d5f5;
  border-radius: var(--radius);
  padding: 18px 20px;
  margin: 8px 0;
  position: relative; overflow: hidden;
}
.cal-card::before {
  content:''; position:absolute; top:0; left:0;
  width:4px; height:100%;
  background: linear-gradient(180deg, var(--blue), #2a55b8);
}
.cal-date-big {
  font-size: 1.9rem; font-weight: 700;
  color: var(--blue); letter-spacing: -.03em; line-height: 1.1;
}
.cal-time   { font-size:.93rem; color:#5580d0; margin-top:2px; }
.cal-title-text { font-size:1.05rem; font-weight:600; color:var(--txt); margin:10px 0 4px; }
.cal-att    { font-size:.80rem; color:var(--txt2); }
.join-btn {
  display:inline-block;
  background: linear-gradient(135deg, var(--blue), #2a55b8);
  color:#fff !important; text-decoration:none !important;
  padding:8px 18px; border-radius:8px;
  font-size:.82rem; font-weight:600; margin-top:12px;
  box-shadow:0 2px 8px rgba(59,111,212,.3);
}

/* ── email card ── */
.email-card {
  background: var(--teal-bg);
  border: 1px solid #b5ddd8;
  border-radius: var(--radius);
  padding: 16px 18px; margin: 8px 0;
  font-size:.85rem;
}
.email-header { display:flex; gap:10px; align-items:center; margin-bottom:10px; }
.email-avatar {
  width:38px; height:38px; border-radius:50%;
  background: linear-gradient(135deg, var(--teal), var(--teal2));
  display:flex; align-items:center; justify-content:center;
  font-size:1.05rem; font-weight:700; color:#fff; flex-shrink:0;
}
.email-to   { font-size:.78rem; color:var(--teal); }
.email-subj { font-weight:600; color:var(--txt); font-size:.92rem; }
.email-preview {
  background:#fff; border-radius:8px; padding:10px 12px;
  color:var(--txt2); font-size:.80rem; line-height:1.55;
  border-left:3px solid var(--teal); margin-top:8px;
}
.sent-badge {
  display:inline-flex; align-items:center; gap:5px;
  background:#d4f0ec; color:var(--teal);
  border-radius:6px; padding:4px 12px;
  font-size:.74rem; font-weight:600; margin-top:10px;
}
.error-badge {
  display:inline-flex; align-items:center; gap:5px;
  background:#fde8e8; color:#c0392b;
  border-radius:6px; padding:4px 12px;
  font-size:.74rem; font-weight:600; margin-top:10px;
}

/* ── source chunks ── */
.source-chunk {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--teal);
  border-radius: 8px; padding:10px 14px;
  margin:6px 0; font-size:.80rem; line-height:1.55; color:var(--txt2);
}
.source-id { color:var(--teal); font-weight:600; font-family:monospace; font-size:.76rem; }

/* ── metric chips ── */
.metric-row { display:flex; gap:6px; flex-wrap:wrap; margin:8px 0 4px; }
.chip {
  background:var(--bg2); border:1px solid var(--border);
  border-radius:99px; padding:3px 11px;
  font-size:.73rem; color:var(--txt2);
}
.chip b { color:var(--txt); }
.cite-pill {
  display:inline-block; background:var(--blue-bg); color:var(--blue);
  border:1px solid #c5d5f5; border-radius:99px;
  padding:1px 9px; font-size:.72rem; margin:2px 3px; font-family:monospace;
}

/* ── badges ── */
.badge {
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 10px; border-radius:99px; font-size:.72rem; font-weight:600;
}
.badge-teal   { background:#d4f0ec; color:var(--teal); }
.badge-coral  { background:#fde8e0; color:var(--accent); }
.badge-blue   { background:var(--blue-bg); color:var(--blue); }
.badge-gold   { background:var(--gold-bg); color:var(--gold); }
.badge-gray   { background:var(--bg3); color:var(--txt2); }
.badge-red    { background:#fde8e8; color:#c0392b; }

/* ── KB panel ── */
.kb-doc-row {
  background:var(--bg2); border:1px solid var(--border);
  border-radius:10px; padding:10px 13px; margin:5px 0; font-size:.80rem;
  transition: border-color .15s;
}
.kb-doc-row:hover { border-color:var(--border2); }
.kb-doc-title { font-weight:600; color:var(--txt); font-size:.83rem; }
.kb-doc-meta  { color:var(--txt3); font-size:.73rem; margin-top:2px; }

/* ── sidebar sections ── */
.sbar-section {
  font-size:.68rem; font-weight:700; letter-spacing:.08em;
  text-transform:uppercase; color:var(--txt3); margin:14px 0 5px 2px;
}

/* ── chat input — glassmorphism warm ── */
[data-testid="stChatInput"] {
  background: rgba(255,255,255,.88) !important;
  backdrop-filter: blur(14px) !important;
  border: 1.5px solid var(--border2) !important;
  border-radius: 18px !important;
  box-shadow: var(--shadow-lg) !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: var(--txt) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .93rem !important;
  caret-color: var(--accent) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(232,87,42,.12), var(--shadow-lg) !important;
}

/* ── buttons ── */
.stButton button {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  color: var(--txt2) !important;
  border-radius: 9px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .82rem !important;
  font-weight: 500 !important;
  transition: all .15s !important;
  box-shadow: 0 1px 4px rgba(80,60,30,.08) !important;
}
.stButton button:hover {
  background: var(--bg2) !important;
  border-color: var(--border2) !important;
  color: var(--accent) !important;
}
.stButton button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), #d44420) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(232,87,42,.25) !important;
}

/* ── form inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  color: var(--txt) !important;
  border-radius: 9px !important;
  font-family: 'Inter', sans-serif !important;
  font-size:.88rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(232,87,42,.12) !important;
}

/* ── expanders ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
[data-testid="stExpander"] summary { color:var(--txt2) !important; font-size:.82rem !important; }

/* ── tabs ── */
[data-testid="stTabs"] [role="tablist"] { border-bottom:1.5px solid var(--border) !important; }
[data-testid="stTabs"] [role="tab"] {
  color:var(--txt2) !important; font-size:.82rem !important;
  padding:6px 14px !important; font-family:'Inter',sans-serif !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
  font-weight: 600 !important;
}

/* ── selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: var(--surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 9px !important;
  color: var(--txt) !important;
}

/* ── toggles ── */
[data-testid="stToggle"] { accent-color: var(--accent); }

/* ── divider ── */
hr { border-color: var(--border) !important; margin:12px 0 !important; }

/* ── force sidebar toggle always visible ── */
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
button[kind="header"] {
    display: block !important;
}

/* ── connect banner (shown when not connected) ── */
.connect-banner {
    background: linear-gradient(135deg, #fff8f0, #fff3e0);
    border: 1.5px solid var(--accent);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.connect-banner-text {
    font-size: .88rem;
    color: var(--txt2);
    flex: 1;
    min-width: 200px;
}
.connect-banner-text b { color: var(--txt); }

/* ── compact inline connect form ── */
.inline-connect {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    gap: 10px;
    align-items: flex-end;
    flex-wrap: wrap;
}

/* ── sidebar toggle ── */
[data-testid="collapsedControl"],
[data-testid="baseButton-header"] {
    display: flex !important;
    visibility: visible !important;
}

/* ── scrollbar ── */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border2); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:var(--txt3); }

/* ── container borders ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
}

/* ── quick prompt chips ── */
.stButton button.qp {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 99px !important;
  color: var(--txt2) !important;
  font-size: .80rem !important;
}
.stButton button.qp:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: #fde8e0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────
_DEFAULTS = dict(messages=[], agent=None, emb_service=None, settings=None,
                 api_key="", provider="openai", show_rag=True, show_tools=True,
                 pending_prompt=None)
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-initialise on launch if env key is already set ──────────────────────
def _auto_init():
    """Silently connect + seed on first load if API key is in environment."""
    if st.session_state.agent is not None:
        return  # already connected
    provider_env = os.environ.get("AI_PROVIDER", "openai")
    key_var      = "ANTHROPIC_API_KEY" if provider_env == "anthropic" else "OPENAI_API_KEY"
    env_key      = os.environ.get(key_var, "").strip()
    if not env_key:
        return  # no key in env — user must connect manually
    try:
        s, e, a = _load_services(env_key, provider_env)
        st.session_state.update(settings=s, emb_service=e, agent=a,
                                 api_key=env_key, provider=provider_env)
        _seed_db(e, force=False)  # seed if not already seeded
    except Exception:
        pass  # fail silently — user can connect manually

_auto_init()

# ── Helpers ───────────────────────────────────────────────────────
def _load_services(api_key, provider):
    """
    Configure environment + return (settings, embedding_service, orchestrator).

    Note: the OpenAI API key is required for embeddings regardless of which
    chat provider is selected. We only set the env var for the *selected*
    provider so we don't accidentally clobber an OpenAI key set in .env
    when the user picks Anthropic for chat.
    """
    os.environ["AI_PROVIDER"] = provider
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    else:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    import app.config.settings as _sm; _sm._settings = None
    settings = _sm.get_settings()

    # Embedding always uses the OpenAI key (from this connect form or from .env)
    openai_key = api_key if provider == "openai" else os.environ.get("OPENAI_API_KEY", "")
    from app.services.embedding import EmbeddingService
    emb = EmbeddingService(api_key=openai_key)

    from app.agents.orchestrator import AgentOrchestrator
    from app.config.database import db
    return settings, emb, AgentOrchestrator(settings, db, emb)

def _seed_db(emb, force=False):
    from app.services.rag import seed_knowledge_base
    return seed_knowledge_base(emb, force_reseed=force)

def _chroma_count():
    from app.config.database import db; return db.count()

def _kb_docs(query=""):
    from app.config.kb_registry import get_all_documents, search_documents
    return search_documents(query) if query.strip() else get_all_documents()

def _kb_stats():
    from app.config.kb_registry import get_stats; return get_stats()

def _gmail_status():
    try:
        from app.config.gmail_auth import check_auth_status
        return check_auth_status()
    except Exception:
        return {"token_valid": False, "oauth_file_exists": False}

def _parse_dt(iso):
    try:
        dt = datetime.fromisoformat(iso.replace("Z",""))
        return dt.strftime("%a, %b %-d"), dt.strftime("%-I:%M %p")
    except Exception:
        return iso[:10], iso[11:16]

# ── Rich tool cards ───────────────────────────────────────────────
def _calendar_card(result):
    r = result.get("result") or {}
    summary  = r.get("summary","Meeting")
    start    = (r.get("start") or {}).get("dateTime","")
    end      = (r.get("end")   or {}).get("dateTime","")
    tz       = (r.get("start") or {}).get("timeZone","UTC")
    atts     = r.get("attendees",[])
    link     = r.get("meet_link") or r.get("event_link","#")
    eid      = r.get("event_id","")
    date_s, st_t = _parse_dt(start)
    _,       en_t = _parse_dt(end)
    att_s = ", ".join(atts[:3]) + ("…" if len(atts)>3 else "")
    st.markdown(f"""
<div class="cal-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="cal-date-big">📅 {date_s}</div>
      <div class="cal-time">🕐 {st_t} — {en_t} &nbsp;·&nbsp; {tz}</div>
    </div>
    <span class="badge badge-blue">Calendar Event</span>
  </div>
  <div class="cal-title-text">{summary}</div>
  {"<div class='cal-att'>👥 " + att_s + "</div>" if att_s else ""}
  <a class="join-btn" href="{link}" target="_blank">🎥 Join Meeting</a>
  <div style="font-size:.69rem;color:#9aabbf;margin-top:8px">Event ID: {eid}</div>
</div>""", unsafe_allow_html=True)

def _email_card(result):
    r = result.get("result") or {}
    success  = result.get("success", False)
    to       = r.get("to","")
    subject  = r.get("subject","")
    frm      = r.get("from","jcw.loong@gmail.com")
    body_txt = r.get("body","")
    mid      = r.get("message_id","")
    error    = result.get("error","")
    avatar   = to[0].upper() if to else "?"
    preview  = body_txt[:220] + ("…" if len(body_txt)>220 else "") if body_txt else ""

    if success:
        badge = "<span class='sent-badge'>✅ Email sent successfully</span>"
    else:
        badge = f"<span class='error-badge'>⚠️ {error}</span>"

    st.markdown(f"""
<div class="email-card">
  <div class="email-header">
    <div class="email-avatar">{avatar}</div>
    <div>
      <div class="email-subj">{subject}</div>
      <div class="email-to">To: {to} &nbsp;·&nbsp; From: {frm}</div>
    </div>
  </div>
  {"<div class='email-preview'>" + preview + "</div>" if preview else ""}
  <div style="margin-top:10px">{badge}
    {"<span style='color:var(--txt3);font-size:.69rem;margin-left:8px'>ID: " + mid + "</span>" if mid else ""}
  </div>
</div>""", unsafe_allow_html=True)

# ── Thought chain ─────────────────────────────────────────────────
def _thought_chain(meta):
    rag   = meta.get("rag_context",[])
    tcs   = meta.get("tool_calls",[])
    trs   = meta.get("tool_results",[])
    cites = meta.get("citations",[])
    tr_map = {r["call_id"]: r for r in trs}

    steps = []
    steps.append(("done" if rag else "skip","🔍",
                  "Knowledge Base search",
                  f"{len(rag)} chunk(s) retrieved" if rag else "No relevant context"))
    steps.append(("done","🧠","Agent reasoning","Query analysed"))
    for tc in tcs:
        r  = tr_map.get(tc["call_id"],{})
        ok = r.get("success",False)
        icon = "📅" if "calendar" in tc["tool_name"] else "📧"
        steps.append(("done" if ok else "skip", icon,
                      f"Tool: {tc['tool_name']}",
                      "✓ Executed successfully" if ok else f"✗ {r.get('error','')}"))
    if cites:
        steps.append(("done","📎","Citations extracted",
                      ", ".join(cites[:3]) + ("…" if len(cites)>3 else "")))
    steps.append(("done","✅","Response ready",""))

    html = "<div class='thought-chain'>"
    for state, icon, label, detail in steps:
        html += (f"<div class='thought-step'>"
                 f"<div class='step-icon step-{state}'>{icon}</div>"
                 f"<div><div class='step-label'>{label}</div>"
                 + (f"<div class='step-detail'>{detail}</div>" if detail else "")
                 + "</div></div>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def _source_drawer(rag):
    if not rag: return
    with st.expander(f"📚 {len(rag)} source chunk(s) — click to read", expanded=False):
        for chunk in rag:
            sim = chunk.get("similarity",0)
            bar = int(sim*100)
            col = "var(--teal)" if sim>.7 else "var(--gold)" if sim>.4 else "var(--txt3)"
            st.markdown(f"""
<div class="source-chunk">
  <div style="display:flex;justify-content:space-between;margin-bottom:5px">
    <span class="source-id">{chunk['chunk_id']}</span>
    <span style="color:{col};font-size:.75rem">{sim:.1%}
      <span style="display:inline-block;width:52px;height:3px;
             background:var(--bg3);border-radius:2px;
             vertical-align:middle;margin-left:4px">
        <span style="display:block;width:{bar}%;height:3px;background:{col};border-radius:2px"></span>
      </span>
    </span>
  </div>
  {chunk['text'][:280]}{"…" if len(chunk['text'])>280 else ""}
</div>""", unsafe_allow_html=True)

def _render_message(msg):
    role, content, meta = msg["role"], msg["content"], msg.get("meta",{})
    if role == "user":
        st.markdown(f"<div class='user-bubble'>👤 &nbsp;{content}</div>",
                    unsafe_allow_html=True)
        return
    # thought chain
    if st.session_state.show_rag:
        _thought_chain(meta)
    st.markdown(f"<div class='agent-bubble'>🤖 &nbsp;{content}</div>",
                unsafe_allow_html=True)
    lat   = meta.get("latency_ms",0)
    n_rag = len(meta.get("rag_context",[]))
    n_tc  = len(meta.get("tool_calls",[]))
    cites = meta.get("citations",[])
    cpills = "".join(f"<span class='cite-pill'>📎 {c}</span>" for c in cites)
    st.markdown(f"""
<div class="metric-row">
  <span class="chip">⏱ <b>{lat}ms</b></span>
  <span class="chip">📚 <b>{n_rag}</b> chunks</span>
  <span class="chip">🔧 <b>{n_tc}</b> tools</span>
  {"<span class='chip'>" + cpills + "</span>" if cites else ""}
</div>""", unsafe_allow_html=True)
    _source_drawer(meta.get("rag_context",[]))
    tcs    = meta.get("tool_calls",[])
    trs    = meta.get("tool_results",[])
    tr_map = {r["call_id"]: r for r in trs}
    for tc in tcs:
        res = tr_map.get(tc["call_id"],{})
        if "calendar" in tc["tool_name"]: _calendar_card(res)
        elif "email" in tc["tool_name"]:  _email_card(res)
        if st.session_state.show_tools:
            with st.expander(f"🔧 Raw data — {tc['tool_name']}", expanded=False):
                c1,c2 = st.columns(2)
                with c1:
                    st.caption("Arguments"); st.json(tc.get("arguments",{}))
                with c2:
                    st.caption("Result"); st.json(res.get("result") or res.get("error") or {})

# ── Knowledge Base right panel ────────────────────────────────────
def _kb_panel():
    stats = _kb_stats()
    td = stats.get("total_docs",0)
    tc = stats.get("total_chunks",0) or 0
    vc = _chroma_count()

    st.markdown(f"""
<div style="font-size:.92rem;font-weight:700;color:var(--txt);
            letter-spacing:-.01em;margin-bottom:10px">
  📚 Knowledge Base
</div>
<div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap">
  <span class="badge badge-blue">📄 {td} docs</span>
  <span class="badge badge-gray">🧩 {tc} chunks</span>
  <span class="badge {'badge-teal' if vc>0 else 'badge-red'}">⚡ {vc} vectors</span>
</div>""", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["Browse", "Add", "Search"])

    # ── Browse ──────────────────────────────────────────────────────
    with t1:
        docs = _kb_docs()
        if not docs:
            st.markdown(
                "<div style='color:var(--txt3);font-size:.80rem;"
                "text-align:center;padding:20px 0'>"
                "No documents yet.<br/>Seed defaults or add one.</div>",
                unsafe_allow_html=True)
            if st.button("🌱 Load default documents", use_container_width=True, key="kb_seed_b"):
                if st.session_state.emb_service:
                    with st.spinner("Seeding…"):
                        _seed_db(st.session_state.emb_service)
                    st.rerun()
                else:
                    st.warning("Connect first")
        for doc in docs[:15]:
            preview = doc["text"][:95].replace("\n"," ")
            tags_h  = " ".join(
                f"<span style='background:#fde8e0;color:var(--accent);"
                f"border-radius:4px;padding:1px 6px;font-size:.67rem'>{t}</span>"
                for t in doc.get("tags",[])[:3])
            st.markdown(f"""
<div class="kb-doc-row">
  <div class="kb-doc-title">{doc['title']}</div>
  <div class="kb-doc-meta">{doc['chunk_count']} chunks · {doc['added_at'][:10]}</div>
  <div style="color:var(--txt3);font-size:.73rem;margin-top:3px">{preview}…</div>
  {"<div style='margin-top:4px'>" + tags_h + "</div>" if tags_h else ""}
</div>""", unsafe_allow_html=True)
            ce, cd = st.columns(2)
            with ce:
                if st.button("✏️ Edit", key=f"e_{doc['doc_id']}", use_container_width=True):
                    st.session_state[f"editing_{doc['doc_id']}"] = True; st.rerun()
            with cd:
                if st.button("🗑 Del", key=f"d_{doc['doc_id']}", use_container_width=True):
                    from app.services.rag import remove_document
                    remove_document(doc["doc_id"]); st.rerun()
            if st.session_state.get(f"editing_{doc['doc_id']}"):
                with st.form(f"ef_{doc['doc_id']}"):
                    nt = st.text_input("Title", value=doc["title"])
                    ns = st.text_input("Source", value=doc.get("source",""))
                    nx = st.text_area("Text", value=doc["text"], height=130)
                    ss, sc = st.form_submit_button("💾 Save"), st.form_submit_button("Cancel")
                    if ss and st.session_state.emb_service:
                        from app.services.rag import add_document
                        add_document(st.session_state.emb_service,
                                     doc_id=doc["doc_id"],title=nt,source=ns,text=nx)
                        st.session_state.pop(f"editing_{doc['doc_id']}",None); st.rerun()
                    if sc:
                        st.session_state.pop(f"editing_{doc['doc_id']}",None); st.rerun()

    # ── Add ─────────────────────────────────────────────────────────
    with t2:
        with st.form("kb_add_f"):
            did   = st.text_input("ID *", placeholder="returns_policy_v2")
            title = st.text_input("Title *", placeholder="Return Policy")
            src   = st.text_input("Source URL", placeholder="https://…")
            tags  = st.text_input("Tags (comma-separated)", placeholder="policy, faq")
            text  = st.text_area("Content *", height=160,
                                  placeholder="Paste document content here…")
            sub   = st.form_submit_button("✅ Add to KB", use_container_width=True, type="primary")
        if sub:
            if not (did and title and text):
                st.error("ID, Title and Content are required")
            elif not st.session_state.emb_service:
                st.error("Connect first")
            else:
                tl = [t.strip() for t in tags.split(",") if t.strip()]
                with st.spinner("Embedding and storing…"):
                    from app.services.rag import add_document
                    n = add_document(st.session_state.emb_service,
                                     doc_id=did,title=title,source=src,text=text,tags=tl)
                st.success(f"✅ Added — {n} chunk(s) stored"); st.rerun()

    # ── Search ──────────────────────────────────────────────────────
    with t3:
        q    = st.text_input("Search", placeholder="type a query…",
                              label_visibility="collapsed", key="kbsq")
        mode = st.radio("", ["Keyword","Semantic"], horizontal=True,
                         label_visibility="collapsed")
        if q.strip():
            if mode == "Keyword":
                res = _kb_docs(q)
                st.caption(f"{len(res)} result(s)")
                for r in res[:8]:
                    st.markdown(
                        f"<div class='kb-doc-row'>"
                        f"<div class='kb-doc-title'>{r['title']}</div>"
                        f"<div class='kb-doc-meta'>{r['doc_id']}</div>"
                        f"</div>", unsafe_allow_html=True)
            else:
                if not st.session_state.emb_service:
                    st.warning("Connect first")
                else:
                    with st.spinner("Vector search…"):
                        from app.config.database import db as _db
                        vec  = st.session_state.emb_service.embed_query(q)
                        hits = _db.vector_search(vec, top_k=6)
                    for h in hits:
                        sim = h.get("similarity",0)
                        col = "var(--teal)" if sim>.7 else "var(--gold)"
                        st.markdown(
                            f"<div class='kb-doc-row'>"
                            f"<div style='display:flex;justify-content:space-between'>"
                            f"<span class='kb-doc-title'>{h['chunk_id']}</span>"
                            f"<span style='color:{col};font-size:.74rem'>{sim:.0%}</span></div>"
                            f"<div style='color:var(--txt3);font-size:.73rem;margin-top:2px'>"
                            f"{h['text'][:100]}…</div></div>",
                            unsafe_allow_html=True)
        st.divider()
        all_docs = _kb_docs()
        if all_docs:
            exp = json.dumps(
                [{"chunk_id":d["doc_id"],"title":d["title"],
                  "source":d["source"],"text":d["text"],"tags":d["tags"]}
                 for d in all_docs], indent=2)
            st.download_button("⬇️ Export KB as JSON", data=exp.encode(),
                               file_name="kb_export.json", mime="application/json",
                               use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='font-size:1.1rem;font-weight:700;color:var(--txt);"
        "letter-spacing:-.02em;margin-bottom:2px'>🎧 Customer Support Assistant</div>"
        "<div style='font-size:.75rem;color:var(--txt3);margin-bottom:8px'>"
        "AI-Powered · Retrieval · Action</div>",
        unsafe_allow_html=True)
    st.divider()

    st.markdown("<div class='sbar-section'>AI Provider</div>", unsafe_allow_html=True)
    provider = st.selectbox("", ["openai","anthropic"],
                            index=0 if st.session_state.provider=="openai" else 1,
                            label_visibility="collapsed")
    st.session_state.provider = provider
    api_key = st.text_input("", value=st.session_state.api_key,
                             type="password", placeholder="API key…",
                             label_visibility="collapsed")
    st.session_state.api_key = api_key

    if st.button("⚡ Connect", use_container_width=True):
        if not api_key.strip():
            st.error("Enter API key")
        else:
            with st.spinner("Connecting…"):
                try:
                    s,e,a = _load_services(api_key, provider)
                    st.session_state.update(settings=s, emb_service=e, agent=a)
                    # Auto-seed KB immediately after connecting
                    with st.spinner("Loading knowledge base…"):
                        _seed_db(e, force=False)
                    st.success("Connected & knowledge base ready!")
                except Exception as ex:
                    st.error(str(ex))

    st.divider()
    st.markdown("<div class='sbar-section'>Status</div>", unsafe_allow_html=True)
    agent_ok  = st.session_state.agent is not None
    cnt       = _chroma_count()
    gmail     = _gmail_status()
    gmail_ok  = gmail.get("token_valid",False)

    st.markdown(
        f"<div style='display:flex;flex-direction:column;gap:6px;margin:4px 0'>"
        f"<span class='badge {'badge-teal' if agent_ok else 'badge-gray'}'>"
        f"{'✓' if agent_ok else '○'} Agent {'ready' if agent_ok else 'disconnected'}</span>"
        f"<span class='badge {'badge-teal' if cnt>0 else 'badge-red'}'>"
        f"{'✓' if cnt>0 else '✗'} {cnt} vectors indexed</span>"
        f"<span class='badge {'badge-teal' if gmail_ok else 'badge-coral'}'>"
        f"{'✓ Gmail authenticated' if gmail_ok else '○ Gmail not authorised'}</span>"
        f"</div>", unsafe_allow_html=True)

    if not gmail_ok:
        with st.expander("📧 Gmail & Calendar setup"):
            if gmail.get("oauth_file_exists"):
                st.caption("Run once to authorise Gmail + Calendar:")
                st.code("python -m app.config.gmail_auth")
                st.caption("⚠️ If already authorised, delete `credentials/gmail_token.json` first to re-authorise with Calendar scope.")
            else:
                st.caption("Follow **credentials/SETUP.md**, enable both Gmail API and Calendar API, then run:")
                st.code("python -m app.config.gmail_auth")

    st.divider()
    st.markdown("<div class='sbar-section'>Display</div>", unsafe_allow_html=True)
    st.session_state.show_rag   = st.toggle("Show thought chain", value=st.session_state.show_rag)
    st.session_state.show_tools = st.toggle("Show raw tool data",  value=st.session_state.show_tools)

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# ══════════════════════════════════════════════════════════════════
# MAIN — two-column layout
# ══════════════════════════════════════════════════════════════════
QUICK_PROMPTS = [
    ("🔄 Return policy",      "What's the return policy for items over $200?"),
    ("📦 Shipping costs",     "What are the shipping options and their costs?"),
    ("📅 Book consultation",  "Schedule a standard consultation for May 20, 2026 at 2pm EST with client@example.com"),
    ("⏱ Demo duration",      "How long is a product demo session?"),
    ("📧 Email me a summary", f"Send me an email to jcw.loong@gmail.com summarising the return and shipping policies"),
    ("🌍 Timezone info",      "What timezone are meetings scheduled in by default?"),
]

col_chat, col_kb = st.columns([3, 2], gap="large")

with col_chat:
    st.markdown(
        "<div style='font-size:1.5rem;font-weight:700;color:var(--txt);"
        "letter-spacing:-.03em;margin-bottom:2px'>🎧 Customer Support Assistant</div>"
        "<div style='color:var(--txt2);font-size:.85rem;margin-bottom:18px;line-height:1.5'>"
        "Ask questions, schedule real calendar events, or send real emails — "
        "the agent reasons step-by-step and calls the right tools automatically."
        "</div>", unsafe_allow_html=True)

    # ── Inline connect form (shown only when not connected) ──────────
    if not st.session_state.agent:
        with st.container(border=True):
            st.markdown(
                "<div style='font-size:.88rem;font-weight:600;color:var(--txt);margin-bottom:10px'>"
                "🔑 Connect to get started</div>",
                unsafe_allow_html=True)
            ic1, ic2, ic3 = st.columns([2, 3, 1])
            with ic1:
                inline_provider = st.selectbox(
                    "Provider", ["openai", "anthropic"],
                    index=0 if st.session_state.provider == "openai" else 1,
                    key="inline_provider"
                )
            with ic2:
                inline_key = st.text_input(
                    "API Key",
                    type="password",
                    placeholder="sk-proj-...  (OpenAI) or  sk-ant-...  (Anthropic)",
                    value=st.session_state.api_key,
                    key="inline_api_key"
                )
            with ic3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                do_connect = st.button("⚡ Connect", use_container_width=True,
                                       type="primary", key="inline_connect")

            if do_connect:
                if not inline_key.strip():
                    st.error("Please enter your API key above.")
                else:
                    with st.spinner("Connecting and loading knowledge base…"):
                        try:
                            s, e, a = _load_services(inline_key, inline_provider)
                            st.session_state.update(
                                settings=s, emb_service=e, agent=a,
                                api_key=inline_key, provider=inline_provider
                            )
                            _seed_db(e, force=False)
                            st.success("✅ Connected! Knowledge base ready.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Connection failed: {ex}")

            st.caption(
                "Get your OpenAI key at **platform.openai.com** → API Keys. "
                "Or set OPENAI_API_KEY in a .env file to connect automatically on launch."
            )

    if not st.session_state.messages:
        st.markdown(
            "<div style='color:var(--txt3);font-size:.74rem;font-weight:600;"
            "letter-spacing:.07em;text-transform:uppercase;margin-bottom:10px'>"
            "Suggested actions</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i,(label,prompt) in enumerate(QUICK_PROMPTS):
            with cols[i%3]:
                if st.button(label, key=f"qp_{i}", use_container_width=True):
                    st.session_state.pending_prompt = prompt

    for msg in st.session_state.messages:
        _render_message(msg)

    pending    = st.session_state.pop("pending_prompt", None) if "pending_prompt" in st.session_state else None
    user_input = st.chat_input("Ask anything or request an action…") or pending

    if user_input:
        if not st.session_state.agent:
            st.warning("⚠️ Enter your API key in the **sidebar** (click **›** top-left) and click **⚡ Connect**.")
            st.stop()
        if _chroma_count() == 0 and st.session_state.emb_service:
            with st.spinner("Loading knowledge base…"):
                _seed_db(st.session_state.emb_service)
        st.session_state.messages.append({"role":"user","content":user_input})
        _render_message({"role":"user","content":user_input})
        history = [{"role":m["role"],"content":m["content"]}
                   for m in st.session_state.messages[:-1]
                   if m["role"] in ("user","assistant")]
        with st.spinner("🧠 Agent reasoning…"):
            result = st.session_state.agent.process_query(
                query=user_input, chat_history=history)
        agent_msg = {
            "role":"assistant","content":result["text"],
            "meta":{"latency_ms":result["latency_ms"],
                    "rag_context":result["rag_context"],
                    "tool_calls":result["tool_calls"],
                    "tool_results":result["tool_results"],
                    "citations":result["citations"]}}
        st.session_state.messages.append(agent_msg)
        _render_message(agent_msg)

with col_kb:
    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        _kb_panel()
