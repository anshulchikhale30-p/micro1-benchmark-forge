from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class VerifierAgent:
    """Executes the generated test suite inside an isolated subprocess via
    `pytest` and returns whether it passed plus the captured logs so the
    Test Generator Agent can self-correct."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def run(self, test_code: str, code_snippet: str, test_id: str = "generated") -> tuple[bool, str]:
        work = Path(tempfile.mkdtemp(prefix="forge_"))
        try:
            (work / "solution.py").write_text(code_snippet, encoding="utf-8")
            (work / f"test_{test_id}.py").write_text(test_code, encoding="utf-8")

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(work / f"test_{test_id}.py"),
                "-q",
                "--no-header",
                "-p",
                "no:cacheprovider",
            ]
            
            # Added a 10-second timeout to prevent infinite loops from hanging the test runner
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(work), timeout=10)
            
            logs = (
                f"--- pytest exit code: {proc.returncode} ---\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )
            return proc.returncode == 0, logs
            
        except subprocess.TimeoutExpired:
            return False, "--- pytest execution timed out after 10 seconds (possible infinite loop) ---"
        except Exception as e:
            return False, f"--- Verifier execution error: {str(e)} ---"
        finally:
            # Clean up the temp directory safely
            shutil.rmtree(work, ignore_errors=True)