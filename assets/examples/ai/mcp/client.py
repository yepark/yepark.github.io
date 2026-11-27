"""MCP 서버를 하위 프로세스로 띄우고 기능을 조회·호출하는 클라이언트."""
import asyncio
import json
import sys

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

            res = await session.list_resources()
            print("리소스:", [str(r.uri) for r in res.resources])
            prompts = await session.list_prompts()
            print("프롬프트:", [p.name for p in prompts.prompts])

            result = await session.call_tool("add_todo", {"title": "운동"})
            print("add_todo →", result.content[0].text)
            result = await session.call_tool("list_todos", {"done": False})
            print("list_todos(done=False) →", result.structured_content)

            summary = await session.read_resource("todo://summary")
            print("todo://summary →", summary.contents[0].text)

            prompt = await session.get_prompt("plan_day", {"focus": "운동"})
            print("plan_day →", prompt.messages[0].content.text)

            bad = await session.call_tool("add_todo", {})
            print("잘못된 호출 isError:", bad.is_error, "|", bad.content[0].text[:80])


asyncio.run(main())
