# 가짜 작업자(fake worker)로 만든 작은 오케스트레이터.
# LLM은 쓰지 않는다. 작업자는 정해진 값을 돌려주는
# 결정적(deterministic) 함수다.
import asyncio
import sys
import time
import uuid
from dataclasses import dataclass

T0 = time.perf_counter()


def ms():
    return round((time.perf_counter() - T0) * 1000)


TRACE = []


def log(run, task, event, **kw):
    TRACE.append((ms(), run, task, event, kw))


# ---------- 계약(contract): 일을 맡길 때의 약속 ----------
@dataclass
class Task:
    id: str
    worker: str          # 누구에게 맡길까
    needs: tuple         # 결과에 꼭 있어야 하는 키
    timeout: float = 0.3  # 한 번 시도의 제한 시간(초)
    retries: int = 1     # 실패하면 몇 번 더 할까
    fallback: str = ""   # 끝내 실패하면 누구에게 넘길까

# ---------- 가짜 작업자들 ----------
CALLS = {}


async def spec():
    await asyncio.sleep(0.10)
    return {"cpu": "M4", "ram_gb": 16}


async def shop_a():
    await asyncio.sleep(0.15)
    return {"price": 1_590_000, "seen": "2026-11-26"}


async def shop_b():
    await asyncio.sleep(0.20)
    return {"price": 1_490_000, "seen": "2026-11-27"}


async def reviews():
    CALLS["reviews"] = CALLS.get("reviews", 0) + 1
    await asyncio.sleep(0.05)
    if CALLS["reviews"] == 1:      # 첫 호출만 실패
        raise ConnectionError("reset by peer")
    return {"score": 4.4}


async def stock():
    await asyncio.sleep(5)          # 항상 시간 초과
    return {"in_stock": True}


async def stock_cache():
    await asyncio.sleep(0.02)
    return {}                       # 필요한 키가 없다


WORKERS = {f.__name__: f for f in
           [spec, shop_a, shop_b, reviews,
            stock, stock_cache]}
COST = {"spec": 2, "shop_a": 2, "shop_b": 2,
        "reviews": 3, "stock": 3, "stock_cache": 1}

# ---------- 전체 예산 ----------
class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, limit):
        self.limit, self.spent = limit, 0

    def charge(self, cost):
        if self.spent + cost > self.limit:
            raise BudgetExceeded(
                f"{self.spent}+{cost}>{self.limit}")
        self.spent += cost

# ---------- 1. 작업 분해 ----------
def make_plan(goal):
    # 실습에서는 고정 규칙으로 계획을 만든다.
    return [
        Task("spec", "spec", ("cpu", "ram_gb")),
        Task("price_a", "shop_a", ("price", "seen")),
        Task("price_b", "shop_b", ("price", "seen")),
        Task("reviews", "reviews", ("score",)),
        Task("stock", "stock", ("in_stock",),
             fallback="stock_cache"),
    ]

# ---------- 2. 위임: 시간 제한, 재시도, 검증 ----------
async def call(run, t, worker, attempt, budget):
    budget.charge(COST[worker])
    log(run, t.id, "start", worker=worker,
        attempt=attempt, spent=budget.spent)
    async with asyncio.timeout(t.timeout):
        out = await WORKERS[worker]()
    missing = [k for k in t.needs if k not in out]
    if missing:                       # 결과 검증
        raise ValueError(f"missing {missing}")
    log(run, t.id, "ok", worker=worker)
    return out


async def run_task(run, t, sem, budget, humans):
    log(run, t.id, "queued")
    try:
        async with sem:               # 동시 실행 제한
            for n in range(1, t.retries + 2):
                try:
                    return await call(
                        run, t, t.worker, n, budget)
                except (TimeoutError, ConnectionError,
                        ValueError) as e:
                    log(run, t.id, "fail",
                        error=type(e).__name__)
                    await asyncio.sleep(0.05)
            if t.fallback:
                try:
                    return await call(
                        run, t, t.fallback, 1, budget)
                except (TimeoutError, ValueError) as e:
                    log(run, t.id, "fail",
                        error=f"{type(e).__name__}: {e}")
            log(run, t.id, "escalate")  # 사람에게
            humans.append(t.id)
            return {"status": "needs_human"}
    except BudgetExceeded as e:
        log(run, t.id, "over_budget", error=str(e))
        raise
    except asyncio.CancelledError:
        log(run, t.id, "cancelled")
        raise

# ---------- 3. 결과 합치기와 충돌 해결 ----------
def aggregate(res):
    report, notes = {}, []
    if "spec" in res:
        report["spec"] = res["spec"]
    prices = [res[k] for k in ("price_a", "price_b")
              if k in res and res[k].get("status") != "needs_human"]
    if len(prices) == 2 and \
            prices[0]["price"] != prices[1]["price"]:
        # 규칙: 더 최근에 확인한 값을 쓴다
        pick = max(prices, key=lambda p: p["seen"])
        notes.append(f"price conflict {prices[0]['price']}"
                     f" vs {prices[1]['price']}"
                     f" -> newest {pick['price']}")
        report["price"] = pick["price"]
    elif prices:
        report["price"] = prices[0]["price"]
    for k in ("reviews", "stock"):
        if k in res:
            report[k] = res[k]
    return report, notes

# ---------- 4. 오케스트레이터 ----------
async def orchestrate(goal, limit, max_parallel=2):
    run = uuid.uuid4().hex[:6]       # 상관관계 ID
    budget, humans = Budget(limit), []
    sem = asyncio.Semaphore(max_parallel)
    plan = make_plan(goal)
    print(f"run={run} plan={[t.id for t in plan]}")
    jobs = {}
    try:
        async with asyncio.TaskGroup() as tg:
            for t in plan:
                jobs[t.id] = tg.create_task(
                    run_task(run, t, sem, budget, humans))
    except* BudgetExceeded:
        log(run, "-", "budget_stop")
    res = {k: j.result() for k, j in jobs.items()
           if j.done() and not j.cancelled()
           and j.exception() is None}
    report, notes = aggregate(res)
    report["missing"] = [t.id for t in plan
                         if t.id not in res]
    return run, report, notes, humans, budget


def show(run, report, notes, humans, budget):
    for t, r, task, ev, kw in TRACE:
        extra = " ".join(f"{k}={v}" for k, v in kw.items())
        print(f"{t:5d}ms {r} {task:8s} {ev:11s} {extra}")
    print("report :", report)
    print("notes  :", notes)
    print("humans :", humans)
    print("budget :", f"{budget.spent}/{budget.limit}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    show(*asyncio.run(orchestrate("노트북 추천", limit)))
