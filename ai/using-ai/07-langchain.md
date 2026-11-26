---
title: "LangChain"
description: "LangChain 1.x의 메시지와 모델, Runnable과 LCEL, 구조화 출력, 도구 호출, 에이전트 상태를 가짜 모델과 실제 로컬 모델로 실행합니다."
parent: AI
nav_order: 7
permalink: /ai/using-ai/langchain/
date: 2026-11-17
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
last_modified_date: 2026-11-27
---

# LangChain
{: .no_toc }

{% include article-toc.md %}

고객이 "키보드가 고장 났어요. 환불해 주세요."라고 보냈다. 상담 화면에는 요약 한 줄이 필요하고, 자동 배정 프로그램에는 `category="환불"` 같은 정해진 값이 필요하다. 배정 기준을 정리해 모델에 주고, 응답을 받은 뒤, 프로그램이 읽을 자료형으로 바꾸는 일이 생긴다.

LangChain은 이 과정에서 쓰는 메시지, 모델 호출, 출력 변환, 도구 실행을 서로 연결하는 프레임워크다. 단계를 미리 정한 프로그램은 연결 순서를 코드로 작성한다. 모델의 판단에 따라 도구를 골라야 할 때는 에이전트가 도구 실행과 모델 재호출을 반복한다. 두 방식 모두 같은 채팅 모델과 도구 객체를 쓸 수 있다. [LangChain 모델 문서](https://docs.langchain.com/oss/python/langchain/models), [에이전트 문서](https://docs.langchain.com/oss/python/langchain/agents)

## 모델 응답을 직접 읽기

Python 3.12.16, `langchain` 1.5.2, `langchain-core` 1.8.5에서 실행했다. `GenericFakeChatModel`은 준비해 둔 답을 하나씩 꺼내 준다. API 키 없이 메시지가 어떻게 오가는지 볼 수 있다. 각 코드 블록을 절에서 지정한 파일 이름으로 저장한 뒤 실행한다.

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install langchain==1.5.2 langchain-core==1.8.5
```

다음을 `model_calls.py`에 저장하고 `python model_calls.py`로 실행한다.

```python
import asyncio
from langchain.messages import (
    SystemMessage, HumanMessage, AIMessage)
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)

fake = GenericFakeChatModel(messages=iter([
    "리스트는 여러 값을 순서대로 담는다.",
    "첫째 답", "둘째 답",
    "비동기 답",
]))

# 1) invoke: 메시지 객체 / 딕셔너리 / 튜플 모두 된다
msgs = [SystemMessage("두 문장으로 설명하세요."),
        {"role": "user", "content": "리스트란?"}]
r = fake.invoke(msgs)
print(type(r).__name__, "|", r.content)
print(r.content_blocks)

# 2) batch: 입력 여러 개를 한 번에
print([m.content for m in fake.batch(["질문1", "질문2"])])

# 3) ainvoke: 비동기 버전
print(asyncio.run(fake.ainvoke("질문")).content)
```

```text
AIMessage | 리스트는 여러 값을 순서대로 담는다.
[{'type': 'text', 'text': '리스트는 여러 값을 순서대로 담는다.'}]
['첫째 답', '둘째 답']
비동기 답
```

| 호출 | 무엇이 반환되나 | 쓸 때 |
| --- | --- | --- |
| `invoke(input)` | 응답 한 개 | 입력 하나를 처리한다. |
| `batch(inputs)` | 입력 순서와 대응하는 응답 목록 | 같은 단계를 여러 입력에 적용한다. |
| `ainvoke(input)` | `await`로 받는 응답 한 개 | 비동기 함수 안에서 기다린다. |
| `stream(input)` | 응답 조각을 내보내는 반복자 | 응답이 끝나기 전에 화면에 띄운다. |

이 예제의 `AIMessage`는 `content`에 문자열을 담고 `content_blocks`에서 이를 표준 텍스트 블록으로 보여 준다. 통합 모델의 응답에는 이미지, 도구 호출 등 다른 종류의 블록도 들어갈 수 있다. 사용량 정보는 모델이 제공할 때 `usage_metadata`에 들어간다. 글자 수와 토큰 수는 서로 다른 값이다. [메시지 문서](https://docs.langchain.com/oss/python/langchain/messages), [모델 문서](https://docs.langchain.com/oss/python/langchain/models)

| 메시지 | 넣는 정보 |
| --- | --- |
| `SystemMessage` | 응답 길이, 말투, 작업 범위 같은 지침 |
| `HumanMessage` | 사용자 질문과 입력 |
| `AIMessage` | 모델의 응답 내용과 도구 호출 요청 |
| `ToolMessage` | 실제 실행 결과와 대응하는 `tool_call_id` |

다음을 `model_stream.py`로 실행하면 조각을 더해 전체 응답으로 모을 수 있다.

```python
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)
fake = GenericFakeChatModel(messages=iter(
    ["리스트는 여러 값을 순서대로 담는다."]))
full = None
for chunk in fake.stream("리스트란?"):
    print(repr(chunk.content), end=" ")
    full = chunk if full is None else full + chunk
