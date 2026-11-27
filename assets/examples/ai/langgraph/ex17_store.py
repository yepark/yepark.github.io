from dataclasses import dataclass
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
store.put(("u1", "prefs"), "lang", {"v": "Python"})
store.put(("u1", "prefs"), "tone", {"v": "짧게"})
store.put(("u2", "prefs"), "lang", {"v": "Swift"})
for it in store.search(("u1", "prefs")):
    print(it.namespace, it.key, it.value)
print(store.get(("u2", "prefs"), "lang").value)


@dataclass
class Ctx:
    user_id: str


def reply(state: MessagesState, runtime: Runtime[Ctx]):
    ns = (runtime.context.user_id, "prefs")
    text = state["messages"][-1].content
    if text.startswith("기억:"):
        runtime.store.put(ns, "note",
                          {"v": text[3:].strip()})
        return {"messages": [("ai", "기억했어요")]}
    got = runtime.store.get(ns, "note")
    memo = got.value["v"] if got else "없음"
    return {"messages": [("ai", f"메모: {memo}")]}


g = StateGraph(MessagesState, context_schema=Ctx)
g.add_node("reply", reply)
g.add_edge(START, "reply")
g.add_edge("reply", END)
app = g.compile(checkpointer=InMemorySaver(),
                store=store)


def ask(thread, user, text):
    cfg = {"configurable": {"thread_id": thread}}
    out = app.invoke({"messages": [("user", text)]},
                     cfg, context=Ctx(user))
    n = len(out["messages"])
    print(thread, user, "→", out["messages"][-1].content,
          f"(이 thread 메시지 {n}개)")


ask("chat-A", "u1", "기억: 금요일 배포")
ask("chat-B", "u1", "내 메모 뭐였지?")   # 다른 thread
ask("chat-C", "u2", "내 메모 뭐였지?")   # 다른 사용자
