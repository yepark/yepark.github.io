---
title: "LLM 기초"
description: "LLM이 다음 토큰을 예측해 글을 만드는 원리를 토큰, 확률, 온도, 컨텍스트 창, 학습과 추론으로 나눠 설명하고, 순수 Python으로 다음 토큰 예측기를 직접 만들어 확인합니다."
parent: AI
nav_order: 0
permalink: /ai/using-ai/llm-basics/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-27
first_written: 2026-11-27
last_modified_date: 2026-11-27
tags: [AI, LLM, Token, Python]
---

# LLM 기초
{: .no_toc }

{% include article-toc.md %}

ChatGPT나 Claude에게 질문하면 답이 한 단어씩 흘러나온다. 화면에 글자가 조금씩 찍히는 것은 연출이 아니라 실제로 그렇게 만들어지기 때문이다. 모델은 답 전체를 한 번에 떠올리지 않는다. **지금까지의 글 다음에 올 조각 하나**를 고르고, 그 조각을 붙여 다시 다음 조각을 고르는 일을 반복한다.

**LLM(Large Language Model, 대규모 언어 모델)**은 인터넷 문서, 책, 코드처럼 방대한 글을 학습해 "이 글 다음에 무엇이 올까"를 예측하도록 만든 모델이다. 파라미터(학습으로 정해지는 숫자)가 수십억에서 수조 개에 이르러 "대규모"라고 부른다. 이 글에서는 LLM을 쓰는 데 필요한 기본 개념을 순서대로 정리하고, 같은 원리를 아주 작은 Python 코드로 직접 만들어 본다.

## 토큰: 모델이 글을 읽는 단위

모델은 글자를 그대로 다루지 않는다. 글을 **토큰**이라는 조각으로 자르고, 각 조각에 번호를 붙여 숫자로 처리한다. 글을 토큰으로 자르는 도구를 **토크나이저**라고 한다.

토큰은 단어와 같지 않다. 자주 나오는 단어는 토큰 하나가 되고, 드문 단어나 한국어는 여러 토큰으로 쪼개지기도 한다. [컨텍스트 엔지니어링]({{ '/ai/using-ai/context-engineering/' | relative_url }}) 글에서 같은 뜻의 문장을 실제로 세어 본 결과가 있다.

| 문장 | 글자 수 | 토큰 수 (o200k_base) |
| --- | ---: | ---: |
| 연차는 다음 해 3월 31일까지 최대 5일 이월할 수 있다. | 33 | 21 |
| Up to 5 days of annual leave can be carried over until March 31 of the next year. | 81 | 21 |

글자 수가 두 배 넘게 차이 나도 토큰 수는 같았다. 토큰이 중요한 이유는 세 가지다.

- **요금**: API 요금은 입력·출력 토큰 수로 매긴다.
- **길이 제한**: 모델이 한 번에 볼 수 있는 양(컨텍스트 창)이 토큰 수로 정해진다.
- **속도**: 출력은 토큰 하나씩 만들어지므로, 출력 토큰이 많을수록 오래 걸린다.

토큰 수는 모델마다 토크나이저가 달라 다르게 나온다. 정확한 값이 필요하면 사용하는 모델의 토큰 계산 API나 응답에 포함된 사용량 정보를 본다.

## 다음 토큰 예측

LLM이 하는 일은 결국 하나다. 지금까지의 토큰 열을 받아, **다음 토큰 후보마다 확률을 매긴다.**

```text
입력: "고양이가 밥을"
출력: "먹는다" 0.82, "좋아한다" 0.09, "찾는다" 0.04, ...
```

그중 하나를 골라 입력 뒤에 붙이고, 늘어난 입력으로 다시 예측한다. 이 반복을 **자기회귀(autoregressive) 생성**이라고 한다.

```text
"고양이가"            → "밥을" 선택
"고양이가 밥을"       → "먹는다" 선택
"고양이가 밥을 먹는다" → "." 선택 → 끝
```

질문에 답하는 것, 코드를 짜는 것, 번역하는 것도 모두 이 "다음 토큰 고르기"의 반복이다. 학습 과정에서 질문 뒤에는 답이, 지시 뒤에는 그 지시를 따른 결과가 오도록 충분히 배웠기 때문에 대화가 되는 것이다.

## 직접 만들어 보기: 아주 작은 다음 토큰 예측기

실제 LLM은 신경망(트랜스포머)으로 확률을 계산하지만, "앞의 토큰을 보고 다음 토큰의 확률을 정한 뒤 하나씩 뽑는다"는 흐름은 단순한 횟수 세기로도 흉내 낼 수 있다. 외부 패키지 없이 실행되는 코드다. `next_token.py`로 저장한다.

