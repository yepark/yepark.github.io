---
title: AI
nav_order: 2
has_children: true
has_toc: false
permalink: /ai/
redirect_from:
  - /ai/using-ai/
---

# AI

모델에 일을 맡기는 방법과 그 실행을 검증하는 방법을 다룬다. 프롬프트·컨텍스트는 입력 설계, 루프·그래프·DAG는 실행 제어, 하네스·평가는 재현과 품질 판단에 초점을 둔다. LangChain·LangGraph 글에는 설치부터 따라가는 Python 예제가 있다. 머신러닝 기초와 Mac에서 TensorFlow로 모델을 학습하는 실습도 있다. MLX는 Apple 실리콘에서 배열 연산과 학습을 살펴보는 별도 주제다.

각 주제는 독립된 글이다. 필요한 주제부터 골라 읽을 수 있다.

## 먼저 알아 둘 용어

| 용어 | 뜻 |
| --- | --- |
| LLM (Large Language Model, 대규모 언어 모델) | 방대한 글을 학습해 "다음에 올 말"을 예측하는 모델. ChatGPT, Claude 같은 서비스의 엔진이다 |
| 토큰 | 모델이 글을 처리하는 단위. 단어보다 작은 조각이며, 한국어 한 글자가 토큰 하나 이상이 되기도 한다. 입력 길이 제한과 요금이 토큰 수로 정해진다 |
| 프롬프트 | 모델에게 보내는 입력 글. 지시, 예시, 자료가 모두 포함된다 |
| 추론(inference) | 학습이 끝난 모델에 입력을 넣어 결과를 얻는 것. 학습(training)과 구분한다 |
| 에이전트 | 모델이 다음 행동(도구 호출, 파일 수정 등)을 고르고, 프로그램이 그 행동을 실행해 결과를 다시 모델에게 보여 주는 반복으로 일을 끝까지 처리하는 시스템 |
| 환각(hallucination) | 모델이 근거 없는 내용을 사실처럼 그럴듯하게 만들어 내는 현상 |

이 용어들이 처음이라면 [LLM 기초]({{ '/ai/using-ai/llm-basics/' | relative_url }})부터 읽으면 나머지 글이 쉬워진다.

{% include series-list.html heading="주제별 포스트" %}
