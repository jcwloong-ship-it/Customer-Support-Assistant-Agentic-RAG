"""
OpenAI-format tool definitions for the agent's function-calling loop.
"""

from typing import List, Dict, Any

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Create a calendar event / meeting. Use when the user wants to schedule "
                "a meeting, appointment, or call. If the user says 'standard consultation' "
                "or similar, check RAG context for default duration before setting end_datetime."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title (e.g. 'Consultation Call with Alice')",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the event (optional)",
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "ISO 8601 start time, e.g. '2026-05-10T14:00:00'",
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "ISO 8601 end time, e.g. '2026-05-10T14:30:00'",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone string, e.g. 'America/New_York'. Defaults to UTC.",
                    },
                },
                "required": ["summary", "start_datetime", "end_datetime"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email to a recipient via Gmail. Use when the user wants to send "
                "a confirmation, follow-up, or any email communication."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body (plain text)"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
]
