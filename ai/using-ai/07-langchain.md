---
title: "LangChain"
description: "LangChain 설치, 메시지, 모델 응답, 도구 등록과 에이전트 실행을 작은 Python 예제로 차근차근 설명합니다."
parent: AI
nav_order: 7
permalink: /ai/using-ai/langchain/
last_modified_date: 2026-11-17
---

# LangChain
{: .no_toc }

{% include article-toc.md %}

AI 앱을 만들려면 사용자 문장을 모델에 전달하고, 응답을 꺼내고, 필요하면 검색이나 계산 함수를 연결해야 한다. LangChain은 이때 자주 사용하는 연결 부품과 에이전트 실행 구조를 제공하는 Python·JavaScript 프레임워크다. 이 글은 Python으로 시작한다.

## 이 글에서 만들 것

먼저 질문 한 번에 응답을 받는 프로그램을 만든다. 다음에는 곱셈 도구를 등록하고 모델이 그 도구를 선택할 수 있는 에이전트로 확장한다.

```text
첫 단계: 질문 → 모델 → 답변
다음 단계: 질문 → 모델 → 계산 도구 → 모델 → 답변
```

LangChain은 모델 자체가 아니다. 사용할 모델은 별도로 선택하고 해당 제공자의 접근 권한을 준비해야 한다. 온라인 모델 호출에는 제공자의 사용 요금이 적용될 수 있다.

## Python 환경 준비하기

공식 quickstart의 Python 3.11 이상 환경을 기준으로 진행한다. `python3.11` 명령이 없다면 해당 Python을 먼저 설치하고 경로를 확인한다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U langchain langchain-openai
```

가상 환경은 현재 프로젝트에서 쓸 Python 패키지를 따로 모으는 공간이다. 설치가 끝나면 다음 명령으로 버전을 기록한다.

```bash
python -m pip show langchain langchain-openai
```

본문은 공식 문서에서 확인한 `init_chat_model`, `create_agent` API 구조를 사용한다. 예전 강의의 클래스 이름이 다르면 같은 코드에 섞지 말고 설치한 버전의 문서를 확인한다.

## 키와 모델 이름 설정하기

다음은 OpenAI 연동을 선택했을 때의 예시다. 다른 제공자를 사용한다면 통합 패키지와 환경 변수도 그 제공자에 맞춰 바꾼다.

```bash
export OPENAI_API_KEY="발급받은-키"
export LLM_MODEL="계정에서-사용할-수-있는-모델-ID"
```

`LLM_MODEL`은 이 글에서 만든 설정 이름이다. 실제로 사용할 모델 ID를 넣어야 하며, 설명 문구를 그대로 입력하면 모델을 찾을 수 없다는 오류가 난다. 키를 코드나 Git 저장소에 넣지 않는다.

## 1. 모델 한 번 호출하기

다음을 `hello.py`에 저장한다.

```python
import os
from langchain.chat_models import init_chat_model

model = init_chat_model(
    os.environ["LLM_MODEL"],
    model_provider="openai",
)

response = model.invoke([
    {"role": "system", "content": "Python 초보자에게 두 문장으로 설명하세요."},
    {"role": "user", "content": "리스트는 무엇인가요?"},
])

print(response.content)
```

터미널에서 실행한다.

```bash
python hello.py
```

`os.environ`은 셸에서 설정한 값을 읽는다. `init_chat_model`은 선택한 제공자의 모델 객체를 준비한다. `invoke`는 입력을 전달하고 응답이 올 때까지 기다리는 동기 호출이다.

`response`는 문자열만 들어 있는 값이 아니라 모델 메시지 객체다. 일반적인 텍스트 예제에서는 `content`를 읽는다. 모델이나 설정에 따라 content block이 포함될 수 있으므로 운영 코드에서는 반환 형식을 확인한다.

## 2. 메시지의 역할 이해하기

| 역할 | 담는 내용 | 예 |
| --- | --- | --- |
| system | 이 대화에서 따를 지침 | 초보자에게 설명하기 |
| user | 사용자의 현재 질문 | 리스트가 무엇인가요? |
| assistant | 모델이 앞서 응답한 내용 | 리스트는 여러 값을… |
| tool | 외부 함수의 실행 결과 | 계산 결과 56088 |

후속 질문에서 이전 답변이 필요하다면 그 이력을 함께 제공하거나 에이전트의 저장 기능을 구성해야 한다. 별도의 `invoke`를 했다는 이유만으로 앞선 대화가 자동 보관된다고 생각하지 않는다.

## 3. 평범한 함수를 도구로 등록하기

```python
from langchain.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

