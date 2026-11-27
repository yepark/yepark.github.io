import asyncio
import time
from typing_extensions import TypedDict
from langgraph.errors import NodeTimeoutError
from langgraph.graph import StateGraph, START, END


class S(TypedDict, total=False):
    a: str
    b: str


async def fetch_a(state: S):
    await asyncio.sleep(0.5)
    return {"a": "A"}


async def fetch_b(state: S):
    await asyncio.sleep(0.5)
    return {"b": "B"}


async def too_slow(state: S):
    await asyncio.sleep(2)
    return {"a": "늦음"}


g = StateGraph(S)
g.add_node("fetch_a", fetch_a)
g.add_node("fetch_b", fetch_b)
g.add_edge(START, "fetch_a")
g.add_edge(START, "fetch_b")
app = g.compile()

g2 = StateGraph(S)
g2.add_node("too_slow", too_slow, timeout=0.3)
g2.add_edge(START, "too_slow")
slow = g2.compile()


async def main():
    t = time.perf_counter()
    async for u in app.astream({}, stream_mode="updates"):
        print(u)
    print(f"걸린 시간 {time.perf_counter() - t:.1f}초")
    try:
        await slow.ainvoke({})
    except NodeTimeoutError as e:
        print("NodeTimeoutError:", e.node, e.kind,
              e.run_timeout)

asyncio.run(main())
