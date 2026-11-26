---
title: "루프 엔지니어링"
description: "AI 에이전트의 관찰·행동·종료 규칙을 모델 호출 없는 Python 예제로 검증하고 완료·실패·한도 소진을 구분합니다."
parent: AI
nav_order: 4
permalink: /ai/using-ai/loop-engineering/
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
date: 2026-11-16
first_written: 2026-11-16
last_modified_date: 2026-11-20
tags: [AI, Agent, Loop-Engineering, LangChain]
---

# 루프 엔지니어링
{: .no_toc }

{% include article-toc.md %}

에이전트는 모델이 다음 행동을 고르고, 프로그램이 도구를 실행하고, 그 결과를 모델에게 돌려주는 과정을 반복할 수 있다. 이때 반복할 수 있다는 능력보다 중요한 것은 **어떤 결과를 관찰하면 다음 행동을 바꾸고, 언제 멈추는가**다.

이 글에서는 그 제어 구조를 루프 엔지니어링이라고 부른다. 표준화된 직무명이 아니라 관찰·행동·종료 규칙을 묶어 설명하는 표현이다. 모델과 도구를 연결하는 실제 API는 [LangChain]({{ '/ai/using-ai/langchain/' | relative_url }})에서 다룬다. 여기서는 API 키 없이 종료 규칙을 시험한다.

## 한 번 호출하는 것과 무엇이 다른가

“주문 A-100의 배송 상태를 알려 달라”는 요청을 받았다고 하자. 모델이 `get_order_status`라는 도구를 고르면 실행기가 주문을 조회한다. 모델이 함수 이름을 출력한 것만으로 조회가 실행되는 것은 아니다.

```text
사용자 요청
  → 모델이 조회 요청을 생성
  → 실행기가 인자와 권한 검사
  → 도구 실행
  → 결과를 모델에 전달
  → 답변하거나 다른 도구 요청
```

도구의 결과는 다음 판단에 들어갈 새 정보다. `shipped`와 `estimated_delivery: null`을 받았다면 “배송이 시작됐으며 도착 예정일은 확인되지 않는다”까지 답할 수 있다. 예상일이 없다는 이유만으로 같은 조회를 반복해도 새 정보가 생기지는 않는다.

