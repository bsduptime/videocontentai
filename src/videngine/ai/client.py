"""Anthropic API wrapper for the AI editing agent."""

from __future__ import annotations

import json
import time
from typing import Any

import anthropic

from ..config import AIConfig
from .schemas import EDIT_DECISION_TOOL


class AIClient:
    def __init__(self, config: AIConfig) -> None:
        self.config = config
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    def create_edit_decision(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Claude with structured output via tool use.

        Returns the parsed tool input (edit decision dict).
        Retries up to 3 times with exponential backoff on transient errors.
        """
        tools = [EDIT_DECISION_TOOL]
        last_error = None

        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    tools=tools,
                    tool_choice={"type": "tool", "name": "create_edit_decision"},
                )
                return self._extract_tool_input(response)

            except anthropic.RateLimitError:
                last_error = "Rate limited"
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    last_error = str(e)
                    wait = 2 ** (attempt + 1)
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"AI API failed after 3 retries: {last_error}")

    def _extract_tool_input(self, response: Any) -> dict[str, Any]:
        """Extract the tool use input from the response."""
        for block in response.content:
            if block.type == "tool_use" and block.name == "create_edit_decision":
                return block.input
        raise ValueError("No create_edit_decision tool use found in response")
