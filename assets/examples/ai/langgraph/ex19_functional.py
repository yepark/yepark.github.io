from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import Command, interrupt

calls = {"n": 0}


@task
def write_essay(topic: str) -> str:
    calls["n"] += 1          # 비싼 작업이라고 생각하자
    return f"{topic}에 관한 글"


@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    essay = write_essay(topic).result()
    ok = interrupt({"검토": essay})
    return {"essay": essay, "approved": ok}


cfg = {"configurable": {"thread_id": "f1"}}
for part in workflow.stream("고양이", cfg):
    print(part)
print("task 실행 횟수:", calls["n"])
print(workflow.invoke(Command(resume=True), cfg))
print("task 실행 횟수:", calls["n"])
