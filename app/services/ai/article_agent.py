"""Article-description agent used before a source becomes a presentation."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings


class ArticleDescriptionAgent:
    """Summarize an article with OpenAI when configured, otherwise locally."""

    def describe(self, title: str, sections: list[dict[str, str]]) -> dict[str, Any]:
        fallback = self._local_description(title, sections)
        settings = get_settings()
        if settings.AI_PROVIDER.lower() != "openai" or not settings.AI_API_KEY or not settings.AI_MODEL:
            return fallback
        try:
            return self._openai_description(settings.AI_MODEL, settings.AI_API_KEY, title, sections, fallback)
        except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError):
            # A source can still become a PPTX when the optional AI service is
            # unavailable; the fallback is deliberately deterministic.
            return fallback

    def _openai_description(
        self, model: str, api_key: str, title: str, sections: list[dict[str, str]], fallback: dict[str, Any]
    ) -> dict[str, Any]:
        source = "\n\n".join(f"## {s['title']}\n{s['text'][:2000]}" for s in sections[:12])
        prompt = (
            "You are an educational-content analyst. Summarize this article in Indonesian. "
            "Return JSON only with keys: description (max 80 words), audience (short string), "
            "and sections (an array of objects with title and summary, preserving source order).\n\n"
            f"Article title: {title}\n\n{source}"
        )
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": prompt, "store": False},
            timeout=30.0,
        )
        response.raise_for_status()
        body = response.json()
        text = "".join(
            part.get("text", "")
            for item in body.get("output", [])
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        )
        result = json.loads(text)
        if not isinstance(result.get("description"), str):
            return fallback
        return {
            "description": result["description"].strip()[:800],
            "audience": str(result.get("audience") or fallback["audience"])[:160],
            "sections": result.get("sections") if isinstance(result.get("sections"), list) else fallback["sections"],
            "agent": "openai",
        }

    def _local_description(self, title: str, sections: list[dict[str, str]]) -> dict[str, Any]:
        first_text = " ".join(section["text"] for section in sections[:2])
        sentences = re.split(r"(?<=[.!?])\s+", first_text.strip())
        summary = " ".join(sentences[:2]).strip() or f"Ringkasan artikel: {title}."
        return {
            "description": summary[:800],
            "audience": "pembaca umum dan peserta pembelajaran profesional",
            "sections": [
                {"title": section["title"], "summary": " ".join(re.split(r"(?<=[.!?])\s+", section["text"])[:1])[:400]}
                for section in sections
            ],
            "agent": "local-fallback",
        }