print(multiply.invoke({"a": 123, "b": 456}))
```

예상 출력은 `56088`이다. 이 코드는 모델 없이 도구만 시험한다. 함수명, 타입 표기, 설명 문자열은 모델이 도구를 선택하고 올바른 인자를 만드는 데 사용된다.

본문의 Python 코드 문법과 이 도구의 단독 실행은 확인했다. 실제 모델 응답과 에이전트의 도구 선택은 제공자 키를 사용해 호출하지 않았으므로, 독자의 모델과 계정 환경에서 추가로 확인해야 한다.

도구 자체가 잘못됐다면 에이전트를 붙여도 정확한 답을 얻기 어렵다. 먼저 도구의 입력과 결과를 독립적으로 검증하는 이유다.

## 4. 모델과 도구 연결하기

`hello.py`의 모델을 만든 코드와 방금 정의한 `multiply` 뒤에 다음을 연결한다.

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[multiply],
    system_prompt=(
        "곱셈 요청은 multiply 도구로 계산하고, "
        "결과를 한국어 한 문장으로 답하세요."
    ),
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "123과 456을 곱해 주세요."}
    ]
})

print(result["messages"][-1].content)
```

모델은 도구 호출 요청을 만들 수 있다. 프레임워크는 실제 함수를 실행하고 결과를 다시 모델에 전달한다. 이후 모델이 최종 문장을 생성한다. 도구를 연결했다고 모든 질문에서 반드시 도구를 호출하는 것은 아니며, 실제 호출 여부는 실행 기록으로 확인한다.

## 5. 중간 메시지 확인하기

```python
for message in result["messages"]:
    print(message.type)
    print(message.content)
    print(getattr(message, "tool_calls", None))
```

최종 답이 맞는지만 보지 말고 계산 도구가 실제로 선택됐는지 본다. `tool_calls`는 모델이 요청한 호출 목록을 확인하는 단서다. 도구 결과 메시지와 그 뒤 모델 응답을 순서대로 읽으면 에이전트 루프가 보인다.

실제 서비스에서는 원문 전체를 로그에 남기기보다 필요한 호출 이름, 성공 여부, 시간 같은 정보를 선별한다.

## 자주 만나는 오류를 찾는 순서

`ModuleNotFoundError`가 나면 현재 가상 환경에 패키지를 설치했는지 확인한다. `python -m pip`를 사용하면 다른 Python의 pip로 설치하는 혼동을 줄일 수 있다.

키 관련 오류라면 실행한 터미널에 환경 변수가 설정됐는지 확인한다. 모델 접근 오류라면 실제 모델 ID와 계정 권한을 확인한다. 도구 입력 오류라면 함수의 인자 이름과 타입, 모델이 만든 인자를 비교한다.

질문을 반복하면 비용이 발생할 수 있으므로 오류 메시지를 읽지 않은 채 무한 재시도하지 않는다. 외부 함수를 실행하는 단계에는 입력 검증과 시간 제한도 둔다.

## LangGraph로 넘어갈 시점

기본 에이전트로 시작해도 충분한 작업이 많다. 업무 순서가 고정돼 있거나, 조건 분기·승인·중단 후 재개를 직접 제어해야 한다면 그래프를 명시적으로 설계하는 편이 유리하다.

다음 편에서는 유료 모델 호출 없이도 실행 가능한 작은 LangGraph를 만들며 그 차이를 배운다.

→ [LangGraph 입문]({{ '/ai/using-ai/langgraph/' | relative_url }})

## 참고

- [LangChain: Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)
- [LangChain: Learn](https://docs.langchain.com/oss/python/learn)
