import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
    )
    args = parser.parse_args()

    try:
        rows = args.path.read_text(encoding="utf-8").splitlines()
        total = sum(int(row) for row in rows)
    except (OSError, ValueError):
        print("invalid input", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps({"total": total}))
    else:
        print(f"total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
