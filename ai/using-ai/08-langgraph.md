---
title: "LangGraph"
description: "모델과 API 키 없이 시작하는 LangGraph 실습으로 StateGraph, 노드, 엣지, 조건 분기와 체크포인트를 설명합니다."
parent: AI
nav_order: 8
permalink: /ai/using-ai/langgraph/
last_modified_date: 2026-11-17
---

# LangGraph
{: .no_toc }

{% include article-toc.md %}

LangGraph를 처음 배우면서 모델 호출까지 동시에 다루면 오류 원인을 찾기 어렵다. 이 글에서는 문장이 비어 있는지 검사하고, 정상 입력을 가공하고, 결과를 반환하는 작은 프로그램부터 만든다. 모델이나 API 키는 필요하지 않다.

## 먼저 만들 흐름 그리기

```text
시작 → 입력 정리 → 유효성 검사
                    ├─ 정상 → 결과 작성 → 끝
                    └─ 빈 값 → 안내 작성 → 끝
```

각 사각형 역할을 수행하는 함수가 노드다. 화살표는 다음 실행 위치를 지정하는 엣지다. 함수 사이에서 전달하는 작업 데이터가 상태다.

그래프의 단계는 반드시 AI일 필요가 없다. 검증처럼 규칙이 명확한 부분은 Python 함수로 만들고, 글을 작성하거나 의도를 분류하는 부분에 필요할 때 모델 호출을 넣을 수 있다.

## 환경 준비하기

Python 3.11 이상 환경을 기준으로 진행한다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U langgraph
```

다음 전체 예제를 `first_graph.py`에 저장한다. 부분 코드를 여러 위치에 붙이는 대신 한 파일에서 실행해 흐름부터 확인하자.

## 전체 실행 코드

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class TextState(TypedDict, total=False):
    original: str
    cleaned: str
    answer: str


def normalize(state: TextState):
    return {"cleaned": state["original"].strip()}


def choose_route(state: TextState):
    return "valid" if state["cleaned"] else "empty"


def write_answer(state: TextState):
    text = state["cleaned"]
    return {"answer": f"입력한 내용: {text} / 글자 수: {len(text)}"}


def explain_empty(state: TextState):
    return {"answer": "내용을 입력해 주세요."}


builder = StateGraph(TextState)
builder.add_node("normalize", normalize)
builder.add_node("write_answer", write_answer)
builder.add_node("explain_empty", explain_empty)

builder.add_edge(START, "normalize")
builder.add_conditional_edges(
    "normalize",
    choose_route,
    {"valid": "write_answer", "empty": "explain_empty"},
)
builder.add_edge("write_answer", END)
builder.add_edge("explain_empty", END)

app = builder.compile()

for text in ["  안녕하세요  ", "   "]:
    result = app.invoke({"original": text})
    print(result["answer"])
```

실행한다.

```bash
python first_graph.py
```

예상 출력은 다음과 같다.

아래 출력은 Python 3.11 환경에서 본문의 전체 코드, 단계별 스트리밍, 메모리 체크포인트 예제를 실제 실행해 확인했다. 유료 모델 API는 호출하지 않았다.

```text
입력한 내용: 안녕하세요 / 글자 수: 5
내용을 입력해 주세요.
```

## 상태를 작업 노트처럼 읽기

최초 입력에는 `original`만 있다. `normalize`가 실행되면 `cleaned`가 추가되고, 마지막 노드가 실행되면 `answer`가 생긴다.

```text
입력        { original }
정리 후     { original, cleaned }
완료 후     { original, cleaned, answer }
```

`total=False`는 모든 키가 처음부터 있어야 하는 타입으로 선언하지 않겠다는 뜻이다. 런타임의 입력 검증을 대신하지는 않으므로 `original`이 아예 없을 수 있는 외부 요청에는 별도 검증이 필요하다.

각 노드는 전체 상태를 새로 작성하지 않고 바뀐 필드만 반환한다. 이 예제는 기본 갱신 규칙을 사용하므로 해당 필드가 새 값으로 대체된다.