print()
print(type(full).__name__, "|", full.content)
```

```text
'리스트는' ' ' '여러' ' ' '값을' ' ' '순서대로' ' ' '담는다.'
AIMessageChunk | 리스트는 여러 값을 순서대로 담는다.
```

가짜 모델은 준비된 문장을 이처럼 나눠 보낸다. 실제 모델의 조각 경계는 모델과 제공자에 따라 달라진다. 도구 호출을 스트리밍하는 앱은 조각에 담긴 인자 문자열도 합쳐서 완성한 뒤 실행한다. [모델의 스트리밍 도구 호출](https://docs.langchain.com/oss/python/langchain/models#streaming-tool-calls)

## 어떤 패키지에서 무엇을 가져오나

| 패키지 | 여기서 맡는 역할 |
| --- | --- |
| `langchain` | `create_agent`, `init_chat_model`, 에이전트 미들웨어 |
| `langchain-core` | 메시지, 프롬프트, Runnable, 출력 변환의 공통 인터페이스 |
| 제공자별 통합 패키지 | `langchain-openai`, `langchain-anthropic`처럼 해당 제공자의 모델에 연결 |
| `langchain-community` | 커뮤니티 통합 모음. 필요한 통합의 설치 문서부터 확인 |
| `langchain-classic` | `LLMChain`과 같은 예전 API를 계속 쓰는 코드의 호환 경로 |
| `langgraph` | `create_agent`가 사용하는 실행 엔진. 노드, 상태, 체크포인터도 직접 구성 가능 |

실습 환경에서 `langchain.messages.HumanMessage`와 `langchain_core.messages.HumanMessage`는 같은 객체였다. 어댑터를 설치하지 않은 상태에서 `init_chat_model("openai:gpt-5")`로 초기화하면 `langchain-openai` 설치를 요구하는 `ImportError`가 났다. 제공자별 모델을 선택했다면 모델 ID, 통합 패키지, 인증 설정을 함께 확인한다. [모델 설정](https://docs.langchain.com/oss/python/langchain/models), [LangChain v1 변경 안내](https://docs.langchain.com/oss/python/migrate/langchain-v1)

## 프롬프트가 만드는 메시지 확인하기

`ChatPromptTemplate`은 변수에 값을 넣어 메시지 목록을 만든다. `MessagesPlaceholder`는 자리에 메시지 여러 개를 끼워 넣는다. 대화 기록을 여기에 주면 각 메시지의 역할을 유지할 수 있다.

다음을 `prompt.py`로 실행한다.

```python
from langchain_core.prompts import (
    ChatPromptTemplate, MessagesPlaceholder)

