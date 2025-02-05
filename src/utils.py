from __future__ import annotations

import json
from typing import Any, Literal

from litellm import ModelResponse
from loguru import logger

# Core types
Model = Literal[
    "claude-3-5-sonnet-20240620",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4o-mini",
    "groq/llama-3.1-8b-instant",
    "groq/llama-3.1-70b-versatile",
    "groq/llama-3.1-405b-reasoning",
]


# Core functions for data transformation
def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return text.lower().strip()


def update_dict_suffixed(
    d: dict[str, Any], d2: dict[str, Any], suffix: str = "_2"
) -> dict[str, Any]:
    """Update dictionary with suffix for colliding keys"""
    for k, v in d2.items():
        suffix_key = f"{k}{suffix}"
        if k in d:
            d[suffix_key] = v
        else:
            d[k] = v
    return d


def strip_response(response: str) -> str:
    """Clean and normalize AI model responses"""
    quote_chars = ['"', "'", """, """]
    code_chars = ["```", "json", "`"]

    for chars in [quote_chars, code_chars]:
        for char in chars:
            response = response.strip().strip("\n").strip(char)

    return response


def handle_response(response: ModelResponse) -> dict[str, list[str]] | None:
    """Handle model response"""
    if not response.choices:
        return None

    content = response.choices[0].message.content # type: ignore

    if content is None:
        return None

    content = strip_response(content)

    try:
        data = json.loads(content)
        if len(data):
            return data
    except Exception as e:
        logger.error(f"Error parsing response: {e}")

    return None
