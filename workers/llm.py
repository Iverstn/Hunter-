from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.settings import settings


class LLMClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.openai_api_key)

    def enabled(self) -> bool:
        return self.client is not None

    def classify(self, text: str) -> dict[str, Any]:
        if not self.client:
            return {"keep": True, "tags": [], "summary": None, "analysis": None, "score_adjust": 0}
        prompt = (
            "You are a buy-side AI signal filter. Decide KEEP or DROP, assign tags, summarize,"
            "and provide 2-3 sentence analysis. Tags: Frontier research, Products & releases,"
            "Infra & semis, Agents & tooling, Safety & alignment, Policy & geopolitics,"
            "Markets & investing, People & org moves, Energy & Datacenter (Power/Cooling/Grid/Nuclear/Real Estate),"
            "AI for Science & Physical World, Data Strategy & Supply, Edge & On-Device AI."
        )
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:6000]},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        return {"keep": True, "tags": [], "summary": content, "analysis": None, "score_adjust": 0}

    def chinese_summary(self, text: str) -> str | None:
        if not self.client:
            return None
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "用中文总结以下内容，简洁清晰。"},
                {"role": "user", "content": text[:6000]},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