prompt = ChatPromptTemplate.from_messages([
    ("system", "{level}에게 {n}문장으로 설명하세요."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])
print(prompt.input_variables)

easy = prompt.partial(level="초등학생")
print(easy.input_variables)

value = easy.invoke({
    "n": 2,
    "history": [("human", "안녕"), ("ai", "안녕하세요!")],
    "question": "리스트란?",
})
for m in value.to_messages():
    print(f"{m.type:6} {m.content}")

try:
    prompt.invoke({"level": "초보자", "question": "?"})
except KeyError as e:
    print("KeyError:", str(e)[:70], "...")
```

```text
['history', 'level', 'n', 'question']
['history', 'n', 'question']
system 초등학생에게 2문장으로 설명하세요.
human  안녕
ai     안녕하세요!
human  리스트란?
KeyError: "Input to ChatPromptTemplate is missing variables {'n', 'history'}.  E ...
```

`partial(level="초등학생")`가 반환한 템플릿에서 `level`은 이미 채워져 있다. `n`과 `history`를 빠뜨린 호출은 모델에 도달하기 전에 `KeyError`로 끝났다. 오류 메시지에 나오는 변수 집합은 실행마다 표시 순서가 달라질 수 있다. 모델 답이 이상할 때도 프롬프트 객체에 값을 넣고 `to_messages()`를 호출하면 실제 입력을 확인할 수 있다. [ChatPromptTemplate API](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)

## Runnable과 LCEL로 단계를 잇기

`Runnable`은 `invoke`, `batch`, `stream`처럼 공통 실행 메서드를 갖는 객체다. 프롬프트와 모델처럼 종류가 달라도 각 출력과 다음 입력의 모양이 맞으면 연결할 수 있다. `|`로 그 연결을 표현하는 방식을 LCEL(LangChain Expression Language)이라고 한다. [Runnable API](https://reference.langchain.com/python/langchain-core/runnables)

다음을 `compose.py`로 실행한다.

```python
from langchain_core.runnables import (
    RunnableLambda, RunnableParallel, RunnablePassthrough)

clean = RunnableLambda(lambda s: s.strip())
upper = RunnableLambda(lambda s: s.upper())
chain = clean | upper
print(type(chain).__name__, chain.invoke("  hello  "))

both = RunnableParallel(
    length=RunnableLambda(len),
    words=RunnableLambda(lambda s: s.split()),
)
print(both.invoke("a b c"))

add = RunnablePassthrough.assign(
    n_chars=lambda d: len(d["question"]))
print(add.invoke({"question": "리스트란?"}))

# 딕셔너리는 자동으로 RunnableParallel이 된다
auto = clean | {"orig": RunnablePassthrough(),
                "up": upper}
print(auto.invoke(" hi "))
```

```text
RunnableSequence HELLO
{'length': 5, 'words': ['a', 'b', 'c']}
{'question': '리스트란?', 'n_chars': 5}
{'orig': 'hi', 'up': 'HI'}
```

| 구성 | 이 예제가 보여 주는 동작 |
| --- | --- |
| `RunnableLambda(fn)` | Python 함수에 공통 실행 메서드를 붙인다. |
| `a \| b` | `a`의 출력이 `b`의 입력이 된다. 두 객체는 `RunnableSequence`에 들어간다. |
| `RunnableParallel` | 같은 입력을 여러 갈래에 보내고, 이름별 결과를 딕셔너리에 모은다. |
| `RunnablePassthrough()` | 입력을 그대로 반환한다. |
| `RunnablePassthrough.assign(...)` | 딕셔너리의 기존 키를 유지하면서 계산한 키를 추가한다. |

LCEL 연결에 딕셔너리를 쓰면 LangChain이 그 자리를 `RunnableParallel`로 바꾼다. 예제의 `{ "orig": ..., "up": ... }`는 입력 문자열을 정리한 뒤 원문과 대문자 결과를 함께 돌려준다.

### 프롬프트, 모델, 출력 변환을 연결하기

`StrOutputParser`는 모델 메시지의 텍스트를 꺼낸다. 이 예제는 프롬프트에 딕셔너리를 넣고 최종 결과는 문자열로 받는다. 분기가 있는 경우 `RunnableBranch`는 앞에서부터 조건을 검사해 참이 된 첫 번째 항목을 고른다. 마지막 항목은 기본 경로다. 다음을 `route.py`로 실행한다.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch, RunnableLambda)
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel)

prompt = ChatPromptTemplate.from_messages(
    [("human", "{q}")])
model = FakeListChatModel(responses=["모델의 답"])
chain = prompt | model | StrOutputParser()
print(chain.invoke({"q": "안녕"}))
print([s.__class__.__name__ for s in chain.steps])

# 분기 1: RunnableBranch
branch = RunnableBranch(
    (lambda d: "코드" in d["q"],
     RunnableLambda(lambda d: "코드 담당")),
    RunnableLambda(lambda d: "일반 담당"),  # 기본값
)
print(branch.invoke({"q": "코드 리뷰"}),
      branch.invoke({"q": "날씨"}))

# 분기 2: 함수가 Runnable을 돌려주면 그것이 실행된다
code = RunnableLambda(lambda d: "코드 담당")
chat = RunnableLambda(lambda d: "일반 담당")
route = RunnableLambda(
    lambda d: code if "코드" in d["q"] else chat)
print(route.invoke({"q": "코드 리뷰"}))
```

```text
모델의 답
['ChatPromptTemplate', 'FakeListChatModel', 'StrOutputParser']
코드 담당 일반 담당
코드 담당
```

{: .tip }
실무에서는 최종 문자열만 시험하기 전에 단계 사이의 자료형을 확인한다. 예를 들어 `prompt.invoke(...).to_messages()`로 메시지를 확인하고, 도구 호출이나 토큰 사용량이 필요하면 `StrOutputParser` 앞에서 `AIMessage`를 확인한다.

### 실행 설정과 동시 호출

`configurable_fields`는 변경할 수 있는 값을 이름으로 노출한다. `configurable_alternatives`는 같은 자리의 실행 객체를 설정에 따라 고른다. `with_config`로 기본 설정을 묶거나, 한 번의 호출에 `config=`를 넘길 수 있다.

`batch`의 `max_concurrency`로 동시에 실행하는 입력 수를 제한할 수 있다. 아래는 인위적으로 0.5초씩 기다리는 함수 네 개의 실행이다. 출력된 시간은 인위적인 대기 함수의 실행 시간이다. 다음을 `config.py`로 실행한다.

```python
import time, asyncio
from langchain_core.runnables import (
    RunnableLambda, ConfigurableField)
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel)

# 1) 실행 시 바꿀 수 있는 필드
model = FakeListChatModel(responses=["A"]).configurable_fields(
    responses=ConfigurableField(id="answers"))
print(model.invoke("q").content)
print(model.invoke("q", config={
    "configurable": {"answers": ["B"]}}).content)

# 2) 갈아 끼울 수 있는 대안
alt = FakeListChatModel(responses=["기본 모델"]) \
    .configurable_alternatives(
        ConfigurableField(id="llm"), default_key="main",
        backup=FakeListChatModel(responses=["백업 모델"]))
print(alt.invoke("q").content,
      alt.with_config(configurable={"llm": "backup"})
         .invoke("q").content)

# 3) batch와 max_concurrency
slow = RunnableLambda(lambda x: time.sleep(0.5) or x)
for mc in (1, 4):
    t = time.perf_counter()
    slow.batch([1, 2, 3, 4], config={"max_concurrency": mc})
    print(f"max_concurrency={mc}: "
          f"{time.perf_counter() - t:.1f}s")
```

```text
A
B
기본 모델 백업 모델
max_concurrency=1: 2.0s
max_concurrency=4: 0.5s
```

여기서 대안 모델의 선택은 실행 전에 일어난다. 실행이 실패한 뒤 백업을 쓰는 경우에는 다음 절의 `with_fallbacks`를 쓴다. 제공자가 분당 처리할 수 있는 요청이나 토큰 수는 동시성 한도와 별개다. 여러 프로세스가 같은 키를 쓴다면 제공자 한도는 함께 고려해야 한다. [Runnable 설정 API](https://reference.langchain.com/python/langchain-core/runnables)

### 재시도와 대체 경로

`with_retry`는 지정한 오류가 나면 같은 단계를 다시 실행한다. `with_fallbacks`는 지정한 오류가 나면 순서대로 대안에 같은 입력을 넣는다. 다음을 `errors.py`로 실행한다.

```python
from langchain_core.runnables import RunnableLambda

calls = {"n": 0}
def flaky(x):
    calls["n"] += 1
    if calls["n"] < 3:
        raise ConnectionError(f"{calls['n']}번째 실패")
    return f"{calls['n']}번째에 성공: {x}"

safe = RunnableLambda(flaky).with_retry(
    retry_if_exception_type=(ConnectionError,),
    stop_after_attempt=3,
    wait_exponential_jitter=False,
)
print(safe.invoke("hi"))

def broken(x):
    raise TimeoutError("주 모델 응답 없음")
main = RunnableLambda(broken)
backup = RunnableLambda(lambda x: f"백업 답: {x}")
print(main.with_fallbacks([backup]).invoke("hi"))

try:
    RunnableLambda(lambda x: 1 / 0).with_retry(
        retry_if_exception_type=(ConnectionError,),
    ).invoke("x")
except ZeroDivisionError as e:
    print("재시도 안 함:", type(e).__name__)
```

```text
3번째에 성공: hi
백업 답: hi
재시도 안 함: ZeroDivisionError
```

{: .warning }
실무에서는 네트워크 호출처럼 일시적으로 실패할 수 있는 단계에 재시도를 한정한다. `stop_after_attempt=3`은 최초 실행을 포함해 세 번이다. 모델 호출에만 재시도를 두면 앞쪽 검색이나 외부 변경을 처음부터 되풀이하는 일을 피할 수 있다. 대체 경로에도 원래 단계와 같은 출력 검증을 적용한다. [RunnableRetry API](https://reference.langchain.com/python/langchain-core/runnables/retry/RunnableRetry)

### 연결 내부의 이벤트 보기

`stream`은 호출자가 받을 출력의 조각을 읽는다. `astream_events`는 내부 프롬프트, 모델, 파서의 시작·조각·종료 이벤트를 읽는다. 연결에 `run_name="greeter"`를 붙이면 바깥 실행을 그 이름으로 찾을 수 있다. 다음을 `events.py`로 실행한다.

```python
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)

model = GenericFakeChatModel(messages=iter(["안녕 하세요 반가워요"]))
chain = (ChatPromptTemplate.from_messages([("human", "{q}")])
         | model | StrOutputParser()).with_config(
             run_name="greeter")

async def main():
    async for ev in chain.astream_events(
            {"q": "hi"}, version="v2"):
        kind = ev["event"]
        if kind == "on_chat_model_stream":
            print(kind, repr(ev["data"]["chunk"].content))
        elif kind.endswith(("_start", "_end")):
            print(kind, ev["name"])
asyncio.run(main())
```

```text
on_chain_start greeter
on_prompt_start ChatPromptTemplate
on_prompt_end ChatPromptTemplate
on_chat_model_start GenericFakeChatModel
on_chat_model_stream '안녕'
on_parser_start StrOutputParser
on_chat_model_stream ' '
on_chat_model_stream '하세요'
on_chat_model_stream ' '
on_chat_model_stream '반가워요'
on_chat_model_end GenericFakeChatModel
on_parser_end StrOutputParser
on_chain_end greeter
```

이벤트에 프롬프트 원문, 모델 출력, 도구 응답이 포함될 수 있다. 로컬 분석에는 필요한 속성만 꺼낸다. LangSmith로 보내는 트레이싱을 쓸 때는 공식 문서의 `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` 설정과 기록할 데이터의 범위를 먼저 확인한다. [LangSmith 트레이싱 문서](https://docs.langchain.com/langsmith/trace-with-langchain)

## 구조화 출력으로 입력을 검증하기

구조화 출력은 프로그램이 읽을 수 있도록 모델의 답에 필드와 자료형을 정하는 방식이다. 예를 들어 상담 분류 결과에 `category`, `urgent`, `summary`를 요구할 수 있다.

| 스키마 | 모델 응답을 받은 뒤 |
| --- | --- |
| Pydantic 모델 | 필드가 맞으면 검증된 객체를 돌려준다. 필수 값이 없거나 제약을 어기면 검증 단계에서 오류가 난다. |
| `TypedDict` | 딕셔너리로 받는다. 런타임 검증이 필요하면 별도로 둔다. |
| JSON Schema 딕셔너리 | JSON Schema를 직접 기술한다. 모델 통합과 출력 방식에 맞춰 런타임 검증 여부를 확인한다. |

지원하는 채팅 모델은 `with_structured_output`으로 이 요구를 표현할 수 있다. 도구 호출 방식은 모델이 정해진 도구의 인자로 필드를 채운다. 제공자 자체의 스키마 강제 기능이나 JSON 모드는 모델 통합에 따라 사용할 수 있다. JSON 모드는 JSON 문법을 다루고, 필드와 값의 제약은 스키마 검증으로 확인한다. [모델의 구조화 출력](https://docs.langchain.com/oss/python/langchain/models#structured-output)

이 절과 뒤의 곱셈 실습은 Apple Silicon Mac에서 `mlx-community/Qwen2.5-3B-Instruct-4bit`를 실행했다. 먼저 아래쪽의 [로컬 모델 어댑터](#로컬-모델-어댑터)를 `lc_mlx.py`로 저장한다. 다음을 같은 폴더의 `ticket.py`에 저장하고 실행한다.

```python
from typing import Literal
from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel, Field
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
text = "어제 산 키보드가 이틀 만에 고장 났어요. 환불해 주세요."

class Ticket(BaseModel):
    """고객 문의를 분류한 결과."""
    category: Literal["환불", "배송", "기타"]
    urgent: bool = Field(description="빨리 처리해야 하면 true")
    summary: str = Field(description="한 문장 요약")

t = llm.with_structured_output(Ticket).invoke(text)
print(type(t).__name__, t)

class TicketTD(TypedDict):
    """고객 문의를 분류한 결과."""
    category: Annotated[str, ..., "환불, 배송, 기타 중 하나"]
    urgent: Annotated[bool, ..., "급하면 true"]

print(llm.with_structured_output(TicketTD).invoke(text))

out = llm.with_structured_output(
    Ticket, include_raw=True).invoke(text)
print(out.keys())
print(out["raw"].tool_calls[0]["name"],
      out["parsing_error"])
```

```text
Ticket category='환불' urgent=False summary='이틀 만에 키보드가 고장하여 환불 요청'
{'category': '환불', 'urgent': False}
dict_keys(['raw', 'parsed', 'parsing_error'])
Ticket None
```

`include_raw=True`에서 `raw`는 모델 메시지, `parsed`는 변환 결과, `parsing_error`는 파싱이나 검증 중에 난 오류다. 이 예제에서는 `raw.tool_calls`에서 모델이 어떤 인자를 만들었는지도 볼 수 있다. 다섯 글자 제한을 어긴 예를 `ticket_error.py`로 실행해 보자.

```python
from pydantic import BaseModel, Field
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
text = "어제 산 키보드가 이틀 만에 고장 났어요. 환불해 주세요."

class Short(BaseModel):
    """문의 요약."""
    summary: str = Field(max_length=5)

out = llm.with_structured_output(
    Short, include_raw=True).invoke(text)
print("raw args:", out["raw"].tool_calls[0]["args"])
print("parsed:", out["parsed"])
print("error:", type(out["parsing_error"]).__name__)

schema = {
    "title": "Sentiment",
    "description": "문장의 감정",
    "type": "object",
    "properties": {"label": {
        "type": "string", "enum": ["긍정", "부정"]}},
    "required": ["label"],
}
print(llm.with_structured_output(schema).invoke(text))
```

```text
raw args: {'summary': '사용자가 어제 산 키보드를 이틀 만에 고장으로 인해 환불을 요청하였습니다.'}
parsed: None
error: ValidationError
{'text': '어제 산 키보드가 이틀만에 고장 났어요. 환불해 주세요.'}
```

이 실행에서 Pydantic은 긴 `summary`를 거부했다. 같은 모델이 JSON Schema로 요구한 `label` 대신 `text`를 돌려줬을 때는 딕셔너리가 그대로 나왔다. 이 어댑터에서 스키마는 도구 호출 인자를 만드는 데 쓰이고, 딕셔너리의 런타임 검증은 따로 하지 않기 때문이다.

{: .warning }
스키마가 값의 모양을 확인해도 분류와 요약의 사실성은 따로 검사해야 한다. 문의가 실제로 환불 요청인지, 요약이 원문의 날짜와 상황을 바꾸지 않았는지는 별도의 평가 항목이다.

## 도구 요청과 실행 결과를 연결하기

`@tool`은 Python 함수를 LangChain 도구로 만든다. 타입 표기로 인자의 스키마를 만들고, 설명 문자열은 모델에 도구의 용도를 전달한다. `bind_tools([multiply])` 뒤에 모델이 `tool_calls`를 돌려주면 호출자는 요청한 이름과 인자를 확인할 수 있다.

다음을 `manual_tool.py`로 실행한다.

```python
from langchain.tools import tool
from langchain.messages import HumanMessage
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

print(multiply.name)
print(multiply.description)
print(multiply.args)

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
llm_t = llm.bind_tools([multiply])
msgs = [HumanMessage("123과 456을 곱해 주세요.")]
ai = llm_t.invoke(msgs)
print("content:", repr(ai.content))
print("tool_calls:", ai.tool_calls)
msgs.append(ai)
for call in ai.tool_calls:
    tm = multiply.invoke(call)
    print(type(tm).__name__, tm.content, tm.tool_call_id == call["id"])
    msgs.append(tm)
final = llm_t.invoke(msgs)
print("final:", final.content)
```

```text
multiply
두 정수의 곱을 정확하게 계산한다.
{'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
content: ''
tool_calls: [{'name': 'multiply', 'args': {'a': 123, 'b': 456}, 'id': 'call_07583300', 'type': 'tool_call'}]
ToolMessage 56088 True
final: 123과 456의 곱은 56088입니다.
```

여기서는 `multiply.invoke(call)`에 호출 객체를 통째로 준다. 실행 결과는 같은 호출 ID를 가진 `ToolMessage`가 된다. 메시지 목록에 모델의 호출 요청과 도구 결과를 순서대로 붙여 다음 모델 호출에 넘긴다. 모델이 여러 도구를 요청할 수 있는 프로그램은 요청한 이름을 등록된 도구와 대조해서 실행한다. [도구 문서](https://docs.langchain.com/oss/python/langchain/tools), [모델의 도구 호출](https://docs.langchain.com/oss/python/langchain/models#tool-calling)

{: .tip }
실무에서는 먼저 `multiply.invoke({"a": 123, "b": 456})`처럼 함수의 입력과 결과를 확인한다. 그다음 모델을 붙여 도구 이름과 인자를 잘 만들었는지 검사한다. 나중에 오류가 났을 때 인자 생성과 도구 내부 실행 중 어느 쪽인지 구분할 수 있다.

## create_agent로 도구 반복을 맡기기

`create_agent`는 모델 호출을 수행하고, 도구 요청이 나오면 지정된 도구를 실행한 뒤 결과를 모델에 돌려주는 그래프를 만든다. 실행 중에 기능을 덧붙이는 코드를 미들웨어라고 한다. `before_model` 훅은 모델 호출 전에 작동하고, `wrap_tool_call` 훅은 도구 실행 전후를 감싼다.

다음을 `agent.py`로 실행한다.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    before_model, wrap_tool_call, ModelCallLimitMiddleware)
from langchain.tools import tool
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

@before_model
def log_model(state, runtime):
    print(f"[before_model] 메시지 {len(state['messages'])}개")

@wrap_tool_call
def log_tool(request, handler):
    call = request.tool_call
    print(f"[tool] {call['name']}({call['args']})")
    result = handler(request)          # 실제 도구 실행
    print(f"[tool] 결과 {result.content}")
    return result

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(
    model=llm,
    tools=[multiply],
    system_prompt="곱셈은 multiply 도구로 계산하고 "
                  "한국어 한 문장으로 답하세요.",
    middleware=[log_model, log_tool,
                ModelCallLimitMiddleware(run_limit=5)],
)
print(type(agent).__name__)

result = agent.invoke({"messages": [
    {"role": "user", "content": "123과 456을 곱해 주세요."}]})
for m in result["messages"]:
    print(f"{m.type:5}", repr(m.content)[:40],
          getattr(m, "tool_calls", ""))
```

```text
CompiledStateGraph
[before_model] 메시지 1개
[tool] multiply({'a': 123, 'b': 456})
[tool] 결과 56088
[before_model] 메시지 3개
human '123과 456을 곱해 주세요.'
ai    '' [{'name': 'multiply', 'args': {'a': 123, 'b': 456}, 'id': 'call_a794f3ca', 'type': 'tool_call'}]
tool  '56088'
ai    '123과 456의 곱은 56088입니다.' []
```

두 번째 `before_model`에서 메시지가 세 개다. 사용자 질문에 모델의 도구 요청과 도구 결과가 더해졌다. 그 뒤의 모델 메시지에서 도구 요청 목록이 비면서 답변이 끝났다. `ModelCallLimitMiddleware(run_limit=5)`는 한 실행의 모델 호출 횟수를 제한한다. 시간 제한과 토큰 예산은 따로 설정해야 한다. [에이전트 문서](https://docs.langchain.com/oss/python/langchain/agents), [모델 호출 한도 미들웨어](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

그래프 단계별 출력을 보고 싶으면 `stream_mode="updates"`를 쓴다. 다음 `agent_stream.py`는 `model`, `tools`, `model` 순서를 보여 준다. 별도로 실행하는 호출 한도 1회 예제에서는 도구 결과를 받은 뒤 다음 모델 호출을 할 수 없어 한도 메시지를 반환했다.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.tools import tool
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(llm, tools=[multiply])
print(list(agent.get_graph().nodes))

q = {"messages": [{"role": "user",
                   "content": "12와 34를 곱해 주세요."}]}
for step in agent.stream(q, stream_mode="updates"):
    for node, update in step.items():
        m = update["messages"][-1]
        print(node, "->", m.type, repr(m.content)[:30])

limited = create_agent(llm, tools=[multiply], middleware=[
    ModelCallLimitMiddleware(run_limit=1)])
r = limited.invoke(q)
print(r["messages"][-1].type, r["messages"][-1].content)
```

```text
['__start__', 'model', 'tools', '__end__']
model -> ai ''
tools -> tool '408'
model -> ai '12과 34의 곱은 408입니다.'
ai Model call limits exceeded: run limit (1/1)
```

## 대화별 이력을 저장하기

체크포인터는 그래프 상태를 저장한다. 대화 상태를 다시 불러올 때는 같은 `thread_id`를 쓴다. 다음 `memory.py`는 이름을 알려 준 대화 `A`에 이어서 묻고, 새 대화 `B`에도 같은 질문을 보낸다.

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(
    llm, tools=[], checkpointer=InMemorySaver(),
    system_prompt="반드시 한국어로 답하세요. "
                  "모르는 것은 모른다고 답하세요.")

def ask(text, thread):
    cfg = {"configurable": {"thread_id": thread}}
    r = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        cfg)
    return r["messages"]

ask("제 이름은 예진입니다.", "A")
m = ask("제 이름이 뭐였죠?", "A")
print("A:", m[-1].content, f"(메시지 {len(m)}개)")
m = ask("제 이름이 뭐였죠?", "B")
print("B:", m[-1].content, f"(메시지 {len(m)}개)")
```

```text
A: 당신의 이름은 예진이라는 것을 들었습니다. (메시지 4개)
B: 당신의 이름은 이번에 말씀드리지 못합니다. 제가 아는 것은 제가 말한 대로 답하는 것입니다. (메시지 2개)
```

`A`에는 앞선 질문과 답이 남아 메시지가 네 개다. `B`에는 이번 질문과 답으로 두 개만 있다. 위 예제의 `InMemorySaver`는 현재 프로세스가 실행되는 동안 상태를 보관한다. 다시 켠 뒤에도 불러와야 하는 앱에서는 영구 저장소를 선택하고, 요청자가 해당 대화에 접근할 권한이 있는지 확인한다. [단기 메모리 문서](https://docs.langchain.com/oss/python/langchain/short-term-memory), [LangGraph 체크포인터](https://docs.langchain.com/oss/python/langgraph/checkpointers)

예전 코드의 `ConversationBufferMemory`는 설치한 `langchain-classic` 1.1.0에서 사용 중단 경고가 났다. 기존 앱을 옮기려면 현재 대화 기록의 보관 범위를 먼저 확인한다. 새 에이전트에 같은 범위를 적용할 때는 체크포인터와 `thread_id`로 재구성한다. [LangChain v1 변경 안내](https://docs.langchain.com/oss/python/migrate/langchain-v1)

## 실무에서는 무엇부터 확인하나

| 증상 | 먼저 확인할 곳 |
| --- | --- |
| `ModuleNotFoundError` | 실행 중인 가상 환경의 Python 경로와 제공자 패키지 설치 여부 |
| 프롬프트 `KeyError` | `input_variables`와 호출에 넣은 키, 대화 기록의 메시지 형태 |
| 구조화 출력이 비어 있음 | `include_raw=True`의 원문, 파싱 오류, 모델의 해당 방식 지원 여부 |
| 답은 맞는데 도구를 썼는지 모름 | `AIMessage.tool_calls`와 뒤에 붙은 `ToolMessage.tool_call_id` |
| 호출이 오래 대기하거나 한도를 넘음 | 제공자 요청 제한, 실행 동시성, 재시도 횟수, 외부 호출 시간 제한 |
| 비동기 화면에서 요청 처리 전체가 멈춤 | 이벤트 루프 안의 동기 호출과 도구 내부의 블로킹 작업 |

단위 테스트에서는 가짜 모델의 응답으로 도구 선택 분기, 누락 인자, 검증 실패의 경로를 고정한다. 실제 모델을 부르는 통합 테스트에서는 키와 모델 설정, 제공자 스키마, 응답이 원래 목적에 맞는지 확인한다. `GenericFakeChatModel`의 응답 반복자는 실행하면서 소비되므로 테스트마다 새 모델 객체를 만든다. [LangChain 테스트 문서](https://docs.langchain.com/oss/python/langchain/test)

## 로컬 모델 어댑터

Apple Silicon Mac에서 이 어댑터와 모델을 실행했다. 위 가상 환경에 `mlx-lm`을 추가한다. 첫 모델 로드에는 모델 파일을 내려받을 네트워크가 필요하다.

```bash
uv pip install mlx==0.32.5 mlx-lm==0.32.2
```

아래를 `lc_mlx.py`로 저장한다. 이 실습 어댑터는 Qwen의 채팅 템플릿을 적용하고, 생성된 도구 호출을 LangChain 메시지로 바꾼다. 특정 도구 호출을 요구하는 구조화 출력 실습에서는 생성 문장 앞에 도구 이름을 채운다. 이 구현은 이 글의 Qwen 실습용이다. 사용량 정보는 텍스트를 토크나이저로 다시 세어 얻은 실습용 추정치다.

```python
import json, re, uuid
from typing import Any
from mlx_lm import load, generate
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import (
    convert_to_openai_tool,
)

ROLE = {"system": "system", "human": "user",
        "ai": "assistant", "tool": "tool"}
TAG = "<tool_call>"
NAME = re.compile(r'"name":\s*"([^"]+)"')
ARGS = re.compile(r'"arguments":\s*')
DEC = json.JSONDecoder()


def parse_calls(text):
    """<tool_call> 뒤에서 name과 arguments만 꺼낸다."""
    parts = text.split(TAG)
    calls = []
    for part in parts[1:]:
        name = NAME.search(part).group(1)
        start = ARGS.search(part).end()
        args, _ = DEC.raw_decode(part[start:])
        calls.append({"name": name, "args": args,
                      "id": "call_" + uuid.uuid4().hex[:8]})
    return parts[0].strip(), calls


def to_dict(m):
    d = {"role": ROLE[m.type], "content": m.content}
    if m.type == "ai" and m.tool_calls:
        d["tool_calls"] = [
            {"type": "function", "function": {
                "name": c["name"], "arguments": c["args"]}}
            for c in m.tool_calls]
    return d


class ChatMLX(BaseChatModel):
    """mlx-lm 모델을 LangChain 채팅 모델로 감싼다."""
    model_id: str
    max_tokens: int = 256
    tools: list = []
    forced: str | None = None   # 강제로 부를 도구 이름
    _mt: Any = None

    def model_post_init(self, _):
        self._mt = load(self.model_id)

    @property
    def _llm_type(self):
        return "mlx-local"

    def bind_tools(self, tools, *, tool_choice=None, **kw):
        specs = [convert_to_openai_tool(t) for t in tools]
        forced = None
        if tool_choice not in (None, "auto", "none"):
            # "any"나 도구 이름: 첫 번째(또는 그) 도구를 강제
            forced = (specs[0]["function"]["name"]
                      if tool_choice == "any" else tool_choice)
        clone = self.model_copy(
            update={"tools": specs, "forced": forced})
        return clone.bind(**kw) if kw else clone

    def _generate(self, messages, stop=None,
                  run_manager=None, **kw):
        model, tok = self._mt
        prompt = tok.apply_chat_template(
            [to_dict(m) for m in messages],
            tools=self.tools or None,
            add_generation_prompt=True, tokenize=False)
        head = ""
        if self.forced:  # 답의 앞부분을 미리 채워 호출을 강제
            head = (TAG + '\n{"name": "%s", '
                    '"arguments": ' % self.forced)
        text = head + generate(model, tok, prompt=prompt + head,
                               max_tokens=self.max_tokens)
        content, calls = parse_calls(text)
        n_in = len(tok.encode(prompt + head))
        n_out = len(tok.encode(text[len(head):]))
        msg = AIMessage(
            content=content, tool_calls=calls,
            usage_metadata={"input_tokens": n_in,
                            "output_tokens": n_out,
                            "total_tokens": n_in + n_out})
        return ChatResult(generations=[ChatGeneration(message=msg)])
```

다음을 `local_model.py`로 실행하면 모델 로드와 일반 응답부터 확인할 수 있다.

```python
from lc_mlx import ChatMLX
llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
r = llm.invoke([("system", "한국어로 한 문장으로 답하세요."),
                ("human", "Python 리스트는 무엇인가요?")])
print(type(r).__name__)
print(r.content)
print(r.usage_metadata)
```

```text
AIMessage
Python 리스트는 여러 개의 데이터를 저장할 수 있는 배열입니다.
{'input_tokens': 32, 'output_tokens': 15, 'total_tokens': 47}
```

## 정리

프롬프트에서 메시지를 만들고, 모델에서 `AIMessage`를 받은 뒤, 소비자가 필요한 타입으로 바꾼다. 순서가 정해져 있으면 Runnable을 연결한다. 모델이 도구를 고르는 작업에서는 `create_agent`의 상태와 호출 기록을 확인한다.

모델이 만든 인자를 외부 작업에 쓰기 전에 스키마와 업무 규칙을 검사한다. 도구 호출이 있는 테스트에는 도구 결과뿐 아니라 요청 ID와 재시도 동작도 포함한다.

## 다음 편

도구 승인에서 멈췄다가 같은 상태에서 재개하거나, 코드로 여러 실행 경로를 직접 결정해야 한다면 [LangGraph]({{ "/ai/using-ai/langgraph/" | relative_url }})에서 노드와 엣지를 연결해 본다.

## 참고

- [LangChain 모델](https://docs.langchain.com/oss/python/langchain/models)
- [LangChain 메시지](https://docs.langchain.com/oss/python/langchain/messages)
- [Runnable API](https://reference.langchain.com/python/langchain-core/runnables)
- [LangChain 에이전트](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain 미들웨어](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
- [LangChain 단기 메모리](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [LangChain으로 LangSmith 트레이싱](https://docs.langchain.com/langsmith/trace-with-langchain)
- [MLX LM](https://github.com/ml-explore/mlx-lm)
