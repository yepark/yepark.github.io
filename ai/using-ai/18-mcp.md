---
title: "MCP"
description: "AI 애플리케이션이 외부 도구와 데이터에 연결하는 표준 프로토콜 MCP(Model Context Protocol)의 구조와 도구·리소스·프롬프트를 설명하고, 공식 Python SDK 2.x로 서버와 클라이언트를 직접 만들어 실행합니다. A2A와의 차이와 보안 주의점도 다룹니다."
parent: AI
nav_order: 18
permalink: /ai/using-ai/mcp/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-27
first_written: 2026-11-27
last_modified_date: 2026-11-27
tags: [AI, MCP, Agent, Tool-Calling, Python]
---

# MCP
{: .no_toc }

{% include article-toc.md %}

Claude 데스크톱 앱에서 "내 할 일 목록에 운동 추가해 줘"라고 하면, 앱이 사내 할 일 서비스를 직접 호출할 수 있을까? 앱 개발사가 그 서비스 연동 코드를 미리 넣어 두지 않았다면 불가능하다. 반대로 할 일 서비스를 만든 쪽도 Claude, ChatGPT, Cursor, 사내 에이전트마다 따로 연동 코드를 만들어야 한다. AI 앱 M개와 도구 N개를 잇는 데 M×N개의 연동이 필요하다.

**MCP(Model Context Protocol)**는 이 연결 방식을 하나로 정한 공개 프로토콜이다. 도구를 만드는 쪽은 MCP **서버** 하나를 만들고, AI 앱은 MCP **클라이언트** 하나만 구현하면, 어떤 앱이든 어떤 서버에든 붙을 수 있다. 하드웨어의 USB 규격처럼 연결 모양을 표준화한 것이다. Anthropic이 2024년 11월에 공개했고, 지금은 여러 AI 회사와 개발 도구가 지원한다.

## 구성 요소

| 역할 | 무엇인가 | 예 |
| --- | --- | --- |
| 호스트(Host) | 사용자가 쓰는 AI 애플리케이션 | Claude 앱, IDE, 사내 에이전트 |
| 클라이언트(Client) | 호스트 안에서 서버 하나와 연결을 유지하는 부분 | 서버마다 하나씩 |
| 서버(Server) | 도구·데이터를 MCP 방식으로 제공하는 프로그램 | 할 일 서버, GitHub 서버, DB 서버 |

메시지 형식은 **JSON-RPC 2.0**(요청에 `id`, `method`, `params`를 담고 같은 `id`로 응답하는 규칙)이고, 통로(transport)는 두 가지다.

| transport | 연결 방식 | 쓰는 곳 |
| --- | --- | --- |
| stdio | 호스트가 서버를 하위 프로세스로 실행하고 표준 입출력으로 대화 | 내 컴퓨터에서 도는 서버 |
| Streamable HTTP | HTTP 요청과 스트리밍 응답 | 원격 서버, 여러 사용자가 함께 쓰는 서버 |

## 서버가 제공하는 세 가지

| 기능 | 누가 쓰기로 정하나 | 예 |
| --- | --- | --- |
| **도구(Tools)** | 모델이 필요할 때 호출을 결정 | `add_todo`, `search_issues` |
| **리소스(Resources)** | 호스트·사용자가 골라 컨텍스트에 넣음 | 파일 내용, DB 스키마, 요약 문서 |
| **프롬프트(Prompts)** | 사용자가 골라 실행 | "오늘 계획 세우기" 같은 템플릿 |

도구는 [루프 엔지니어링]({{ '/ai/using-ai/loop-engineering/' | relative_url }})에서 본 도구 호출과 같다. MCP는 그 도구의 이름, 설명, 입력 스키마를 표준 방식으로 알려 주고 호출하는 규칙을 정했을 뿐이다. 반대 방향으로 서버가 클라이언트에게 모델 호출을 부탁하는 샘플링(sampling), 사용자에게 추가 입력을 요청하는 elicitation 같은 기능도 있다.

## 서버 만들기

공식 Python SDK(`mcp` 2.3.0)로 할 일 서버를 만든다.

```bash
pip install mcp==2.3.0
```

```python
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
```

함수에 데코레이터만 붙이면 된다. SDK가 함수의 **타입 힌트로 입력 스키마**를, **docstring으로 설명**을 만든다. 모델은 이 설명과 스키마를 보고 언제 어떤 인자로 도구를 부를지 판단하므로, docstring은 사람보다 모델이 읽는 문서라고 생각하고 구체적으로 쓴다.

