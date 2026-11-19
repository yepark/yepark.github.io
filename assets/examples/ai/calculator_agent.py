"""Offline tool test by default; use --online to call the configured model."""
import argparse
import os

from langchain.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()
    if not args.online:
        assert multiply.invoke({"a": 123, "b": 456}) == 56088
        print("tool-only: 56088")
        return

    from langchain.agents import create_agent
    from langchain.chat_models import init_chat_model

    model = init_chat_model(
        os.environ["LLM_MODEL"], model_provider="openai",
        timeout=30, max_retries=0,
    )
    agent = create_agent(
        model=model, tools=[multiply],
        system_prompt="곱셈 요청은 multiply 도구로 계산하고 결과를 한국어로 답한다.",
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "123과 456을 곱해 주세요."}]},
        config={"recursion_limit": 10},
    )
    for message in result["messages"]:
        print(message.type, message.content)
        calls = getattr(message, "tool_calls", None)
        if calls:
            print("tool_calls:", calls)


if __name__ == "__main__":
    main()
