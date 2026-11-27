"""할 일 목록을 다루는 작은 MCP 서버 (stdio)."""
from mcp.server.mcpserver import MCPServer

server = MCPServer("todo")

TODOS = [
    {"id": 1, "title": "장보기", "done": False},
    {"id": 2, "title": "블로그 쓰기", "done": True},
]


@server.tool()
def list_todos(done: bool | None = None) -> list[dict]:
    """할 일 목록을 돌려준다. done을 주면 완료 여부로 거른다."""
    return [t for t in TODOS if done is None or t["done"] == done]


@server.tool()
def add_todo(title: str) -> dict:
    """새 할 일을 추가하고 추가된 항목을 돌려준다."""
    todo = {"id": max(t["id"] for t in TODOS) + 1, "title": title, "done": False}
    TODOS.append(todo)
    return todo


@server.resource("todo://summary")
def summary() -> str:
    """완료/미완료 개수 요약."""
    done = sum(t["done"] for t in TODOS)
    return f"전체 {len(TODOS)}개, 완료 {done}개, 남음 {len(TODOS) - done}개"


@server.prompt()
def plan_day(focus: str) -> str:
    """오늘 계획을 세우는 프롬프트 템플릿."""
    return f"남은 할 일을 보고 '{focus}'에 집중하는 오늘 계획을 세 줄로 세워 줘."


if __name__ == "__main__":
    server.run()  # 기본 transport는 stdio
