"""Anthropic API wrapper for the AI editing agent."""

from __future__ import annotations

import time
from typing import Any

import anthropic

from ..config import AIConfig
from .schemas import ANALYZE_TRANSCRIPT_TOOL, CREATE_CUT_PLAN_TOOL


class AIClient:
    def __init__(self, config: AIConfig) -> None:
        self.config = config
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    def analyze_transcript(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Claude to analyze and score transcript segments.

        Returns the parsed tool input (analysis dict).
        """
        return self._call_tool(
            system_prompt, user_prompt, ANALYZE_TRANSCRIPT_TOOL, "analyze_transcript"
        )

    def create_cut_plan(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Claude to create a cut plan for a specific content format.

        Returns the parsed tool input (cut plan dict).
        """
        return self._call_tool(
            system_prompt, user_prompt, CREATE_CUT_PLAN_TOOL, "create_cut_plan"
        )

    def _call_tool(
        self,
        system_prompt: str,
        user_prompt: str,
        tool: dict,
        tool_name: str,
    ) -> dict[str, Any]:
        """Call Claude with structured output via tool use.

        Retries up to 3 times with exponential backoff on transient errors.
        """
        tools = [tool]
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
                    tool_choice={"type": "tool", "name": tool_name},
                )
                return self._extract_tool_input(response, tool_name)

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

    def _extract_tool_input(self, response: Any, tool_name: str) -> dict[str, Any]:
        """Extract the tool use input from the response."""
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input
        raise ValueError(f"No {tool_name} tool use found in response")
