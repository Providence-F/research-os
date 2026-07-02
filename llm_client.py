#!/usr/bin/env python3
"""DeepSeek LLM client for Research OS intent layer.

Used by intent_discovery, intent_tracker, profile_updater. Kept minimal -
no SDK dependency, just urllib + json. No logging to avoid leaking user
content to stdout or log files.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

import config  # ensures .env is loaded into os.environ before key lookup


DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
MAX_RETRIES = 3


def chat(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    timeout: int = 90,
) -> str:
    """Call DeepSeek chat completion. Returns the assistant message content.

    Raises RuntimeError after MAX_RETRIES failed attempts. Retries with
    exponential backoff (1s, 2s, 4s) on network/timeout errors.
    """
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not set. Create .env in research-os/ with "
            "DEEPSEEK_API_KEY=sk-..., or export the variable in your shell."
        )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(
            DEEPSEEK_ENDPOINT, data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            last_err = exc
            # 4xx (except 429) usually means bad request - don't retry
            if 400 <= exc.code < 500 and exc.code != 429:
                raise RuntimeError(f"DeepSeek API HTTP {exc.code}: {exc.reason}") from exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_err = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
    raise RuntimeError(f"DeepSeek API failed after {MAX_RETRIES} attempts: {last_err}")


def chat_json(
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 2500,
) -> dict[str, Any]:
    """Call chat() and parse the response as JSON.

    Strips markdown code fences if DeepSeek wrapped the response in
    ```json ... ``` blocks.
    """
    raw = chat(messages, temperature=temperature, max_tokens=max_tokens)
    text = raw.strip()
    if text.startswith("```"):
        # Drop opening fence line
        if "\n" in text:
            text = text.split("\n", 1)[1]
        else:
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    # Sometimes the model adds prose before/after the JSON. Find the first
    # balanced { ... } block.
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)
