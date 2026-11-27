from typing_extensions import TypedDict
from langgraph.errors import NodeError
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.types import Command, RetryPolicy


class S(TypedDict, total=False):
    result: str


def flaky(state: S, runtime: Runtime):
    n = runtime.execution_info.node_attempt
    print("  시도", n)
    if n < 3:
        raise ConnectionError("잠깐 끊김")
    return {"result": f"{n}번째에 성공"}


def broken(state: S):
    raise ConnectionError("계속 끊김")


def on_error(state: S, error: NodeError) -> Command:
    return Command(
        update={"result": f"대체 처리: {error.error}"},
        goto=END)


fast = RetryPolicy(max_attempts=3, initial_interval=0.01,
                   retry_on=ConnectionError)

g = StateGraph(S)
g.add_node("flaky", flaky, retry_policy=fast)
g.add_edge(START, "flaky")
g.add_edge("flaky", END)
print(g.compile().invoke({}))

g2 = StateGraph(S)
g2.add_node("broken", broken, retry_policy=fast,
            error_handler=on_error)
g2.add_edge(START, "broken")
g2.add_edge("broken", END)
print(g2.compile().invoke({}))

g3 = StateGraph(S)
g3.add_node("slow", lambda s: {}, timeout=5)
g3.add_edge(START, "slow")
try:
    g3.compile()
except Exception as e:
    print(type(e).__name__, str(e)[:70])