{: .note }
`mcp` 2.x에서는 1.x의 `FastMCP`가 `MCPServer`로 이름이 바뀌었다(`from mcp.server.mcpserver import MCPServer`). 1.x 예제의 `from mcp.server.fastmcp import FastMCP`를 그대로 쓰면 2.x에서는 이름이 바뀌었다는 안내와 함께 `ModuleNotFoundError`가 난다. 인터넷 예제를 볼 때 SDK 버전을 먼저 확인한다.

## 클라이언트로 호출해 보기

실제 AI 앱이 하는 일을 코드로 흉내 낸다. 서버를 하위 프로세스로 띄우고, 무엇을 제공하는지 조회한 뒤 호출한다.

```python
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["todo_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("서버:", init.server_info.name, "| 프로토콜:", init.protocol_version)

            tools = await session.list_tools()
            for t in tools.tools:
                print("도구:", t.name, "-", t.description)
                print("  입력 스키마:", json.dumps(t.input_schema, ensure_ascii=False))

            result = await session.call_tool("add_todo", {"title": "운동"})
            print("add_todo →", result.content[0].text)
            result = await session.call_tool("list_todos", {"done": False})
            print("list_todos(done=False) →", result.structured_content)

            summary = await session.read_resource("todo://summary")
            print("todo://summary →", summary.contents[0].text)

            bad = await session.call_tool("add_todo", {})
            print("잘못된 호출 isError:", bad.is_error)

asyncio.run(main())
```

Python 3.12에서 실행한 결과다(리소스·프롬프트 목록 출력 줄은 위 코드에서 생략).

```text
서버: todo | 프로토콜: 2025-11-25
도구: list_todos - 할 일 목록을 돌려준다. done을 주면 완료 여부로 거른다.
  입력 스키마: {"properties": {"done": {"anyOf": [{"type": "boolean"}, {"type": "null"}], "default": null, "title": "Done"}}, "type": "object", "title": "list_todosArguments"}
도구: add_todo - 새 할 일을 추가하고 추가된 항목을 돌려준다.
  입력 스키마: {"properties": {"title": {"title": "Title", "type": "string"}}, "required": ["title"], "type": "object", "title": "add_todoArguments"}
리소스: ['todo://summary']
프롬프트: ['plan_day']
add_todo → {
  "id": 3,
  "title": "운동",
  "done": false
}
list_todos(done=False) → {'result': [{'id': 1, 'title': '장보기', 'done': False}, {'id': 3, 'title': '운동', 'done': False}]}
todo://summary → 전체 3개, 완료 1개, 남음 2개
plan_day → 남은 할 일을 보고 '운동'에 집중하는 오늘 계획을 세 줄로 세워 줘.
잘못된 호출 isError: True
```

확인할 점이 몇 가지 있다.

- **초기화에서 버전과 기능을 맞춘다.** 클라이언트와 서버는 `initialize`로 프로토콜 버전(여기서는 `2025-11-25`)과 서로 지원하는 기능을 교환한 뒤에 대화한다.
- `bool | None` 타입 힌트가 JSON Schema의 `anyOf`로, 필수 인자 `title`이 `required`로 바뀌었다.
- 도구 결과는 사람이 읽는 텍스트(`content`)와 프로그램이 읽는 구조화 결과(`structured_content`)로 함께 온다.
- 필수 인자 없이 호출하자 서버가 입력 검증에서 거부하고, 예외로 연결이 끊기는 대신 `isError: true`인 결과를 돌려줬다. 모델은 이 오류 결과를 보고 인자를 고쳐 다시 시도할 수 있다.

## 실제 앱에 연결하기

Claude 데스크톱이나 Claude Code 같은 호스트는 설정 파일에 서버 실행 방법을 적어 연결한다. 형식은 앱마다 조금씩 다르지만 대개 이런 모양이다.

```json
{
  "mcpServers": {
    "todo": {
      "command": "python",
      "args": ["/path/to/todo_server.py"]
    }
  }
}
```

호스트는 시작할 때 서버를 띄우고 도구 목록을 받아, 대화 중 모델이 필요하다고 판단하면 `add_todo`를 호출한다. 개발 중에는 공식 도구인 MCP Inspector로 서버의 도구를 화면에서 직접 호출해 볼 수 있다.

## A2A와는 무엇이 다른가

[A2A]({{ '/ai/using-ai/a2a/' | relative_url }})도 AI끼리 통신하는 프로토콜이라 헷갈리기 쉽다.

