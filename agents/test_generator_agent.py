from __future__ import annotations

import json

from .llm_client import LLMClient


class TestGeneratorAgent:
    """Writes a pytest unit-test module for the extracted problem.

    The verification loop feeds pytest stderr back into `run()` via the
    `feedback` argument so the agent can self-correct on subsequent attempts.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(
        self,
        problem: dict,
        feedback: str | None = None,
        attempt: int = 0,
        context: dict | None = None,
    ) -> str:
        if self.llm.mode == "mock":
            return self._mock_generate(problem, attempt, context)
        return self._llm_generate(problem, feedback, attempt)

    # ------------------------------------------------------------------ LLM
    def _system(self) -> str:
        return (
            "You are the Test Generator Agent of Benchmark-Forge. Write a pytest "
            "unit-test module that imports the target function from the module "
            "named `solution` and asserts the expected behavior. Return ONLY "
            "Python code, no explanation."
        )

    def _build_prompt(self, problem: dict, feedback: str | None, attempt: int) -> str:
        p = json.dumps(problem, indent=2)
        fb = (
            f"\nPrevious attempt (try {attempt}) failed. pytest output:\n{feedback}\n"
            "Analyse the error and rewrite the test so it is syntactically valid, "
            "imports correctly, and asserts the expected behavior.\n"
            if feedback
            else ""
        )
        return f"Problem:\n{p}\n{fb}\nReturn ONLY the Python test module code."

    def _llm_generate(self, problem: dict, feedback: str | None, attempt: int) -> str:
        return self.llm.complete(self._build_prompt(problem, feedback, attempt), system=self._system())

    # ---------------------------------------------------------------- mock
    def _mock_generate(self, problem: dict, attempt: int, context: dict | None = None) -> str:
        # Deterministic offline behaviour:
        #  - attempt 0 intentionally imports from a wrong module to exercise the
        #    verification/self-correction loop (ImportError).
        #  - attempt >= 1 imports from the real `solution` module and asserts the
        #    expected behaviour derived from the evaluation case examples.
        func = problem.get("function_name", "function")
        examples = problem.get("examples", []) or (context or {}).get("examples", [])
        module = "wrong_module" if attempt == 0 else "solution"

        header = [
            '"""',
            f"Auto-generated pytest suite for `{func}` (Benchmark-Forge Agent).",
            "",
            "Produced by the Test Generator Agent and verified inside an isolated",
            "sandbox by the Verifier Agent (pytest). The suite asserts the expected",
            "behaviour captured from the bug report / evaluation case.",
            '"""',
            "import pytest",
            "",
            f"from {module} import {func}",
            "",
        ]
        if not examples:
            body = [
                "",
                "def test_callable():",
                '    """The target function must be importable and callable."""',
                f"    assert callable({func})",
            ]
        else:
            body = []
            for i, ex in enumerate(examples):
                inp = ex.get("input", [])
                exp = ex.get("expected")
                # Use Python repr (not JSON) so booleans/null become valid literals.
                inp_repr = repr(inp)
                exp_repr = repr(exp)
                body.append("")
                body.append(f"def test_example_{i}():")
                body.append(f'    """Regression test: {func}({inp_repr}) == {exp_repr}."""')
                body.append(f"    assert {func}(*{inp_repr}) == {exp_repr}")
        return "\n".join(header + body + [""])
