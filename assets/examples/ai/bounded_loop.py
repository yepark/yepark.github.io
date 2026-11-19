from collections import deque


def lookup(order_id, responses, max_attempts=2):
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if not order_id:
        return "needs_input", 0

    for attempt in range(1, max_attempts + 1):
        result = responses.popleft()
        if result["kind"] == "ok":
            if result.get("order_id") != order_id:
                return "failed", attempt
            if "status" not in result or "estimated_delivery" not in result:
                return "failed", attempt
            return "complete", attempt
        if result["kind"] != "timeout":
            return "failed", attempt

    return "exhausted", max_attempts


def success():
    return {"kind": "ok", "order_id": "A-100",
            "status": "shipped", "estimated_delivery": None}


cases = {
    "success": ("A-100", [success()]),
    "retry": ("A-100", [{"kind": "timeout"}, success()]),
    "missing": ("", []),
    "denied": ("A-100", [{"kind": "forbidden"}]),
    "exhausted": ("A-100", [{"kind": "timeout"}] * 2),
}
for name, (order_id, responses) in cases.items():
    state, attempts = lookup(order_id, deque(responses))
    print(f"{name}: {state}, attempts={attempts}")
