import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from verify import run_cases, save


def run_demo(scenario: str, evidence: Path) -> None:
    source = Path(__file__).with_name("report.py").read_text(
        encoding="utf-8",
    )
    bad = source.replace(
        'json.dumps({"total": total})',
        'json.dumps({"sum": total})',
        1,
    )
    regression = source.replace("total={total}", "sum={total}", 1)
    versions = {
        "repair": [bad, source],
        "regression": [regression],
        "limit": [bad, bad],
    }
    evidence.mkdir()

    with TemporaryDirectory() as folder:
        candidate = Path(folder) / "report.py"
        for attempt, version in enumerate(versions[scenario], 1):
            candidate.write_text(version, encoding="utf-8")
            quick = run_cases(candidate, "quick")
            save(quick, evidence / f"{attempt}-quick.json")
            summary = "PASS" if quick["passed"] else "FAIL"
            print(f"attempt={attempt} quick={summary}")
            if not quick["passed"]:
                continue

            golden = run_cases(candidate, "golden")
            save(golden, evidence / f"{attempt}-golden.json")
            if golden["passed"]:
                print("golden=PASS decision=VERIFIED")
            else:
                failed = [
                    c["id"] for c in golden["cases"]
                    if not c["passed"]
                ]
                print(f"golden=FAIL cases={','.join(failed)}")
                print("decision=NEEDS_REVISION")
            return
    print("decision=ESCALATE reason=attempt_limit")


parser = argparse.ArgumentParser()
parser.add_argument("scenario", choices=(
    "repair", "regression", "limit",
))
parser.add_argument("evidence", type=Path)
args = parser.parse_args()
run_demo(args.scenario, args.evidence)
