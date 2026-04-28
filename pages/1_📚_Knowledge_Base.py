"""
Knowledge Base — Browse, add, edit, search and delete documents.
"""

import os
import sys
import json
import io

import streamlit as st

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="Knowledge Base · CS Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (consistent dark theme) ───────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#0f1117; color:#e0e0e0; }
[data-testid="stSidebar"] { background:#161b27; border-right:1px solid #2a2d3a; }

.doc-card {
    background:#1a1d2e;
    border:1px solid #2e3348;
    border-radius:12px;
    padding:16px 20px;
    margin:8px 0;
    transition: border-color 0.2s;
}
.doc-card:hover { border-color:#3b82f6; }
.doc-title { font-size:1rem; font-weight:600; color:#e0e0e0; margin-bottom:4px; }
.doc-meta  { font-size:0.78rem; color:#6b7280; }
.doc-preview { font-size:0.82rem; color:#9ca3af; margin-top:8px;
               border-left:2px solid #374151; padding-left:10px; }
.tag-pill {
    display:inline-block; background:#1e3a5f; color:#60a5fa;
    border:1px solid #1d4ed8; border-radius:99px;
    padding:1px 10px; font-size:0.72rem; margin:2px 3px;
}
.stat-card {
    background:#1a1d2e; border:1px solid #2e3348; border-radius:10px;
    padding:14px 18px; text-align:center;
}
.stat-num  { font-size:1.8rem; font-weight:700; color:#60a5fa; }
.stat-label{ font-size:0.78rem; color:#6b7280; margin-top:2px; }
.badge { display:inline-block; padding:2px 10px; border-radius:99px;
         font-size:0.72rem; font-weight:600; }
.badge-green  { background:#064e3b; color:#34d399; }
.badge-yellow { background:#451a03; color:#fbbf24; }
.badge-red    { background:#450a0a; color:#f87171; }
.badge-blue   { background:#1e3a5f; color:#60a5fa; }
.section-header {
    font-size:0.72rem; font-weight:700; letter-spacing:0.08em;
    text-transform:uppercase; color:#6b7280; margin:14px 0 6px;
}
</style>
""", unsafe_allow_html=True)


# ── Imports ───────────────────────────────────────────────────────────────────
from app.config.kb_registry import (
    get_all_documents, get_document, search_documents,
    get_stats, upsert_document,
)
from app.config.database import db as _chroma
from app.data.default_documents import DEFAULT_DOCUMENTS


# ── Session helpers ───────────────────────────────────────────────────────────
def _emb():
    return st.session_state.get("emb_service")

def _connected():
    return st.session_state.get("agent") is not None

def _require_connection():
    if not _connected():
        st.warning("⚠️ Go to the **Chat** page, enter your API key and click **Connect** first.")
        st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📚 Knowledge Base")
    st.markdown("<div style='color:#6b7280;font-size:0.82rem'>Manage RAG documents</div>",
                unsafe_allow_html=True)
    st.divider()

    # Live stats
    stats = get_stats()
    st.markdown("### 📊 Database Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{stats.get('total_docs',0)}</div>"
            f"<div class='stat-label'>Documents</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            f"<div class='stat-card'><div class='stat-num'>{stats.get('total_chunks',0) or 0}</div>"
            f"<div class='stat-label'>Chunks</div></div>", unsafe_allow_html=True)

    chroma_count = _chroma.count()
    st.markdown(
        f"<br><span class='badge badge-{'green' if chroma_count>0 else 'red'}'>"
        f"{'Ready' if chroma_count>0 else 'Empty'}</span> "
        f"<span style='color:#9ca3af;font-size:0.8rem'>{chroma_count} vectors in ChromaDB</span>",
        unsafe_allow_html=True)

    st.divider()

    # Quick seed defaults
    st.markdown("### ⚡ Quick Actions")
    if st.button("🌱 Seed default KB", use_container_width=True):
        if not _connected():
            st.warning("Connect first on the Chat page.")
        else:
            with st.spinner("Seeding…"):
                from app.services.rag import seed_knowledge_base
                n = seed_knowledge_base(
                    st.session_state.emb_service,
                    documents=DEFAULT_DOCUMENTS,
                    force_reseed=False,
                )
                st.success(f"✅ {n} chunks added")
                st.rerun()

    if st.button("🗑️ Clear ALL documents", use_container_width=True, type="secondary"):
        st.session_state["confirm_clear"] = True

    if st.session_state.get("confirm_clear"):
        st.error("⚠️ This deletes everything from ChromaDB **and** the registry!")
        col_y, col_n = st.columns(2)
        with col_y:
            if st.button("Yes, clear", use_container_width=True):
                _chroma.clear()
                from app.config.kb_registry import _conn
                with _conn() as con:
                    con.execute("DELETE FROM documents")
                    con.commit()
                st.session_state.pop("confirm_clear", None)
                st.success("Cleared!")
                st.rerun()
        with col_n:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("confirm_clear", None)
                st.rerun()

    st.divider()
    st.page_link("streamlit_app.py", label="💬 Back to Chat", icon="🎧")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN AREA — tabs
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("# 📚 Knowledge Base Manager")
st.markdown(
    "<div style='color:#6b7280;margin-bottom:1.2rem'>"
    "Browse, search, add, edit and delete documents in your RAG knowledge base. "
    "Changes are immediately reflected in ChromaDB and used by the agent."
    "</div>", unsafe_allow_html=True)

tab_browse, tab_add, tab_import, tab_search = st.tabs([
    "📋 Browse Documents",
    "➕ Add Document",
    "📥 Import / Bulk",
    "🔍 Search KB",
])


# ════════════════════════════════════════════════════════
# TAB 1 — BROWSE
# ════════════════════════════════════════════════════════
with tab_browse:
    docs = get_all_documents()

    if not docs:
        st.info("No documents in the knowledge base yet. Use **Add Document** or **Seed default KB** to get started.")
    else:
        # Sort / filter bar
        col_sort, col_filter, col_count = st.columns([2, 3, 1])
        with col_sort:
            sort_by = st.selectbox("Sort by", ["Newest first", "Oldest first", "Title A→Z", "Most chunks"],
                                   label_visibility="collapsed")
        with col_filter:
            filter_tag = st.text_input("Filter by tag", placeholder="e.g. policy", label_visibility="collapsed")
        with col_count:
            st.markdown(f"<div style='color:#6b7280;padding-top:8px'>{len(docs)} docs</div>",
                        unsafe_allow_html=True)

        # Apply sort
        if sort_by == "Oldest first":
            docs = sorted(docs, key=lambda d: d["added_at"])
        elif sort_by == "Title A→Z":
            docs = sorted(docs, key=lambda d: d["title"].lower())
        elif sort_by == "Most chunks":
            docs = sorted(docs, key=lambda d: d["chunk_count"], reverse=True)

        # Apply tag filter
        if filter_tag.strip():
            ft = filter_tag.strip().lower()
            docs = [d for d in docs if any(ft in t.lower() for t in d["tags"])
                    or ft in d["title"].lower()]

        for doc in docs:
            _render_doc_card(doc)


def _render_doc_card(doc: dict):
    """Render a document card with inline expand/edit/delete."""
    doc_id = doc["doc_id"]
    title  = doc["title"]
    source = doc["source"]
    tags   = doc.get("tags", [])
    chunks = doc.get("chunk_count", 0)
    added  = doc.get("added_at", "")[:10]

    tag_html = "".join(f"<span class='tag-pill'>{t}</span>" for t in tags)
    preview  = doc["text"][:180].replace("\n", " ") + ("…" if len(doc["text"]) > 180 else "")

    with st.container():
        st.markdown(
            f"<div class='doc-card'>"
            f"<div class='doc-title'>📄 {title}</div>"
            f"<div class='doc-meta'>"
            f"ID: <code>{doc_id}</code> &nbsp;·&nbsp; "
            f"{chunks} chunk{'s' if chunks!=1 else ''} &nbsp;·&nbsp; "
            f"Added {added}"
            + (f" &nbsp;·&nbsp; <a href='{source}' target='_blank' style='color:#60a5fa'>{source[:50]}</a>" if source else "")
            + f"</div>"
            f"{('<div style=\"margin-top:6px\">' + tag_html + '</div>') if tags else ''}"
            f"<div class='doc-preview'>{preview}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        col_view, col_edit, col_del = st.columns([2, 1, 1])
        with col_view:
            with st.expander("👁 View full text"):
                st.text_area("Full document text", value=doc["text"], height=200,
                             disabled=True, key=f"view_{doc_id}", label_visibility="collapsed")
        with col_edit:
            if st.button("✏️ Edit", key=f"edit_btn_{doc_id}", use_container_width=True):
                st.session_state[f"editing_{doc_id}"] = True

        with col_del:
            if st.button("🗑️ Delete", key=f"del_btn_{doc_id}", use_container_width=True):
                st.session_state[f"confirm_del_{doc_id}"] = True

        # Confirm delete
        if st.session_state.get(f"confirm_del_{doc_id}"):
            st.warning(f"Delete **{title}**? This removes all its chunks from ChromaDB.")
            cy, cn = st.columns(2)
            with cy:
                if st.button("Yes, delete", key=f"yes_del_{doc_id}", use_container_width=True):
                    from app.services.rag import remove_document
                    remove_document(doc_id)
                    st.session_state.pop(f"confirm_del_{doc_id}", None)
                    st.success(f"Deleted '{title}'")
                    st.rerun()
            with cn:
                if st.button("Cancel", key=f"no_del_{doc_id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{doc_id}", None)
                    st.rerun()

        # Inline edit form
        if st.session_state.get(f"editing_{doc_id}"):
            with st.form(key=f"edit_form_{doc_id}"):
                st.markdown("**Edit document**")
                new_title  = st.text_input("Title", value=title)
                new_source = st.text_input("Source URL", value=source)
                new_tags   = st.text_input("Tags (comma-separated)", value=", ".join(tags))
                new_text   = st.text_area("Document text", value=doc["text"], height=250)
                col_save, col_cancel = st.columns(2)
                with col_save:
                    submitted = st.form_submit_button("💾 Save & Re-embed", use_container_width=True)
                with col_cancel:
                    cancelled = st.form_submit_button("Cancel", use_container_width=True)

                if submitted:
                    if not _connected():
                        st.error("Connect on the Chat page first.")
                    else:
                        tag_list = [t.strip() for t in new_tags.split(",") if t.strip()]
                        with st.spinner("Re-embedding…"):
                            from app.services.rag import add_document
                            n = add_document(
                                st.session_state.emb_service,
                                doc_id=doc_id,
                                title=new_title,
                                source=new_source,
                                text=new_text,
                                tags=tag_list,
                            )
                        st.session_state.pop(f"editing_{doc_id}", None)
                        st.success(f"Updated! {n} chunks re-embedded.")
                        st.rerun()

                if cancelled:
                    st.session_state.pop(f"editing_{doc_id}", None)
                    st.rerun()


# ════════════════════════════════════════════════════════
# TAB 2 — ADD DOCUMENT
# ════════════════════════════════════════════════════════
with tab_add:
    st.markdown("### ➕ Add a New Document")
    st.markdown(
        "<div style='color:#6b7280;font-size:0.85rem;margin-bottom:1rem'>"
        "Documents are chunked and embedded automatically. "
        "The agent will use them immediately for RAG retrieval."
        "</div>", unsafe_allow_html=True)

    with st.form("add_doc_form"):
        col_id, col_title = st.columns(2)
        with col_id:
            new_id    = st.text_input("Document ID *", placeholder="policy_refund_v2",
                                      help="Unique identifier, no spaces")
        with col_title:
            new_title = st.text_input("Title *", placeholder="Refund Policy")

        new_source = st.text_input("Source URL", placeholder="https://help.example.com/refunds")
        new_tags   = st.text_input("Tags (comma-separated)", placeholder="policy, refund, returns")
        new_text   = st.text_area("Document text *", height=300,
                                  placeholder="Paste your document content here…")

        col_preview, col_submit = st.columns([1, 1])
        with col_preview:
            preview_btn = st.form_submit_button("👁 Preview chunks", use_container_width=True)
        with col_submit:
            add_btn = st.form_submit_button("✅ Add to Knowledge Base", use_container_width=True,
                                            type="primary")

    if preview_btn and new_text:
        from app.services.chunker import chunker
        doc = {"chunk_id": new_id or "preview_doc", "source": new_source, "text": new_text}
        chunks = chunker.chunk_documents([doc])
        st.markdown(f"<div class='section-header'>Preview — {len(chunks)} chunks</div>",
                    unsafe_allow_html=True)
        for i, c in enumerate(chunks, 1):
            with st.expander(f"Chunk {i} — {c['chunk_id']} ({len(c['text'].split())} words)"):
                st.text(c["text"])

    if add_btn:
        if not new_id or not new_title or not new_text:
            st.error("Document ID, Title and Text are required.")
        elif not _connected():
            st.error("Please connect on the Chat page first (API key → Connect).")
        else:
            # Check for duplicate
            existing = get_document(new_id)
            if existing:
                st.warning(f"Document ID `{new_id}` already exists. Saving will overwrite it.")

            tag_list = [t.strip() for t in new_tags.split(",") if t.strip()]
            with st.spinner(f"Embedding and storing '{new_title}'…"):
                from app.services.rag import add_document
                n = add_document(
                    st.session_state.emb_service,
                    doc_id=new_id,
                    title=new_title,
                    source=new_source,
                    text=new_text,
                    tags=tag_list,
                )
            st.success(f"✅ Added **{new_title}** — {n} chunk{'s' if n!=1 else ''} embedded and stored!")
            st.balloons()


# ════════════════════════════════════════════════════════
# TAB 3 — IMPORT / BULK
# ════════════════════════════════════════════════════════
with tab_import:
    st.markdown("### 📥 Bulk Import")

    import_tab1, import_tab2, import_tab3 = st.tabs(["📄 Upload .txt / .md", "🗂️ Upload JSON", "📋 Export KB"])

    with import_tab1:
        st.markdown("Upload one or more plain-text or Markdown files. Each file becomes one document.")
        uploaded_files = st.file_uploader(
            "Choose files", type=["txt", "md"],
            accept_multiple_files=True, label_visibility="collapsed"
        )
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
            for f in uploaded_files:
                st.markdown(f"- `{f.name}` ({f.size:,} bytes)")

            src_url = st.text_input("Source URL (applies to all files)", placeholder="https://docs.example.com/")
            tags_all = st.text_input("Tags for all files (comma-separated)", placeholder="imported, docs")

            if st.button("📥 Import all files", type="primary"):
                if not _connected():
                    st.error("Connect on the Chat page first.")
                else:
                    from app.services.rag import add_document
                    tag_list = [t.strip() for t in tags_all.split(",") if t.strip()]
                    total = 0
                    progress = st.progress(0)
                    for i, f in enumerate(uploaded_files):
                        text = f.read().decode("utf-8", errors="replace")
                        doc_id = f.name.rsplit(".", 1)[0].replace(" ", "_").lower()
                        title  = f.name.rsplit(".", 1)[0].replace("_", " ").title()
                        n = add_document(
                            st.session_state.emb_service,
                            doc_id=doc_id, title=title,
                            source=src_url, text=text, tags=tag_list,
                        )
                        total += n
                        progress.progress((i + 1) / len(uploaded_files))
                    st.success(f"✅ Imported {len(uploaded_files)} files → {total} chunks total")
                    st.rerun()

    with import_tab2:
        st.markdown("""
Upload a JSON file with this format:
```json
[
  {
    "chunk_id": "doc_id_here",
    "title": "My Document",
    "source": "https://...",
    "text": "Document content...",
    "tags": ["tag1", "tag2"]
  }
]
```
""")
        json_file = st.file_uploader("Choose JSON file", type=["json"], label_visibility="collapsed")

        if json_file:
            try:
                raw = json.loads(json_file.read().decode())
                if isinstance(raw, dict):
                    # Wrap single doc
                    raw = [raw]
                st.success(f"Valid JSON — {len(raw)} document(s) found")
                st.dataframe(
                    [{"id": d.get("chunk_id",""), "title": d.get("title",""), "chars": len(d.get("text",""))}
                     for d in raw],
                    use_container_width=True,
                )
                if st.button("📥 Import JSON", type="primary"):
                    if not _connected():
                        st.error("Connect on the Chat page first.")
                    else:
                        from app.services.rag import add_document
                        total = 0
                        for doc in raw:
                            n = add_document(
                                st.session_state.emb_service,
                                doc_id=doc.get("chunk_id", f"doc_{total}"),
                                title=doc.get("title", doc.get("chunk_id", "Untitled")),
                                source=doc.get("source", ""),
                                text=doc.get("text", ""),
                                tags=doc.get("tags", []),
                            )
                            total += n
                        st.success(f"✅ Imported {len(raw)} docs → {total} chunks")
                        st.rerun()
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    with import_tab3:
        st.markdown("Download all your knowledge base documents as a JSON file.")
        docs_all = get_all_documents()
        if not docs_all:
            st.info("No documents to export yet.")
        else:
            export_data = [
                {
                    "chunk_id": d["doc_id"],
                    "title":    d["title"],
                    "source":   d["source"],
                    "text":     d["text"],
                    "tags":     d["tags"],
                    "added_at": d["added_at"],
                }
                for d in docs_all
            ]
            export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                label=f"⬇️ Export {len(docs_all)} documents as JSON",
                data=export_json.encode("utf-8"),
                file_name="kb_export.json",
                mime="application/json",
                use_container_width=True,
            )
            st.caption(f"Export includes {len(docs_all)} documents · {sum(d.get('chunk_count',0) for d in docs_all)} total chunks")


# ════════════════════════════════════════════════════════
# TAB 4 — SEARCH
# ════════════════════════════════════════════════════════
with tab_search:
    st.markdown("### 🔍 Search the Knowledge Base")

    col_q, col_mode = st.columns([4, 1])
    with col_q:
        query = st.text_input("Search query", placeholder="return policy, consultation duration…",
                              label_visibility="collapsed")
    with col_mode:
        mode = st.selectbox("Mode", ["Keyword", "Semantic"], label_visibility="collapsed")

    if query.strip():
        if mode == "Keyword":
            results = search_documents(query)
            st.markdown(f"<div class='section-header'>{len(results)} keyword result(s) for \"{query}\"</div>",
                        unsafe_allow_html=True)
            if not results:
                st.info("No documents matched. Try different keywords.")
            for doc in results:
                # Highlight matching text
                preview = doc["text"][:300].replace("\n", " ")
                st.markdown(
                    f"<div class='doc-card'>"
                    f"<div class='doc-title'>📄 {doc['title']}</div>"
                    f"<div class='doc-meta'>ID: <code>{doc['doc_id']}</code> · {doc['chunk_count']} chunks</div>"
                    f"<div class='doc-preview'>{preview}…</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        else:  # Semantic
            if not _connected():
                st.warning("Connect on the Chat page to use semantic search.")
            else:
                with st.spinner("Running vector similarity search…"):
                    from app.services.embedding import EmbeddingService
                    emb_vec = st.session_state.emb_service.embed_query(query)
                    raw = _chroma.vector_search(emb_vec, top_k=8)

                st.markdown(f"<div class='section-header'>{len(raw)} semantic result(s) for \"{query}\"</div>",
                            unsafe_allow_html=True)

                for r in raw:
                    sim = r.get("similarity", 0)
                    bar_w = int(sim * 100)
                    bar_color = "#10b981" if sim > 0.7 else "#f59e0b" if sim > 0.4 else "#6b7280"
                    st.markdown(
                        f"<div class='doc-card'>"
                        f"<div class='doc-title'>🔎 {r['chunk_id']}</div>"
                        f"<div class='doc-meta'>"
                        f"Similarity: <b style='color:{bar_color}'>{sim:.1%}</b>"
                        f"<div style='background:#1e2130;border-radius:4px;height:4px;margin:4px 0'>"
                        f"<div style='background:{bar_color};width:{bar_w}%;height:4px;border-radius:4px'></div>"
                        f"</div></div>"
                        f"<div class='doc-preview'>{r['text'][:280]}…</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
