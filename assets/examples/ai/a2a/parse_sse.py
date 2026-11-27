import json
import sys

for line in sys.stdin:
    if not line.startswith("data: "):
        continue
    result = json.loads(line[6:])["result"]
    kind = next(iter(result))
    body = result[kind]
    state = body.get("status", {}).get("state", "")
    print(kind, state)
