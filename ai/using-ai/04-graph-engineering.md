---
title: "4. 그래프 엔지니어링: LangGraph로 상태와 분기 연결하기"
description: "LangGraph의 상태, 노드, 엣지, 조건 분기, 반복, 체크포인트와 사람 승인을 첫 Python 예제로 설명합니다."
parent: AI 사용법
grand_parent: AI
nav_order: 4
permalink: /ai/using-ai/graph-engineering/
first_written: 2026-11-16
last_modified_date: 2026-11-16
tags: [AI, Agent, Graph-Engineering, LangGraph, LangChain]
---

# 그래프 엔지니어링: LangGraph로 상태와 분기 연결하기
{: .no_toc }

<details open markdown="block">
  <summary>목차</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

작업이 길어지면 단순한 “모델 → 도구 → 모델” 루프만으로 전체 흐름을 이해하기 어려워진다. 문의 종류에 따라 다른 경로로 보내고, 실패하면 재시도하고, 중요한 작업은 사람의 승인을 기다린 뒤 이어서 실행해야 할 수 있다.

이 흐름을 **노드와 연결선으로 표현한 것**이 그래프다. 그래프 엔지니어링은 에이전트 업무를 상태, 단계, 분기, 반복, 종료로 나눠 **실행 경로가 보이고 복구 가능한 구조**로 설계하는 일이다.

{: .note }
“그래프 엔지니어링”도 하나로 표준화된 직무명이라기보다, 이 글에서는 AI 워크플로와 에이전트 제어 흐름을 그래프로 설계하는 일을 뜻한다.

## 그래프를 일상적인 업무로 이해하기

고객 이메일 처리 과정을 생각해 보자.

```text
[메일 받기]
      ↓
[문의 분류]
   ├─ 단순 질문 → [문서 검색] → [답변 작성]
   ├─ 버그 신고 → [이슈 등록] → [접수 답변]
   └─ 환불 요청 → [환불 초안] → [사람 승인]
                                      ├─ 승인 → [환불 실행]
                                      └─ 거절 → [수정 요청]
```

이 그림에서:

- 네모 하나는 **노드(Node)**: 한 단계의 작업
- 화살표는 **엣지(Edge)**: 다음 단계로 가는 경로
- 분기 조건은 **라우팅(Routing)**: 어느 화살표를 탈지 결정
- 단계들이 함께 보는 정보는 **상태(State)**
- 시작과 끝은 **START**, **END**

## 왜 굳이 그래프로 만들까

### 실행 경로가 보인다

한 프롬프트 안에 모든 규칙을 넣는 대신, 어떤 상황에서 검색하고 언제 승인받는지 구조로 확인할 수 있다.

### 단계별로 검사할 수 있다

분류는 맞았는지, 검색 결과는 충분한지, 답변 초안은 기준을 통과했는지 각각 테스트할 수 있다.

### 실패 지점부터 복구할 수 있다

각 노드 뒤에 상태를 저장하면 마지막 성공 지점부터 재개할 수 있다. 긴 작업 전체를 처음부터 반복하지 않아도 된다.

### 결정적인 규칙과 AI 판단을 섞어 쓸 수 있다

금액이 100만 원 이상이면 무조건 사람에게 보내는 규칙은 일반 코드로, 문의 의도를 분류하는 일은 모델로 처리할 수 있다.

## 그래프의 핵심은 그림보다 상태다

상태는 모든 노드가 넘겨받는 작업 노트다.

```python
class SupportState(TypedDict):
    email: str
    category: str
    search_results: list[str]
    draft: str
    approved: bool
    error: str
```

각 노드는 전체 상태를 받아 필요한 일부를 읽고, 자신이 만든 변경만 반환한다.

```python
def classify(state: SupportState):
    category = classify_email(state["email"])
    return {"category": category}
```

상태에는 단계 사이에서 정말 유지해야 하는 원본 데이터를 둔다.

- 원본 사용자 요청
- 분류 결과
- 검색 결과
- 작성 중인 초안
- 승인 여부
- 재시도 횟수와 오류 정보

프롬프트 전체를 미리 만들어 상태에 저장하기보다, 각 노드에서 원본 상태를 사용해 그때 필요한 프롬프트를 만드는 편이 수정과 디버깅에 유리하다.

## LangGraph는 무엇인가

LangGraph는 상태를 가진 장기 실행 에이전트와 워크플로를 그래프로 만드는 프레임워크다. LangChain의 에이전트도 내부적으로 LangGraph의 기반 요소를 사용하며, 더 세밀한 분기·지속성·중단·재개가 필요하면 LangGraph를 직접 사용할 수 있다.

초보자 기준으로 둘을 구분하면 다음과 같다.