```python
import math
import random
from collections import Counter, defaultdict

corpus = (
    "고양이가 밥을 먹는다. 고양이가 잠을 잔다. 고양이가 밥을 먹는다. "
    "강아지가 밥을 먹는다. 강아지가 공을 쫓는다. 고양이가 공을 쫓는다."
)

# 1. 토큰화: 여기서는 띄어쓰기 단위로 자른다
tokens = corpus.replace(".", " .").split()
print("토큰 수:", len(tokens), "| 앞 6개:", tokens[:6])

# 2. 학습: 각 토큰 다음에 어떤 토큰이 몇 번 왔는지 센다
next_counts = defaultdict(Counter)
for cur, nxt in zip(tokens, tokens[1:]):
    next_counts[cur][nxt] += 1
print("'고양이가' 다음:", dict(next_counts["고양이가"]))

# 3. 다음 토큰 확률: 횟수를 점수로 보고 온도를 적용한 softmax
def probs(word, temperature):
    cands = next_counts[word]
    scores = {w: math.log(c) / temperature for w, c in cands.items()}
    m = max(scores.values())
    exp = {w: math.exp(s - m) for w, s in scores.items()}
    total = sum(exp.values())
    return {w: round(v / total, 2) for w, v in exp.items()}

for t in (0.5, 1.0, 2.0):
    print(f"온도 {t}:", probs("고양이가", t))

# 4. 생성: 한 토큰씩 골라 이어 붙인다
def generate(start, temperature, seed, max_tokens=8):
    rng = random.Random(seed)
    out = [start]
    while len(out) < max_tokens and out[-1] != ".":
        p = probs(out[-1], temperature)
        out.append(rng.choices(list(p), weights=list(p.values()))[0])
    return " ".join(out)

for seed in (1, 2, 3):
    print(f"seed {seed}:", generate("강아지가", 1.0, seed))
```

Python 3.13에서 실행한 결과다.

```text
토큰 수: 24 | 앞 6개: ['고양이가', '밥을', '먹는다', '.', '고양이가', '잠을']
'고양이가' 다음: {'밥을': 2, '잠을': 1, '공을': 1}
온도 0.5: {'밥을': 0.67, '잠을': 0.17, '공을': 0.17}
온도 1.0: {'밥을': 0.5, '잠을': 0.25, '공을': 0.25}
온도 2.0: {'밥을': 0.41, '잠을': 0.29, '공을': 0.29}
seed 1: 강아지가 밥을 먹는다 .
seed 2: 강아지가 공을 쫓는다 .
seed 3: 강아지가 밥을 먹는다 .
```

이 작은 코드에 LLM의 핵심 개념이 모두 들어 있다.

| 코드 | LLM에서 |
| --- | --- |
| 띄어쓰기로 자르기 | 토크나이저 |
| "다음에 온 횟수" 세기 | 학습. 실제로는 신경망의 파라미터를 조정한다 |
| `probs()` | 모델이 매긴 다음 토큰 확률 |
| `generate()`의 반복 | 자기회귀 생성 |
| `seed`마다 다른 문장 | 같은 질문에도 답이 달라지는 이유 |

차이도 분명하다. 이 코드는 **바로 앞 토큰 하나만** 본다. 그래서 "강아지가 잠을 잔다"처럼 학습 데이터에 없는 조합은 만들지 못하고, 긴 문맥도 기억하지 못한다. 실제 LLM은 트랜스포머 구조 덕분에 앞의 토큰 수천~수십만 개를 한꺼번에 보고, 처음 보는 조합도 비슷한 패턴에서 일반화해 만들어 낸다.

## 온도: 얼마나 모험할 것인가

위 결과에서 온도를 낮추면 가장 흔한 `밥을`의 확률이 0.67로 커지고, 높이면 0.41로 줄어 후보들이 고르게 됐다. **온도(temperature)**는 이 확률 분포를 얼마나 뾰족하게 또는 평평하게 만들지 정하는 값이다.

| 온도 | 결과 | 어울리는 작업 |
| --- | --- | --- |
| 0에 가까움 | 거의 항상 가장 확률 높은 토큰. 답이 일정하다 | 분류, 정보 추출, 코드 |
| 1 전후 | 확률대로 뽑음 | 일반 대화 |
| 1보다 큼 | 낮은 확률 후보도 자주 나옴. 다양하지만 엉뚱해질 수 있다 | 아이디어 내기, 창작 |

온도를 0으로 둬도 서비스 환경에 따라 결과가 완전히 같다는 보장은 없다. 같은 답이 꼭 필요하면 출력 형식을 정하고 결과를 검증하는 쪽으로 설계한다. 이 내용은 [프롬프트 엔지니어링]({{ '/ai/using-ai/prompt-engineering/' | relative_url }})에서 이어진다.

## 컨텍스트 창: 한 번에 볼 수 있는 양

모델이 다음 토큰을 예측할 때 참고하는 입력 전체를 **컨텍스트**라고 하고, 그 최대 길이를 **컨텍스트 창(context window)**이라고 한다. 시스템 지시, 이전 대화, 첨부 문서, 도구 정의, 그리고 지금 만들어지는 답까지 모두 이 창 안에 들어가야 한다.

LLM은 기본적으로 **대화를 기억하지 않는다.** 채팅 앱에서 이전 대화를 기억하는 것처럼 보이는 것은, 앱이 매번 이전 대화를 다시 입력에 넣어 보내기 때문이다. 대화가 길어질수록 입력 토큰이 쌓이고, 창이 가득 차면 오래된 내용을 요약하거나 버려야 한다. 무엇을 넣고 뺄지 설계하는 일이 [컨텍스트 엔지니어링]({{ '/ai/using-ai/context-engineering/' | relative_url }})이다.

