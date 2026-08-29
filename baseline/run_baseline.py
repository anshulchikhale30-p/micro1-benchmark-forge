from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.extractor_agent import ExtractorAgent
from agents.llm_client import build_llm
from agents.test_generator_agent import TestGeneratorAgent
from agents.verifier_agent import VerifierAgent


def run_baseline_case(case: dict, llm) -> dict:
    """Single-prompt baseline: extract + one-shot generate, no verification
    loop. This mirrors the simplest possible LLM test-generation pipeline."""
    extractor = ExtractorAgent(llm)
    generator = TestGeneratorAgent(llm)
    verifier = VerifierAgent()

    problem = extractor.run(
        case.get("bug_report", ""), case.get("code_snippet", ""), context=case
    )
    # One-shot generation: no feedback, no retries.
    test_code = generator.run(problem, attempt=0, context=case)
    passed, logs = verifier.run(test_code, case.get("code_snippet", ""), test_id="baseline")
    return {
        "id": case.get("id"),
        "passed": passed,
        "attempts": 1,
        "logs": logs,
        "test": test_code,
    }


def main() -> None:
    cases_path = ROOT / "evaluation" / "test_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    llm = build_llm()

    results = [run_baseline_case(c, llm) for c in cases]
    passed = sum(1 for r in results if r["passed"])

    print(f"Baseline (single-prompt, no loop): {passed}/{len(results)} valid")
    for r in results:
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['id']}")


if __name__ == "__main__":
    main()
