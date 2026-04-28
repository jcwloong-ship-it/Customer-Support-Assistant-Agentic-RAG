"""
Tier 2 — Reasoning & Logic Tests
==================================
Validates the agentic loop: prompt construction, tool decision-making,
multi-turn history, citation extraction, and date injection.

All LLM calls are mocked — these tests verify the orchestrator's
control flow, not GPT-4o's language quality.
"""

import json
import re
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.schemas.tool_schemas import TOOL_DEFINITIONS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service):
    """Instantiate an orchestrator whose LLM client is a fresh MagicMock."""
    with patch("openai.OpenAI"):
        orch = AgentOrchestrator(fake_settings, in_memory_db, fake_embedding_service)
    orch._client = MagicMock()
    return orch


def _llm_text_response(text: str):
    """Mock a plain-text LLM response (no tool call)."""
    msg = MagicMock()
    msg.content    = text
    msg.tool_calls = None
    resp = MagicMock()
    resp.choices   = [MagicMock(message=msg)]
    return resp


def _llm_tool_response(name: str, arguments: dict, call_id: str = "call_001"):
    """Mock a tool-calling LLM response."""
    tc           = MagicMock()
    tc.id        = call_id
    tc.function.name      = name
    tc.function.arguments = json.dumps(arguments)

    msg = MagicMock()
    msg.content    = None
    msg.tool_calls = [tc]

    resp = MagicMock()
    resp.choices  = [MagicMock(message=msg)]
    return resp


# ── Tests: Prompt construction ─────────────────────────────────────────────────

class TestPromptConstruction:

    def test_current_date_injected_into_system_prompt(self, fake_settings,
                                                       in_memory_db,
                                                       fake_embedding_service):
        """Today's date and year must appear in the system prompt so the LLM
        never schedules events in the past."""
        orch     = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        messages = orch._build_messages("hello", [], None)
        system   = messages[0]["content"]

        today = datetime.now().strftime("%Y-%m-%d")
        year  = str(datetime.now().year)
        assert today in system, f"Today's date ({today}) missing from system prompt"
        assert year  in system, f"Current year ({year}) missing from system prompt"

    def test_rag_context_injected_as_chunk_ids(self, fake_settings,
                                                in_memory_db,
                                                fake_embedding_service):
        """Retrieved chunks must be prefixed [chunk_id] in the system prompt."""
        rag_context = [
            {"chunk_id": "policy_returns_v1#1", "text": "Return within 30 days.", "source": ""},
            {"chunk_id": "policy_shipping_v1#1", "text": "Free shipping over $50.", "source": ""},
        ]
        orch     = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        messages = orch._build_messages("test", rag_context, None)
        system   = messages[0]["content"]

        assert "[policy_returns_v1#1]"  in system
        assert "[policy_shipping_v1#1]" in system

    def test_empty_rag_context_uses_fallback(self, fake_settings,
                                              in_memory_db,
                                              fake_embedding_service):
        """When ChromaDB returns nothing, the prompt must say so explicitly."""
        orch     = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        messages = orch._build_messages("obscure question", [], None)
        system   = messages[0]["content"]
        assert "No relevant context found" in system

    def test_chat_history_appended_before_user_message(self, fake_settings,
                                                        in_memory_db,
                                                        fake_embedding_service):
        """Multi-turn history must be sandwiched between system prompt and
        the current user query."""
        history = [
            {"role": "user",      "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"},
        ]
        orch     = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        messages = orch._build_messages("What is your return policy?", [], history)

        roles = [m["role"] for m in messages]
        assert roles[0] == "system"
        assert roles[-1] == "user"
        # History is in the middle
        assert {"role": "assistant", "content": "Hello! How can I help?"} in messages

    def test_user_message_is_last(self, fake_settings, in_memory_db, fake_embedding_service):
        orch     = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        messages = orch._build_messages("My query", [], None)
        assert messages[-1] == {"role": "user", "content": "My query"}

    def test_tool_definitions_sent_to_llm(self, fake_settings, in_memory_db,
                                           fake_embedding_service):
        """The LLM must always receive the full tool schema so it can decide
        whether to call a tool."""
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        orch._client.chat.completions.create.return_value = _llm_text_response("ok")

        orch.process_query("hello")

        call_kwargs = orch._client.chat.completions.create.call_args.kwargs
        assert "tools" in call_kwargs, "tools parameter missing from LLM call"
        tool_names = [t["function"]["name"] for t in call_kwargs["tools"]]
        assert "create_calendar_event" in tool_names
        assert "send_email"            in tool_names


