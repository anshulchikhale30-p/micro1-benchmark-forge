from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.extractor_agent import ExtractorAgent
from agents.llm_client import build_llm
from agents.test_generator_agent import TestGeneratorAgent
from agents.verifier_agent import VerifierAgent

MAX_RETRIES = 3


def run_forge_case(case: dict, llm, trajectories: list) -> tuple[dict, str, str]:
    """Run the full agentic workflow for a single evaluation case.

    1. Extractor parses the bug report / code into a structured problem.
    2. Test Generator writes a pytest module.
    3. Verifier runs pytest in a safe subprocess. On failure, the error log is
       fed back to the generator for self-correction (up to MAX_RETRIES).
    """
    extractor = ExtractorAgent(llm)
    generator = TestGeneratorAgent(llm)
    verifier = VerifierAgent(max_retries=MAX_RETRIES)

    traj = {"id": case.get("id"), "title": case.get("title", ""), "steps": []}

    problem = extractor.run(
        case.get("bug_report", ""), case.get("code_snippet", ""), context=case
    )
    traj["steps"].append({"agent": "extractor", "output": problem})

    test_code = None
    passed = False
    logs = ""
    attempt = 0
    for attempt in range(MAX_RETRIES):
        feedback = logs if attempt > 0 else None
        test_code = generator.run(problem, feedback=feedback, attempt=attempt, context=case)
        traj["steps"].append({"agent": "generator", "attempt": attempt, "test": test_code})

        passed, logs = verifier.run(test_code, case.get("code_snippet", ""), test_id=f"forge_{case.get('id')}")
        traj["steps"].append(
            {"agent": "verifier", "attempt": attempt, "passed": passed, "logs": logs}
        )
        if passed:
            break

    traj["result"] = {"passed": passed, "attempts": attempt + 1}
    trajectories.append(traj)
    return traj["result"], test_code, logs


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    llm = build_llm(mode)

    cases_path = ROOT / "evaluation" / "test_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    trajectories: list = []
    results: list = []
    for case in cases:
        res, _test, _logs = run_forge_case(case, llm, trajectories)
        results.append(res)
        print(f"[{'PASS' if res['passed'] else 'FAIL'}] {case.get('id')} (attempts={res['attempts']})")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\nBenchmark-Forge: {passed}/{total} cases produced valid, passing tests.")

    write_trajectories(trajectories)
    write_summary(results, passed, total)


def write_trajectories(trajectories: list) -> None:
    out = ROOT / "trajectories.md"
    lines = [
        "# Benchmark-Forge Agent — Execution Trajectories",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "Each section logs the step-by-step execution of the Extractor, Test "
        "Generator, and Verifier agents, including verification retries.",
        "",
    ]
    for t in trajectories:
        lines.append(f"## Case `{t['id']}` — {t['title']}")
        lines.append("")
        for s in t["steps"]:
            if s["agent"] == "extractor":
                lines += ["### Extractor Agent", "", "```json", json.dumps(s["output"], indent=2), "```", ""]
            elif s["agent"] == "generator":
                lines += [
                    f"### Test Generator Agent (attempt {s['attempt']})",
                    "",
                    "```python",
                    s["test"],
                    "```",
                    "",
                ]
            elif s["agent"] == "verifier":
                status = "PASS" if s["passed"] else "FAIL"
                lines += [
                    f"### Verifier Agent (attempt {s['attempt']}) — {status}",
                    "",
                    "```",
                    s["logs"][:2000],
                    "```",
                    "",
                ]
        r = t["result"]
        lines.append(f"**Result:** {'PASS' if r['passed'] else 'FAIL'} in {r['attempts']} attempt(s).")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote trajectories -> {out}")


def write_summary(results: list, passed: int, total: int) -> None:
    out = ROOT / "evaluation" / "results.json"
    out.write_text(
        json.dumps({"total": total, "passed": passed, "results": results}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
