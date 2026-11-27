from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END
from langgraph.graph.message import add_messages

old = [HumanMessage("안녕", id="1"),
       AIMessage("반가워요", id="2")]
new = [AIMessage("반갑습니다!", id="2"),  # 같은 id → 교체
       HumanMessage("날씨 알려줘", id="3")]  # 새 id → 추가
for m in add_messages(old, new):
    print(m.type, m.id, m.content)

def bot(state: MessagesState):
    return {"messages": [("ai", "네, 말씀하세요.")]}

g = StateGraph(MessagesState)
g.add_node("bot", bot)
g.add_edge(START, "bot")
g.add_edge("bot", END)
out = g.compile().invoke(
    {"messages": [{"role": "user", "content": "저기요"}]})
for m in out["messages"]:
    print(type(m).__name__, repr(m.content))