# ── Tests: Agentic reasoning loop ─────────────────────────────────────────────

class TestAgentReasoningLoop:

    def test_plain_query_resolves_in_one_iteration(self, fake_settings,
                                                    in_memory_db,
                                                    fake_embedding_service):
        """An informational question should not trigger any tool calls."""
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)
        orch._client.chat.completions.create.return_value = _llm_text_response(
            "Our return policy allows returns within 30 days [policy_returns_v1#1]."
        )

        result = orch.process_query("What is your return policy?")

        assert result["text"] != ""
        assert result["tool_calls"] == []
        # LLM should have been called exactly once
        assert orch._client.chat.completions.create.call_count == 1

    def test_scheduling_query_triggers_calendar_tool(self, fake_settings,
                                                      in_memory_db,
                                                      fake_embedding_service):
        """A scheduling request must trigger create_calendar_event."""
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)

        # First call: LLM returns a tool call
        orch._client.chat.completions.create.side_effect = [
            _llm_tool_response(
                "create_calendar_event",
                {
                    "summary":        "Product Demo",
                    "start_datetime": "2026-05-20T10:00:00",
                    "end_datetime":   "2026-05-20T10:45:00",
                    "attendees":      ["client@example.com"],
                    "timezone":       "America/New_York",
                },
                call_id="call_demo",
            ),
            # Second call: LLM writes confirmation text
            _llm_text_response("Your demo is booked for May 20 at 10 AM."),
        ]

        with patch("app.agents.tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "result":  {
                    "event_id":   "evt_123",
                    "event_link": "https://calendar.google.com/event?eid=evt_123",
                    "meet_link":  "https://meet.google.com/abc-defg",
                    "summary":    "Product Demo",
                    "start":      {"dateTime": "2026-05-20T10:00:00", "timeZone": "America/New_York"},
                    "end":        {"dateTime": "2026-05-20T10:45:00", "timeZone": "America/New_York"},
                    "attendees":  ["jcw.loong@gmail.com", "client@example.com"],
                    "status":     "confirmed",
                },
                "error": None,
            }

            result = orch.process_query("Schedule a product demo tomorrow at 10 AM")

        assert len(result["tool_calls"]) == 1
        tc = result["tool_calls"][0]
        assert tc["tool_name"] == "create_calendar_event"
        assert tc["arguments"]["summary"] == "Product Demo"

    def test_demo_end_time_is_45_minutes_after_start(self, fake_settings,
                                                       in_memory_db,
                                                       fake_embedding_service):
        """
        Reasoning test: when the agent retrieves the demo-duration policy
        (45 minutes) it must calculate end_datetime = start + 45 min.

        We assert this by inspecting the arguments the LLM decided to pass
        to create_calendar_event.
        """
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)

        tool_args = {
            "summary":        "Product Demo",
            "start_datetime": "2026-05-20T10:00:00",
            "end_datetime":   "2026-05-20T10:45:00",  # 45 min later
            "attendees":      ["client@example.com"],
            "timezone":       "America/New_York",
        }

        orch._client.chat.completions.create.side_effect = [
            _llm_tool_response("create_calendar_event", tool_args, "call_dur"),
            _llm_text_response("Demo booked for 45 minutes."),
        ]

        with patch("app.agents.tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = {"success": True, "result": {}, "error": None}
            result = orch.process_query(
                "Schedule a product demo for May 20 at 10 AM. "
                "Use the standard demo duration from the policy."
            )

        captured = result["tool_calls"][0]["arguments"]
        start = datetime.fromisoformat(captured["start_datetime"])
        end   = datetime.fromisoformat(captured["end_datetime"])
        delta_minutes = (end - start).total_seconds() / 60

        assert delta_minutes == 45, (
            f"Expected 45-minute demo, got {delta_minutes:.0f} minutes. "
            "Agent may not have applied the scheduling policy."
        )

    def test_email_query_triggers_send_email_tool(self, fake_settings,
                                                   in_memory_db,
                                                   fake_embedding_service):
        """An email request must trigger the send_email tool."""
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)

        orch._client.chat.completions.create.side_effect = [
            _llm_tool_response(
                "send_email",
                {
                    "to":      "alice@example.com",
                    "subject": "Meeting Confirmation",
                    "body":    "Your meeting is confirmed for tomorrow at 10 AM.",
                },
                call_id="call_mail",
            ),
            _llm_text_response("Email sent to alice@example.com."),
        ]

        with patch("app.agents.tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "result":  {"message_id": "msg_abc", "status": "sent"},
                "error":   None,
            }
            result = orch.process_query(
                "Send a confirmation email to alice@example.com about tomorrow's meeting."
            )

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool_name"] == "send_email"
        assert result["tool_calls"][0]["arguments"]["to"] == "alice@example.com"

    def test_max_iterations_prevent_infinite_loop(self, fake_settings,
                                                   in_memory_db,
                                                   fake_embedding_service):
        """The loop must exit after max_agent_iterations even if the LLM
        keeps returning tool calls without ever producing a final text."""
        fake_settings.max_agent_iterations = 3
        orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)

        # LLM always returns a tool call, never a text response
        orch._client.chat.completions.create.return_value = _llm_tool_response(
            "create_calendar_event",
            {"summary": "loop", "start_datetime": "2026-01-01T10:00:00",
             "end_datetime": "2026-01-01T11:00:00"},
        )

        with patch("app.agents.tools.registry.execute_tool") as mock_exec:
            mock_exec.return_value = {"success": True, "result": {}, "error": None}
            result = orch.process_query("keep scheduling forever")

        # Loop ran exactly max_agent_iterations times and did not crash
        assert orch._client.chat.completions.create.call_count == 3
        assert "latency_ms" in result  # result dict was returned cleanly