| 도구 | 쉽게 말하면 | 잘 맞는 상황 |
| --- | --- | --- |
| LangChain | 모델과 도구를 빠르게 연결하는 부품 상자 | 기본 에이전트, RAG, 간단한 도구 호출 |
| LangGraph | 상태와 실행 경로를 직접 그리는 작업 흐름 엔진 | 복잡한 분기, 반복, 승인, 중단 후 재개 |

둘 중 하나만 선택하는 관계가 아니다. LangGraph 노드 안에서 LangChain의 모델, 도구, 검색기를 사용할 수 있다.

## 설치하기

Python 가상 환경을 만든 뒤 패키지를 설치한다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U langgraph langchain langchain-openai
```

API 키는 코드에 직접 쓰지 말고 환경 변수나 비밀 관리 도구를 사용한다.

```bash
export OPENAI_API_KEY="발급받은-키"
```

실제 키를 Git 저장소의 `.env`나 소스 파일에 커밋하지 않는다.

## 모델 없이 배우는 첫 LangGraph

먼저 LLM 호출 없이 그래프 구조만 이해해 보자. 입력한 주제로 목차를 만들고 초안을 만드는 두 단계다.

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class BlogState(TypedDict):
    topic: str
    outline: list[str]
    draft: str


def make_outline(state: BlogState):
    topic = state["topic"]
    return {
        "outline": [
            f"{topic}이란?",
            f"{topic}은 언제 사용할까?",
            f"{topic} 예제",
        ]
    }


def write_draft(state: BlogState):
    lines = [f"# {state['topic']}"]

    for heading in state["outline"]:
        lines.append(f"\n## {heading}\n설명을 작성합니다.")

    return {"draft": "\n".join(lines)}


builder = StateGraph(BlogState)
builder.add_node("make_outline", make_outline)
builder.add_node("write_draft", write_draft)

builder.add_edge(START, "make_outline")
builder.add_edge("make_outline", "write_draft")
builder.add_edge("write_draft", END)

app = builder.compile()

result = app.invoke({"topic": "LangGraph"})
print(result["draft"])
```

### 코드를 순서대로 해석하면

1. `BlogState`는 그래프가 들고 다닐 작업 노트의 모양이다.
2. `make_outline` 노드는 `topic`을 읽고 `outline`을 추가한다.
3. `write_draft` 노드는 앞 노드가 만든 `outline`을 읽고 `draft`를 만든다.
4. `add_node`로 함수에 노드 이름을 붙인다.
5. `add_edge`로 실행 순서를 연결한다.
6. `compile()`이 실행 가능한 그래프를 만든다.
7. `invoke()`에 최초 상태를 넣으면 START부터 END까지 실행된다.

이 예제의 핵심은 각 함수가 전역 변수를 몰래 바꾸는 대신 **상태를 입력받고 상태 변경을 반환한다**는 점이다.

## 조건에 따라 길을 나누기

초안이 너무 짧으면 보강하고, 충분하면 끝내 보자.

```python
def choose_next(state: BlogState):
    if len(state["draft"]) < 500:
        return "expand_draft"
    return "finish"


def expand_draft(state: BlogState):
    return {
        "draft": state["draft"] + "\n\n더 자세한 예시를 추가합니다."
    }


builder.add_node("expand_draft", expand_draft)

builder.add_conditional_edges(
    "write_draft",
    choose_next,
    {
        "expand_draft": "expand_draft",
        "finish": END,
    },
)
builder.add_edge("expand_draft", END)
```

`choose_next`는 작업을 수행하는 노드가 아니라 다음 경로를 고르는 라우터다. 실제 서비스에서는 길이 하나만 보지 말고 내용 평가, 안전 검사, 사용자 권한 같은 조건을 함께 사용할 수 있다.

## 반복을 만들 때 반드시 상한을 둔다

평가에 실패하면 다시 작성하는 그래프는 쉽게 무한 루프가 된다.

```text
초안 작성 → 평가 → 실패 → 수정 → 평가 → 실패 → ...
```

상태에 반복 횟수를 넣고 종료 규칙을 만든다.

```python
class ReviewState(TypedDict):
    draft: str
    feedback: str
    score: int
    revision_count: int


def route_after_review(state: ReviewState):
    if state["score"] >= 80:
        return "finish"
    if state["revision_count"] >= 3:
        return "human_review"
    return "revise"
```

좋은 반복 그래프에는 다음이 필요하다.

- 합격 기준
- 최대 반복 횟수
- 이전보다 좋아졌는지 비교할 기준
- 가장 좋았던 결과를 보관하는 방법
- 개선이 멈췄을 때 사람에게 넘기는 경로

## 체크포인트: 멈췄다가 이어가기

긴 작업은 프로세스가 종료되거나 사람 답변을 기다리며 멈출 수 있다. 체크포인터는 그래프 상태를 단계 사이에 저장한다.

