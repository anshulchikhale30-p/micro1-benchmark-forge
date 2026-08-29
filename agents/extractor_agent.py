from __future__ import annotations

import json
import re

from .llm_client import LLMClient


class ExtractorAgent:
    """Parses bug descriptions / diffs / code snippets into a structured
    problem description used by the Test Generator Agent."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, bug_report: str, code_snippet: str, context: dict | None = None) -> dict:
        if self.llm.mode == "mock":
            return self._mock_extract(bug_report, code_snippet, context)
        return self._llm_extract(bug_report, code_snippet)

    # ------------------------------------------------------------------ LLM
    def _system(self) -> str:
        return (
            "You are the Extractor Agent of Benchmark-Forge. Convert a bug "
            "report and/or code snippet into a strict JSON object describing the "
            "problem to be tested. Output ONLY valid JSON, no prose."
        )

    def _build_prompt(self, bug_report: str, code_snippet: str) -> str:
        return f"""Bug report:
{bug_report}

Code snippet:
{code_snippet}

Return JSON with exactly these keys:
{{
  "title": str,
  "language": "python",
  "function_name": str,
  "description": str,
  "expected_behavior": str,
  "edge_cases": [str],
  "examples": [{{"input": [args...], "expected": value}}]
}}
"""

    def _llm_extract(self, bug_report: str, code_snippet: str) -> dict:
        out = self.llm.complete(self._build_prompt(bug_report, code_snippet), system=self._system())
        return self._coerce(json.loads(self._extract_json(out)))

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
        return text.strip()

    # ---------------------------------------------------------------- mock
    def _mock_extract(self, bug_report: str, code_snippet: str, context: dict | None = None) -> dict:
        m = re.search(r"def\s+([A-Za-z_]\w*)\s*\(", code_snippet or "")
        func = m.group(1) if m else (context or {}).get("function_name", "function")
        ctx = context or {}
        title = bug_report.strip().splitlines()[0] if bug_report.strip() else f"Test {func}"
        return {
            "title": title,
            "language": "python",
            "function_name": func,
            "description": bug_report.strip(),
            "expected_behavior": ctx.get("expected_behavior", ""),
            "edge_cases": ctx.get("edge_cases", []),
            "examples": ctx.get("examples", []),
        }

    @staticmethod
    def _coerce(d: dict) -> dict:
        d.setdefault("examples", [])
        d.setdefault("function_name", "function")
        d.setdefault("language", "python")
        return d