고정된 조회 한 번이면 충분한 서비스는 일반 함수로 구현해도 된다. 실행 중 결과에 따라 행동을 달리 선택해야 할 때 모델이 제어하는 루프가 필요하다. [Anthropic의 에이전트 설계 문서](https://www.anthropic.com/engineering/building-effective-agents)는 코드가 경로를 정하는 워크플로와 모델이 동적으로 정하는 에이전트를 구분한다.

## 완료·실패·한도 소진은 다른 결과다

반복문을 빠져나왔다고 목표를 달성한 것은 아니다. 호출자에게 최소한 다음 상태를 구분해서 돌려줘야 한다.

| 상태 | 이 주문 조회에서의 의미 | 다음 처리 |
| --- | --- | --- |
| `complete` | 알려진 상태와 예상일을 확인함 | 근거 범위 안에서 답변 |
| `needs_input` | 주문 ID가 없음 | 필요한 정보를 질문 |
| `failed` | 권한 거부 또는 재시도 불가 오류 | 원인을 보고하고 중단 |
| `exhausted` | 일시 오류가 시도 상한까지 계속됨 | 미완료로 보고 |

모델이 “완료했다”고 출력하는 것과 완료 판정도 분리한다. 조회에 성공한 주문 ID가 사용자가 요청한 ID인지, 결과의 필수 필드가 있는지는 실행기가 검사할 수 있다. 자연어 답변의 정확성은 그다음 평가 대상이다.

## 실행 가능한 최소 루프

다음을 `bounded_loop.py`에 저장한다. Python 3.11 이상에서 외부 패키지와 API 키 없이 실행한다. 실제 배송 서버와 모델 대신 고정된 응답을 사용한다.

```python
from collections import deque


def lookup(order_id, responses, max_attempts=2):
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if not order_id:
        return "needs_input", 0

    for attempt in range(1, max_attempts + 1):
        result = responses.popleft()
        if result["kind"] == "ok":
            if result.get("order_id") != order_id:
                return "failed", attempt
            if "status" not in result or "estimated_delivery" not in result:
                return "failed", attempt
            return "complete", attempt
        if result["kind"] != "timeout":
            return "failed", attempt

    return "exhausted", max_attempts


def success():
    return {"kind": "ok", "order_id": "A-100",
            "status": "shipped", "estimated_delivery": None}


cases = {
    "success": ("A-100", [success()]),
    "retry": ("A-100", [{"kind": "timeout"}, success()]),
    "missing": ("", []),
    "denied": ("A-100", [{"kind": "forbidden"}]),
    "exhausted": ("A-100", [{"kind": "timeout"}] * 2),
}
for name, (order_id, responses) in cases.items():
    state, attempts = lookup(order_id, deque(responses))
    print(f"{name}: {state}, attempts={attempts}")
```

```bash
python bounded_loop.py
```

실제로 실행한 결과다.

```text
success: complete, attempts=1
retry: complete, attempts=2
missing: needs_input, attempts=0
denied: failed, attempts=1
exhausted: exhausted, attempts=2
```

`max_attempts=2`는 최초 호출을 포함한 총 시도 수다. `responses`는 테스트 응답을 순서대로 꺼내는 큐다. 응답이 부족하면 이 테스트 장치는 오류를 내므로 각 사례에 필요한 응답을 준비했다. 실제 실행기에서는 도구 호출의 예외를 명시적인 결과 상태로 바꿔야 한다.

이 프로그램은 모델이 행동을 선택하는 에이전트 전체가 아니다. **결과를 분류하고 상한 안에서 멈추는 제어 부분**이다. 임의의 모델 출력도 실행기의 검사를 통과해야 한다는 구조를 먼저 익히기 위한 예제다.

[실행 파일 내려받기]({{ "/assets/examples/ai/bounded_loop.py" | relative_url }}). 본문의 코드와 같은 파일이다.

## 모델을 연결하면 달라지는 경계

실제 루프에서는 `responses.popleft()` 자리에 모델이 선택한 도구 호출과 실행 결과가 들어간다. 모델에는 허용된 도구의 이름·설명·인자 스키마를 준다. 실행기는 도구 이름과 인자를 검증하고, 현재 사용자에게 실행 권한이 있는지도 별도로 확인한다.

도구 실행 결과에는 성공 여부뿐 아니라 오류 종류와 재시도 가능성을 담는다. 시간 초과는 제한 안에서 다시 시도할 수 있지만, 없는 주문 ID는 사용자 확인이 먼저이고 권한 부족은 반복 호출로 해결되지 않는다. 오류 메시지를 모델에게 보여 주는 것만으로 이 정책이 강제되지는 않는다.

모델에게 전달할 상태는 요청, 확인한 근거, 직전 오류, 남은 예산처럼 다음 행동을 바꿀 정보여야 한다. 동일한 입력과 오류만 계속 쌓으면 비용은 늘어도 진전이 생기지 않는다.

## 반복 횟수만 제한하면 충분할까

한 호출이 영원히 응답하지 않으면 반복 상한에 도달하지도 못한다. 도구별 시간 제한과 전체 마감 시각이 따로 필요하다. 모델 호출 수, 도구 호출 수, 수정 횟수도 서로 다른 값이다. 한 번의 모델 응답에 여러 도구 호출이 들어갈 수 있다.

실제 서비스에서는 일시 오류 사이에 대기 간격과 무작위 지연을 두고, 제공자의 요청 제한을 따른다. 예제는 기다림을 구현하지 않아 제어 흐름만 즉시 시험한다.

쓰기 작업의 시간 초과는 특히 다르다. 환불 서버가 처리한 뒤 응답만 유실됐다면 다시 요청할 때 두 번 반영될 수 있다. 같은 업무 요청을 식별하는 멱등 키로 중복을 막거나 서버 상태를 재조회해야 한다. “오류이므로 재시도”는 충분한 계약이 아니다.

## 검토·수정 루프도 같은 원리다

초안 → 검토 → 수정은 조회 재시도와 다르다. 평가 결과가 다음 초안의 입력을 바꾼다. 이 루프에는 구체적인 결함, 수정 횟수, 이전 결과보다 나아졌는지 판단할 기준이 필요하다.

예를 들어 최대 두 번 수정하되 필수 출처가 없는 초안은 완료로 내보내지 않는다고 정할 수 있다. 두 번 뒤에도 실패하면 `exhausted`와 미해결 결함을 반환한다. 무조건 마지막 초안을 성공 결과로 내보내면 한도가 품질 기준을 대신하게 된다.

사람의 판단이 필요하면 현재 상태와 제안된 행동을 보관하고 실행을 멈춘다. 승인을 기다리는 동안 자동으로 외부 변경을 진행해서는 안 된다. 여러 분기와 복구 지점이 생기면 [그래프 엔지니어링]({{ '/ai/using-ai/graph-engineering/' | relative_url }})처럼 상태와 경로를 명시하는 방식이 도움이 된다.

## 참고

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [LangChain: Agents](https://docs.langchain.com/oss/python/langchain/agents)
