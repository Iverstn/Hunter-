from __future__ import annotations

import re
from dataclasses import dataclass

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "llm",
    "language model",
    "diffusion",
    "transformer",
    "gpu",
    "datacenter",
    "semiconductor",
    "compute",
    "inference",
    "training",
    "safety",
    "alignment",
    "policy",
    "export control",
    "regulation",
    "chip",
    "nvidia",
    "openai",
    "anthropic",
    "deepmind",
    "xai",
    "agent",
    "benchmark",
    "model release",
    "paper",
]

TAG_RULES = {
    "Frontier research": ["paper", "benchmark", "model", "research"],
    "Products & releases": ["launch", "release", "product", "api"],
    "Infra & semis": ["gpu", "chip", "datacenter", "semiconductor", "nvidia"],
    "Agents & tooling": ["agent", "tool", "framework", "sdk"],
    "Safety & alignment": ["safety", "alignment", "eval"],
    "Policy & geopolitics": ["policy", "regulation", "export control"],
    "Markets & investing": ["funding", "investment", "market", "valuation"],
    "People & org moves": ["hiring", "joins", "leaves", "promotion"],
    "Energy & Datacenter (Power/Cooling/Grid/Nuclear/Real Estate)": [
        "power",
        "cooling",
        "grid",
        "nuclear",
        "real estate",
        "datacenter",
    ],
    "AI for Science & Physical World": ["biology", "chemistry", "robot", "physics"],
    "Data Strategy & Supply": ["data", "dataset", "corpus"],
    "Edge & On-Device AI": ["edge", "on-device", "mobile"],
}


@dataclass
class FilterResult:
    keep: bool
    tags: list[str]
    reasons: list[str]


def rule_filter(text: str) -> FilterResult:
    text_lower = text.lower()
    hits = [kw for kw in AI_KEYWORDS if kw in text_lower]
    keep = bool(hits)
    tags: list[str] = []
    for tag, keywords in TAG_RULES.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return FilterResult(keep=keep, tags=tags, reasons=hits)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