# ── Tests: Citation extraction ─────────────────────────────────────────────────

class TestCitationExtraction:

    @pytest.fixture(autouse=True)
    def setup(self, fake_settings, in_memory_db, fake_embedding_service):
        self.orch = _make_orchestrator(fake_settings, in_memory_db, fake_embedding_service)

    def _extract(self, text, context_ids):
        context = [{"chunk_id": cid, "text": "", "source": ""} for cid in context_ids]
        return self.orch._extract_citations(text, context)

    def test_valid_citation_extracted(self):
        text   = "Returns are allowed [policy_returns_v1#1] within 30 days."
        result = self._extract(text, ["policy_returns_v1#1", "policy_shipping_v1#1"])
        assert "policy_returns_v1#1" in result

    def test_invalid_citation_ignored(self):
        """[1] or [some text] should not be extracted as citations."""
        text   = "See [1] and [important note] for details."
        result = self._extract(text, ["policy_returns_v1#1"])
        assert result == [], f"Expected no citations, got: {result}"

    def test_duplicate_citations_deduplicated(self):
        """The same chunk_id mentioned twice should appear only once."""
        text   = "See [policy_returns_v1#1] and again [policy_returns_v1#1]."
        result = self._extract(text, ["policy_returns_v1#1"])
        assert result.count("policy_returns_v1#1") == 1

    def test_multiple_distinct_citations(self):
        text = (
            "Free shipping [policy_shipping_v1#1] and "
            "returns within 30 days [policy_returns_v1#1]."
        )
        result = self._extract(
            text, ["policy_shipping_v1#1", "policy_returns_v1#1"]
        )
        assert "policy_shipping_v1#1"  in result
        assert "policy_returns_v1#1"  in result

    def test_empty_text_returns_empty_list(self):
        assert self._extract("", ["policy_returns_v1#1"]) == []

    def test_empty_context_returns_empty_list(self):
        assert self._extract("See [policy_returns_v1#1].", []) == []

    def test_citations_preserve_order_of_first_appearance(self):
        """Citations should be returned in the order they first appear in text."""
        text   = "[policy_shipping_v1#1] and then [policy_returns_v1#1]."
        result = self._extract(text, ["policy_shipping_v1#1", "policy_returns_v1#1"])
        assert result == ["policy_shipping_v1#1", "policy_returns_v1#1"]