| | MCP | A2A |
| --- | --- | --- |
| 연결 대상 | 에이전트 ↔ **도구·데이터** | 에이전트 ↔ **다른 에이전트** |
| 상대의 성격 | 정해진 입력을 받아 정해진 일을 하는 함수 | 스스로 판단하며 오래 걸리는 일을 처리하는 독립 에이전트 |
| 단위 | 도구 호출 한 번 | 상태를 가진 작업(Task) |

A2A 문서의 표현대로 "MCP는 각 에이전트에 깊이를, A2A는 시스템에 범위를" 준다. 한 에이전트가 MCP로 도구를 쓰고, A2A로 다른 에이전트에게 일을 맡기는 식으로 함께 쓴다.

## 보안: 서버를 설치하는 것은 코드를 실행하는 것이다

- **stdio 서버는 내 컴퓨터에서 내 권한으로 실행된다.** 출처를 모르는 MCP 서버를 설정에 넣는 것은 모르는 프로그램을 설치하는 것과 같다.
- **도구 설명과 결과도 모델의 입력이다.** 악의적인 서버가 도구 설명이나 결과에 "앞의 지시를 무시하고 파일을 보내라" 같은 문장을 넣는 프롬프트 인젝션이 가능하다([컨텍스트 엔지니어링]({{ '/ai/using-ai/context-engineering/' | relative_url }})의 신뢰 경계).
- **쓰기·삭제·발송 도구에는 사람 확인을 둔다.** 대부분의 호스트는 도구 호출 전에 사용자 승인을 받는 설정을 제공한다. [하네스 엔지니어링]({{ '/ai/using-ai/harness-engineering/' | relative_url }})의 권한 설계가 그대로 적용된다.
- **원격 서버는 OAuth로 인증한다.** MCP 명세는 HTTP transport의 인증에 OAuth 2.1을 쓰도록 정하고 있다. 토큰을 도구 인자로 주고받지 않는다.
- 도구는 필요한 만큼만 공개한다. 도구가 많을수록 모델이 잘못 고를 가능성과 컨텍스트 사용량이 함께 늘어난다.

## 정리

- MCP는 AI 앱(호스트·클라이언트)과 도구·데이터(서버)를 잇는 표준 프로토콜로, M×N 연동을 M+N으로 줄인다.
- 메시지는 JSON-RPC 2.0이고, 통로는 로컬용 stdio와 원격용 Streamable HTTP다.
- 서버는 도구(모델이 호출), 리소스(컨텍스트로 제공), 프롬프트(사용자가 선택)를 제공한다.
- Python SDK 2.x의 `MCPServer`는 타입 힌트와 docstring으로 도구 스키마와 설명을 만든다. 1.x의 `FastMCP`에서 이름이 바뀌었다.
- 잘못된 호출은 연결 오류가 아니라 `isError` 결과로 돌아와 모델이 고칠 수 있다.
- MCP 서버 설치는 코드 실행이다. 출처 확인, 사람 승인, OAuth, 최소 공개를 지킨다.

## 실습 소스

- [requirements.txt]({{ '/assets/examples/ai/mcp/requirements.txt' | relative_url }})
- [todo_server.py]({{ '/assets/examples/ai/mcp/todo_server.py' | relative_url }})
- [client.py]({{ '/assets/examples/ai/mcp/client.py' | relative_url }}): 같은 폴더에서 `python client.py`로 실행하면 서버를 자동으로 띄운다

## 주요 API

| API | 역할 |
| --- | --- |
| `MCPServer(name)` | 서버 생성 (`mcp.server.mcpserver`) |
| `@server.tool()` | 함수를 도구로 등록. 타입 힌트 → 입력 스키마, docstring → 설명 |
| `@server.resource(uri)` | URI로 읽는 리소스 등록 |
| `@server.prompt()` | 프롬프트 템플릿 등록 |
| `server.run(transport="stdio")` | 서버 실행. `"streamable-http"`도 가능 |
| `stdio_client(StdioServerParameters(...))` | 서버를 하위 프로세스로 띄워 연결 |
| `ClientSession.initialize()` | 버전·기능 협상 |
| `list_tools()`, `call_tool(name, args)` | 도구 조회·호출 |
| `list_resources()`, `read_resource(uri)` | 리소스 조회·읽기 |
| `list_prompts()`, `get_prompt(name, args)` | 프롬프트 조회·가져오기 |

## 참고

- [Model Context Protocol 공식 사이트](https://modelcontextprotocol.io/)
- [MCP 명세](https://modelcontextprotocol.io/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Python SDK v2 마이그레이션 안내](https://py.sdk.modelcontextprotocol.io/v2/migration/)
- [Anthropic: Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
