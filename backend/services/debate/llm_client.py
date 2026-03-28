"""Small OpenAI-backed helper for agentic debate nodes."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from typing import Any
from urllib import request

from dotenv import load_dotenv

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

# Ensure local `.env` is available for standalone module usage.
load_dotenv()


def llm_available() -> bool:
    """Return whether LLM calls can be attempted."""
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _extract_json_object(text: str) -> dict[str, object] | None:
    cleaned = text.strip()
    if not cleaned:
        return None
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = _JSON_BLOCK_RE.search(cleaned)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _content_from_response(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message", {})
    if not isinstance(message, Mapping):
        return ""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Some SDK/providers return a list of content blocks.
        parts: list[str] = []
        for block in content:
            if not isinstance(block, Mapping):
                continue
            text = block.get("text", "")
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(parts).strip()
    return ""


def call_llm_json(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> dict[str, object] | None:
    """Request JSON output from OpenAI Chat Completions.

    Returns None when key/model/network is unavailable or parsing fails.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENAI_DEBATE_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    timeout = float(os.getenv("OPENAI_DEBATE_TIMEOUT_SECONDS", "10"))
    endpoint = (
        os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        + "/chat/completions"
    )

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    encoded = json.dumps(body).encode("utf-8")
    req = request.Request(
        endpoint,
        data=encoded,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception:
        return None

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(decoded, Mapping):
        return None
    content = _content_from_response(decoded)
    if not content:
        return None
    return _extract_json_object(content)