## 조건 분기는 함수의 반환값으로 결정된다

`choose_route`가 반환한 `valid` 또는 `empty`는 다음 노드 이름에 매핑된다. 문자열 철자가 매핑 키와 다르면 경로를 찾지 못한다.

조건부 분기와 같은 출발점에 일반 엣지를 추가하면 그 일반 경로도 함께 실행될 수 있다. 한 갈래만 선택하려는 목적이라면 위처럼 조건부 엣지로만 연결한다.

## compile과 invoke 구분하기

`compile()`은 노드와 연결을 실행할 수 있는 그래프로 준비한다. `invoke()`는 준비된 그래프에 실제 입력을 넣어 한 번 실행한다.

builder를 수정한 뒤에는 다시 compile해야 새 연결이 반영된다. 이미 만든 `app`을 계속 사용하면서 연결이 바뀌었다고 기대하면 실습 결과를 잘못 해석할 수 있다.

## 중간 상태를 관찰하기

같은 `app`에 다음을 추가해 각 단계의 변경을 볼 수 있다.

```python
for update in app.stream(
    {"original": "  테스트  "},
    stream_mode="updates",
):
    print(update)
```

이것은 모델의 글자 생성 스트리밍과 다르다. `updates` 모드는 그래프 단계에서 어떤 상태가 갱신됐는지 관찰한다. 입력 정리 뒤에는 `cleaned`, 답변 작성 뒤에는 `answer` 변경을 확인할 수 있다.

## 체크포인트로 상태 보관하기

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()
saved_app = builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "practice-1"}}

saved_app.invoke({"original": "기록할 내용"}, config)
snapshot = saved_app.get_state(config)
print(snapshot.values)
```

`thread_id`는 같은 작업 흐름을 찾는 식별자다. 체크포인터는 해당 흐름의 상태를 보관한다. 이 예제의 `InMemorySaver`는 프로세스 메모리 안에 있으므로 프로그램을 종료하면 사라진다. 운영에서 재시작 후에도 이어가려면 영구 저장 백엔드를 구성해야 한다.

사용자 선호처럼 여러 thread에 걸쳐 보관할 정보는 별도의 store 개념과 구분한다. 대화 하나의 실행 상태와 사용자 전체의 장기 정보는 보존 범위가 다르다.

## 반복과 승인을 추가할 때

수정 노드에서 검사 노드로 돌아가는 엣지를 만들면 반복이 된다. 이때 상태에 수정 횟수를 두고 ‘통과’, ‘횟수 초과’, ‘사용자 입력 필요’를 각각 종료 또는 중단 경로로 연결한다.

승인 대기는 잠깐 기다렸다가 자동 실행하는 동작이 아니다. 실제로 실행을 중단하고 명시적인 사용자 결정을 받은 뒤 재개해야 한다. 파일 발송이나 결제 같은 외부 행동은 재실행되더라도 중복 반영되지 않도록 요청 ID도 관리한다.

## 모델을 넣는 위치

위 예제의 `write_answer` 함수를 모델 호출로 바꾸면 그래프 전체 구조를 유지하면서 생성 단계를 추가할 수 있다. 먼저 입력 검증과 분기가 맞는지 확인한 다음 모델을 연결하면 네트워크 오류와 그래프 오류를 구분하기 쉽다.

처음부터 모든 노드를 에이전트로 만들 필요는 없다. 노드는 한 단계의 책임을 뜻하며, AI 판단이 필요 없는 단계는 일반 함수로 남겨도 된다.

## 다음 실습

입력에 공백, 한글, 여러 줄 문장을 각각 넣어 보자. 다음에는 글자 수가 일정 기준을 넘을 때 별도 노드로 보내는 분기를 추가한다. 새 경로를 만들 때는 기존 두 입력이 여전히 예상대로 처리되는지도 다시 확인한다.

## 참고

- [LangGraph: Graph API overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [개념부터 읽기: 그래프 엔지니어링]({{ '/ai/using-ai/graph-engineering/' | relative_url }})
