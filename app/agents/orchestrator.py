"""
Agent Orchestrator — the core reasoning loop of the Customer Support Assistant.

For every user query:
  1. Retrieve relevant chunks from ChromaDB (RAG)
  2. Build a system prompt with retrieved context + current date
  3. Call the LLM with tool definitions (up to max_agent_iterations)
  4. Execute any tool calls and feed results back to the LLM
  5. Extract citations and return the structured result
"""

import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.gmail_auth import SENDER_EMAIL

logger = logging.getLogger(__name__)


class AgentOrchestrator:

    def __init__(self, settings, db, embedding_service):
        self.settings = settings
        self.db       = db
        self.emb      = embedding_service

        provider = settings.ai_provider
        if provider == "openai":
            import openai
            self._client = openai.OpenAI(api_key=settings.openai_api_key)
            self._model  = settings.openai_chat_model
        elif provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self._model  = settings.anthropic_chat_model
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

        self._provider = provider
        logger.info(f"Agent ready — {provider} / {self._model}")

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────

    def process_query(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None,
        top_k: int = 6,
    ) -> Dict[str, Any]:
        t0              = time.time()
        tool_calls_made: List[Dict] = []
        tool_results:    List[Dict] = []

        try:
            rag_context = self._retrieve(query, top_k)
            messages    = self._build_messages(query, rag_context, chat_history)
            final_text  = None

            for iteration in range(1, self.settings.max_agent_iterations + 1):
                logger.info(f"Agent iteration {iteration}")
                response = self._call_llm(messages)

                if response.get("tool_calls"):
                    for tc in response["tool_calls"]:
                        name   = tc["function"]["name"]
                        args   = json.loads(tc["function"]["arguments"])
                        logger.info(f"Executing tool: {name}")

                        from app.agents.tools.registry import execute_tool
                        result = execute_tool(name, **args)

                        tool_calls_made.append({
                            "tool_name": name,
                            "arguments": args,
                            "call_id":   tc["id"],
                        })
                        tool_results.append({
                            "call_id":   tc["id"],
                            "tool_name": name,
                            **result,
                        })
                        messages.append({
                            "role":       "assistant",
                            "content":    None,
                            "tool_calls": [{"id": tc["id"], "type": "function",
                                            "function": tc["function"]}],
                        })
                        messages.append({
                            "role":        "tool",
                            "tool_call_id": tc["id"],
                            "content":     json.dumps(result),
                        })
                else:
                    final_text = response.get("content", "")
                    break

            return {
                "text":         final_text or "Request processed.",
                "tool_calls":   tool_calls_made,
                "tool_results": tool_results,
                "citations":    self._extract_citations(final_text or "", rag_context),
                "rag_context":  rag_context,
                "latency_ms":   int((time.time() - t0) * 1000),
            }

        except Exception as exc:
            logger.error(f"Agent error: {exc}", exc_info=True)
            return {
                "text":         f"Error: {exc}",
                "tool_calls":   tool_calls_made,
                "tool_results": tool_results,
                "citations":    [],
                "rag_context":  [],
                "latency_ms":   int((time.time() - t0) * 1000),
            }

    # ─────────────────────────────────────────────────────────────────
    # RAG retrieval
    # ─────────────────────────────────────────────────────────────────

    def _retrieve(self, query: str, top_k: int) -> List[Dict]:
        try:
            raw  = self.db.vector_search(self.emb.embed_query(query), top_k)
            seen, blocks = set(), []
            for r in raw:
                base = r["chunk_id"].split("#")[0]
                if base not in seen:
                    blocks.append(r)
                    seen.add(base)
                if len(blocks) >= 4:
                    break
            return blocks
        except Exception as exc:
            logger.error(f"RAG retrieval failed: {exc}")
            return []

    # ─────────────────────────────────────────────────────────────────
    # Prompt construction
    # ─────────────────────────────────────────────────────────────────

    def _build_messages(
        self,
        query: str,
        rag_context: List[Dict],
        chat_history: Optional[List[Dict]],
    ) -> List[Dict]:
        ctx   = "\n\n".join(f"[{b['chunk_id']}] {b['text']}" for b in rag_context) \
                or "No relevant context found."
        today = datetime.now().strftime("%Y-%m-%d")
        year  = datetime.now().year

        system = f"""You are a helpful Customer Support AI assistant.

## Today's date
{today} (year {year}) — always use this year or future dates when scheduling.

## Knowledge base context
{ctx}

## Capabilities
1. Answer questions from the context above — cite sources as [chunk_id].
2. Schedule meetings using the `create_calendar_event` tool.
3. Send emails using the `send_email` tool.

## Guidelines
- Answer from context and include [chunk_id] citations.
- Use tools for action requests; confirm key details after each tool call.
- If context does not cover the question, say so honestly.
- Organiser / sender email: {self.settings.google_calendar_email or SENDER_EMAIL}"""

        messages: List[Dict] = [{"role": "system", "content": system}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": query})
        return messages

    # ─────────────────────────────────────────────────────────────────
    # LLM call — OpenAI or Anthropic
    # ─────────────────────────────────────────────────────────────────

    def _call_llm(self, messages: List[Dict]) -> Dict:
        from app.schemas.tool_schemas import TOOL_DEFINITIONS

        if self._provider == "openai":
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=self.settings.temperature,
                max_tokens=1500,
            )
            msg = resp.choices[0].message
            return {
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "function": {"name": tc.function.name,
                                               "arguments": tc.function.arguments}}
                    for tc in (msg.tool_calls or [])
                ] or None,
            }

        # Anthropic
        system_msg      = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs       = [m for m in messages if m["role"] != "system"]
        anthropic_tools = [
            {
                "name":         t["function"]["name"],
                "description":  t["function"]["description"],
                "input_schema": t["function"]["parameters"],
            }
            for t in TOOL_DEFINITIONS
        ]
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=1500,
            temperature=self.settings.temperature,
            system=system_msg,
            messages=user_msgs,
            tools=anthropic_tools,
        )
        content, tool_calls = "", []
        for block in resp.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id":       block.id,
                    "function": {"name": block.name, "arguments": json.dumps(block.input)},
                })
        return {"content": content, "tool_calls": tool_calls or None}

    # ─────────────────────────────────────────────────────────────────
    # Citation extraction
    # ─────────────────────────────────────────────────────────────────

    def _extract_citations(self, text: str, context: List[Dict]) -> List[str]:
        """Return chunk IDs that appear in [brackets] in the LLM response."""
        valid = {b["chunk_id"] for b in context}
        found, seen = [], set()
        for m in re.findall(r"\[([^\]]+)\]", text):
            if m in valid and m not in seen:
                found.append(m)
                seen.add(m)
        return found
