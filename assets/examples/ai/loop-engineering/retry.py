import random


class Timeout(Exception): pass
class RateLimited(Exception):
    def __init__(self, after):
        self.after = after
class NotFound(Exception): pass
class Forbidden(Exception): pass


RETRYABLE = (Timeout, RateLimited)


def classify(exc):
    if isinstance(exc, RETRYABLE):
        return "retryable"
    return "fatal"


class FaultyTool:
    """미리 정한 순서로 실패를 주입하는 도구"""
    def __init__(self, faults):
        self.faults = list(faults)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        f = self.faults.pop(0) if self.faults else None
        if f:
            raise f
        return {"status": "shipped"}


def backoff(n, rng, base=0.5, cap=8.0):
    # 지수 백오프 + full jitter
    return rng.uniform(0, min(cap, base * 2 ** n))


def call_with_retry(tool, rng, sleeps,
                    max_attempts=4):
    for n in range(max_attempts):
        try:
            return "ok", tool()
        except Exception as e:
            kind = classify(e)
            name = type(e).__name__
            if kind == "fatal":
                return "fatal", name
            if n == max_attempts - 1:
                return "exhausted", name
            wait = backoff(n, rng)
            if isinstance(e, RateLimited):
                wait = max(wait, e.after)
            sleeps.append(round(wait, 2))


class Breaker:
    """연속 실패가 쌓이면 잠시 호출을 막는다"""
    def __init__(self, limit=3, cooldown=2):
        self.limit, self.cooldown = limit, cooldown
        self.fails, self.blocked = 0, 0

    def call(self, fn):
        if self.blocked > 0:
            self.blocked -= 1
            return "open", None
        result = fn()
        if result[0] == "ok":
            self.fails = 0
        else:
            self.fails += 1
            if self.fails >= self.limit:
                self.blocked = self.cooldown
                self.fails = 0
        return result


def as_tool_result(status, value):
    """루프 안에서 모델에게 돌려줄 관찰"""
    if status == "ok":
        return {"content": value}
    hint = {"fatal": "다시 시도해도 안 됨",
            "exhausted": "잠시 뒤 다시"}
    return {"content": f"{value}: {hint[status]}",
            "is_error": True}


if __name__ == "__main__":
    cases = {
        "timeout 2번 뒤 성공":
            [Timeout(), Timeout()],
        "rate limit(3초)":
            [RateLimited(3.0)],
        "권한 없음": [Forbidden()],
        "없는 주문": [NotFound()],
        "timeout 계속": [Timeout()] * 9,
    }
    for label, faults in cases.items():
        rng = random.Random(42)
        sleeps = []
        tool = FaultyTool(faults)
        st, val = call_with_retry(tool, rng, sleeps)
        print(f"{label}: {st} calls={tool.calls}"
              f" sleeps={sleeps}")
        print("   ->", as_tool_result(st, val))

    print("-- circuit breaker --")
    br = Breaker(limit=3, cooldown=2)
    down = FaultyTool([Timeout()] * 12)
    for i in range(1, 7):
        st, _ = br.call(lambda: call_with_retry(
            down, random.Random(0), []))
        print(f"요청 {i}: {st} (도구 호출 누적"
              f" {down.calls})")
