import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def matches(actual: dict, expected: dict, json_mode: bool) -> bool:
    if not json_mode:
        return actual == expected
    if (actual.get("exit"), actual.get("stderr")) != (0, ""):
        return False
    try:
        value = json.loads(actual["stdout"])
    except json.JSONDecodeError:
        return False
    return (
        isinstance(value, dict)
        and set(value) == {"total"}
        and type(value["total"]) is int
        and value == json.loads(expected["stdout"])
    )


def run_cases(candidate: Path, stage: str) -> dict:
    candidate = candidate.resolve()
    before = candidate.read_bytes()
    cases = [
        ("A1", "2\n3\n", ["--format", "json"],
         0, '{"total": 5}\n', ""),
    ]
    if stage == "golden":
        cases += [
            ("A2", "2\n3\n", [], 0, "total=5\n", ""),
            ("A3", "2\noops\n", ["--format", "json"],
             1, "", "invalid input\n"),
        ]

    results = []
    with TemporaryDirectory() as folder:
        fixture = Path(folder) / "numbers.txt"
        for name, data, options, code, output, errors in cases:
            fixture.write_text(data, encoding="utf-8")
            command = [
                sys.executable, str(candidate), fixture.name,
                *options,
            ]
            expected = {
                "exit": code, "stdout": output, "stderr": errors,
            }
            try:
                r = subprocess.run(
                    command, cwd=folder, capture_output=True,
                    text=True, encoding="utf-8", timeout=5,
                )
                actual = {
                    "exit": r.returncode, "stdout": r.stdout,
                    "stderr": r.stderr,
                }
            except subprocess.TimeoutExpired:
                actual = {"error": "timeout"}
            results.append({
                "id": name, "input": data, "args": options,
                "expected": expected, "actual": actual,
                "passed": matches(actual, expected, name == "A1"),
            })

    unchanged = before == candidate.read_bytes()
    return {
        "stage": stage,
        "source_sha256": hashlib.sha256(before).hexdigest(),
        "candidate_unchanged": unchanged,
        "passed": unchanged and all(c["passed"] for c in results),
        "cases": results,
    }


def save(report: dict, path: Path) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    candidate, evidence = map(Path, sys.argv[1:])
    report = run_cases(candidate, "golden")
    save(report, evidence)
    print("PASS" if report["passed"] else "FAIL")
    raise SystemExit(0 if report["passed"] else 1)