```text
문서 검색 완료 → [상태 저장]
초안 작성 완료 → [상태 저장]
사람 승인 대기 → 며칠 뒤 같은 상태에서 재개
```

LangGraph에서는 그래프를 컴파일할 때 체크포인터를 연결하고, 실행마다 `thread_id` 같은 식별자를 사용한다. 개발 예제의 메모리 저장소와 운영 환경의 영구 데이터베이스는 목적이 다르므로 구분해야 한다.

체크포인트가 있어도 외부 행동은 별도 주의가 필요하다. 결제가 성공한 직후 프로세스가 멈춰 같은 노드를 재실행하면 중복 결제가 될 수 있다. 요청 ID를 저장해 같은 작업이 한 번만 반영되도록 **멱등성**을 설계한다.

## 사람 승인으로 멈추기

그래프의 장점 중 하나는 사람 확인을 예외가 아니라 정상 경로로 표현할 수 있다는 점이다.

```text
[환불안 생성]
      ↓
[실행 중단 + 승인 요청]
      ↓
사람의 승인/수정/거절 입력
      ↓
[저장된 상태에서 재개]
```

사람에게는 다음을 보여 줘야 한다.

- 무엇을 실행하려는가
- 영향을 받는 대상과 범위
- 왜 이 행동을 선택했는가
- 승인하면 바로 어떤 일이 일어나는가
- 수정하거나 거절할 방법

## 노드를 얼마나 잘게 나눌까

너무 큰 노드:

```text
[검색 + 분석 + 작성 + 발송]
```

어디서 실패했는지 알기 어렵고, 마지막 발송에서 실패해도 검색부터 다시 할 수 있다.

너무 작은 노드:

```text
[문장 읽기] → [단어 분리] → [첫 단어 확인] → ...
```

구조와 로그만 복잡해진다.

다음 기준으로 나누면 실용적이다.

- 별도로 재시도할 필요가 있는가?
- 앞뒤에서 사용하는 도구나 권한이 다른가?
- 사람 승인이나 검증이 필요한 경계인가?
- 중간 결과를 관찰하고 싶은가?
- 실패했을 때 이 단계부터 다시 시작할 가치가 있는가?

## LangChain만 쓸지 LangGraph까지 쓸지

### LangChain의 기본 에이전트로 시작해도 좋은 경우

- 도구 수가 적다.
- 모델이 다음 도구를 자유롭게 골라도 된다.
- 승인과 복구 경로가 단순하다.
- 짧은 요청 안에 끝난다.

### LangGraph를 직접 고려할 경우

- 반드시 지켜야 하는 업무 순서가 있다.
- 조건 분기와 재시도가 많다.
- 사람 승인에서 오래 멈췄다가 재개해야 한다.
- 단계별 상태와 실행 기록이 중요하다.
- 일부 단계만 다시 실행해야 한다.
- 여러 에이전트나 워크플로를 명시적으로 조정한다.

프레임워크를 먼저 고르고 문제를 끼워 맞추지 않는다. 먼저 사람이 하는 업무 흐름을 그린 뒤 필요한 도구를 선택한다.

## 그래프 설계 체크리스트

- 시작 상태와 완료 상태가 명확한가?
- 각 노드는 한 가지 책임을 갖는가?
- 상태에는 원본 데이터가 저장되는가?
- 모든 조건 분기에 갈 곳이 있는가?
- 반복 경로에 횟수·시간·비용 상한이 있는가?
- 일시 오류와 사람 판단 필요를 다른 경로로 처리하는가?
- 중요한 외부 행동 전에 승인 노드가 있는가?
- 중단 후 재개할 체크포인트가 있는가?
- 외부 쓰기 작업은 재실행해도 중복되지 않는가?
- 노드별 입력, 출력, 지연, 오류를 추적할 수 있는가?

## 정리

그래프는 에이전트를 복잡하게 보이게 만드는 그림이 아니라, 복잡한 일을 상태와 경로로 드러내는 도구다. LangChain이 모델과 도구를 빠르게 연결한다면, LangGraph는 그 부품들이 언제 실행되고 어디서 멈추며 어떻게 재개되는지를 세밀하게 제어한다.

하지만 그래프만으로 도구 권한, 파일 환경, 테스트, 기록, 배포 안전성까지 해결되지는 않는다. 다음 편에서는 이 모든 실행 조건을 묶는 하네스 엔지니어링을 다룬다.

→ [5. 하네스 엔지니어링: AI가 안정적으로 일하는 환경 만들기]({{ '/ai/using-ai/harness-engineering/' | relative_url }})

## 참고

- [LangChain 공식 문서: Learn](https://docs.langchain.com/oss/python/learn)
- [LangGraph 공식 문서: Thinking in LangGraph](https://docs.langchain.com/oss/javascript/langgraph/thinking-in-langgraph)