## 학습과 추론

| 단계 | 하는 일 | 누가 하나 |
| --- | --- | --- |
| 사전 학습(pre-training) | 방대한 글로 다음 토큰 예측을 배운다. 수천 대의 GPU로 몇 주~몇 달 | 모델 개발사 |
| 후속 학습(post-training) | 지시를 따르고, 대화하고, 위험한 요청을 거절하도록 다듬는다 | 모델 개발사 |
| 미세 조정(fine-tuning) | 특정 분야 데이터로 추가 학습한다 | 필요한 경우 사용자 |
| 추론(inference) | 학습이 끝난 모델에 입력을 넣어 답을 얻는다 | 모든 사용자 |

앱 개발자가 하는 일은 대부분 **추론**이다. 모델의 지식은 학습 시점에 고정되므로, 그 이후의 사실이나 회사 내부 문서는 모델이 모른다. 이것을 보완하는 방법이 질문할 때 관련 문서를 찾아 함께 넣어 주는 [RAG]({{ '/ai/using-ai/rag/' | relative_url }})다. 학습 원리 자체는 [머신러닝 기초]({{ '/ai/using-ai/machine-learning/' | relative_url }})와 [Mac에서 TensorFlow 실습]({{ '/ai/using-ai/tensorflow-mac/' | relative_url }})에서 다룬다.

## 환각: 그럴듯한 오답

모델은 "사실인 말"이 아니라 "다음에 올 법한 말"을 고른다. 그래서 모르는 내용도 그럴듯한 문장으로 만들어 낼 수 있다. 존재하지 않는 논문 제목, 틀린 API 이름, 지어낸 숫자가 대표적이다. 이것을 **환각(hallucination)**이라고 한다.

환각을 줄이는 방법은 모델에게 "정확히 답하라"고 부탁하는 것보다 구조로 막는 쪽이 효과적이다.

- 근거 자료를 함께 넣고, 자료에 있는 내용만 답하게 한다 ([RAG]({{ '/ai/using-ai/rag/' | relative_url }}))
- 답에 근거 문장을 인용하게 하고, 그 인용이 실제로 자료에 있는지 프로그램이 확인한다
- 모르면 모른다고 답할 수 있는 선택지를 준다
- 결과를 미리 정한 사례로 반복 측정한다 ([평가]({{ '/ai/using-ai/evaluation/' | relative_url }}))

## 모델에서 에이전트로

LLM 자체는 글을 입력받아 글을 내놓는 함수일 뿐이다. 파일을 열거나 검색하거나 메일을 보내지는 못한다. 그래서 프로그램이 모델에게 "쓸 수 있는 도구 목록"을 알려 주고, 모델이 "이 도구를 이 인자로 불러 달라"고 답하면 프로그램이 실제로 실행해 결과를 다시 모델에게 보여 준다. 이것을 **도구 호출(tool calling)**이라고 한다.

도구 호출을 여러 번 반복하며 스스로 다음 행동을 정해 일을 끝까지 처리하는 시스템을 **에이전트**라고 부른다. 이 블로그의 AI 글들은 대부분 이 에이전트를 잘 만드는 방법을 다룬다.

| 하고 싶은 일 | 읽을 글 |
| --- | --- |
| 지시를 잘 쓰기 | [프롬프트 엔지니어링]({{ '/ai/using-ai/prompt-engineering/' | relative_url }}) |
| 입력에 무엇을 넣을지 정하기 | [컨텍스트 엔지니어링]({{ '/ai/using-ai/context-engineering/' | relative_url }}) |
| 도구 실행 반복 만들기 | [루프 엔지니어링]({{ '/ai/using-ai/loop-engineering/' | relative_url }}) |
| 도구·권한·기록을 묶는 실행 환경 | [하네스 엔지니어링]({{ '/ai/using-ai/harness-engineering/' | relative_url }}) |
| 결과를 측정하기 | [AI 평가와 개선]({{ '/ai/using-ai/evaluation/' | relative_url }}) |

## 정리

- LLM은 지금까지의 토큰 열을 보고 다음 토큰의 확률을 매기는 모델이며, 하나씩 골라 이어 붙여 글을 만든다.
- 토큰은 모델이 글을 처리하는 단위로, 요금·길이 제한·속도의 기준이다.
- 온도는 다음 토큰을 얼마나 고르게 뽑을지 정한다.
- 모델은 대화를 기억하지 않는다. 앱이 매번 이전 대화를 컨텍스트 창에 다시 넣는다.
- 모델의 지식은 학습 시점에 고정되고, 모르는 것도 그럴듯하게 만들어 낼 수 있다(환각).
- 도구 호출을 반복하며 일을 처리하는 시스템이 에이전트다.

## 실습 소스

- [next_token.py]({{ '/assets/examples/ai/llm-basics/next_token.py' | relative_url }})

## 참고

- [Anthropic: Claude Docs - Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Vaswani et al., Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762)
- [Andrej Karpathy: Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY)
