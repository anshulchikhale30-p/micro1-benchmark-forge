"""LLM client abstraction for Benchmark-Forge Agent.

Supports two providers:
  * "openai"  - uses the `openai` python package (requires OPENAI_API_KEY)
  * "mock"    - deterministic, offline rule-based responses used for
                reproducible runs in clean environments without API keys.

Select the provider with the BENCHMARK_FORGE_MODE environment variable
(defaults to "mock").
"""
from __future__ import annotations

import os


class LLMClient:
    mode = "base"

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    mode = "openai"

    def __init__(self, model: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""


class MockClient(LLMClient):
    mode = "mock"

    def complete(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
        # The mock provider never reaches this path: each agent implements its
        # own deterministic offline behaviour so runs are reproducible.
        return ""


def build_llm(mode: str | None = None) -> LLMClient:
    mode = mode or os.environ.get("BENCHMARK_FORGE_MODE", "mock")
    if mode == "openai":
        return OpenAIClient()
    return MockClient()
