from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ModelRecommendation:
    label: str
    model: str
    chat_template: str
    min_vram_gb: int
    best_for: str
    notes: str
    lora_rank: int = 16
    max_seq_length: int = 2048


CATALOG: List[ModelRecommendation] = [
    ModelRecommendation(
        "tiny-smoke-test",
        "unsloth/Llama-3.2-1B-Instruct-bnb-4bit",
        "llama-3.1",
        6,
        "validating your pipeline quickly",
        "Smallest safe default. Use this before spending real GPU time.",
        lora_rank=8,
    ),
    ModelRecommendation(
        "beginner-3b",
        "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
        "llama-3.1",
        8,
        "chat assistants, support bots, tone/style adapters",
        "Great default for beginners on a T4/3060-class GPU.",
    ),
    ModelRecommendation(
        "qwen-7b-quality",
        "unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
        "chatml",
        14,
        "domain Q&A, extraction, multilingual use cases",
        "Stronger than 3B; needs more VRAM. If this OOMs, fall back to beginner-3b.",
        lora_rank=16,
    ),
    ModelRecommendation(
        "llama-8b-quality",
        "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
        "llama-3.1",
        16,
        "general chat quality and tool-ish instruction following",
        "May require a Hugging Face token / license acceptance.",
        lora_rank=16,
    ),
    ModelRecommendation(
        "mistral-7b-fast",
        "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
        "mistral",
        14,
        "short-form assistants and classification/extraction",
        "Good 7B alternative if Llama is gated for you.",
        lora_rank=16,
    ),
]

TASK_HINTS = {
    "support-bot": "Prioritize consistent tone, policy answers, and refusal/escalation examples.",
    "domain-qa": "Include grounded Q&A pairs and eval questions held out from training.",
    "writing-style": "Use many short examples of desired style; avoid private or copyrighted text you cannot use.",
    "extractor": "Make outputs strict JSON and add malformed/edge-case inputs to eval.",
    "classifier": "Use a small model and deterministic labels; evaluate exact label accuracy.",
    "code-helper": "Prefer a code-tuned base model if your data is mostly code.",
}


def recommend_models(task: str = "chat-assistant", vram_gb: Optional[float] = None) -> List[ModelRecommendation]:
    """Return recommendations sorted for a beginner's task/hardware."""
    if vram_gb is None:
        return CATALOG[:]
    fits = [m for m in CATALOG if m.min_vram_gb <= vram_gb]
    if not fits:
        return [CATALOG[0]]
    # Include one stretch option so users know what upgrade buys them.
    stretch = next((m for m in CATALOG if m.min_vram_gb > vram_gb), None)
    return fits + ([stretch] if stretch else [])


def get_recommendation(label_or_model: str) -> ModelRecommendation:
    for rec in CATALOG:
        if label_or_model in {rec.label, rec.model}:
            return rec
    # Treat unknown values as a user-supplied HF model. Use auto template.
    return ModelRecommendation(
        label="custom",
        model=label_or_model,
        chat_template="auto",
        min_vram_gb=0,
        best_for="custom use case",
        notes="Custom model: verify the chat template with `unslothkit data preview` before training.",
    )


def task_hint(task: str) -> str:
    return TASK_HINTS.get(task, "Start with a smoke test, inspect examples, then run a small training job.")
