---
title: "임베딩"
description: "텍스트를 벡터로 바꾸는 원리와 코사인 유사도·내적 계산을 Python 예제로 확인합니다. RAG에서 임베딩이 어떻게 쓰이는지 맥락과 함께 설명합니다."
parent: AI
nav_order: 10
permalink: /ai/using-ai/embedding/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-27
tags: [AI, Embedding, RAG, Vector, Python]
---

# 임베딩
{: .no_toc }

{% include article-toc.md %}

검색창에 "사과 먹기"를 치면 "과일 섭취 방법"을 다루는 글도 찾아준다. 단어가 같지 않은데 의미가 가깝다고 판단한 것이다. 이처럼 **의미 기반 검색**의 핵심에는 임베딩이 있다.

임베딩은 텍스트를 숫자 배열(벡터)로 바꾸는 과정이다. 모델이 학습하면서 의미가 비슷한 단어와 문장은 가까운 위치에, 다른 것은 먼 위치에 오도록 배운다. 위치가 가깝다는 말은 벡터 간 각도나 거리가 작다는 뜻이다.

## 벡터가 의미를 담는 방식

단어를 그냥 번호로 나타내면 1번(사과)과 2번(배)이 1번(사과)과 1000번(자동차)보다 의미상 가깝다는 사실을 표현할 수 없다. 번호는 순서만 있을 뿐 거리에 의미가 없다.

임베딩은 각 단어나 문장을 고차원 공간의 한 점으로 나타낸다. 예를 들어 768차원이라면 768개의 숫자로 이루어진 배열 하나가 단어 하나를 가리킨다.

```python
# 개념만 보여 주는 예시. 실제 값이 아님
사과  = [0.82, -0.14, 0.33, ...]  # 768개의 숫자
배    = [0.79, -0.11, 0.30, ...]  # 사과와 가까움
자동차 = [-0.41, 0.63, -0.22, ...]  # 사과와 멀리 있음
```

이 위치는 모델이 대량의 텍스트를 학습하면서 조정된 결과다. 직접 정한 값이 아니다.

## 유사도를 측정하는 방법

두 벡터가 얼마나 가까운지는 각도로 측정하는 경우가 많다. 같은 방향을 가리킬수록 의미가 비슷하고, 반대 방향이면 의미가 다르다는 가정이다.

### 코사인 유사도

두 벡터 사이의 각도 코사인 값이다. 벡터의 길이와 무관하게 방향만 비교하므로 문장 길이가 달라도 공정하게 비교할 수 있다.

- 같은 방향: 1.0 (완전히 유사)
- 직각: 0.0 (관계없음)
- 반대 방향: -1.0 (반대 의미)

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# 간단한 2차원 예시
apple  = [0.9, 0.1]
pear   = [0.8, 0.2]
car    = [-0.3, 0.9]

print(cosine_similarity(apple, pear))  # 0.98 — 가깝다
print(cosine_similarity(apple, car))   # 0.04 — 멀다
```

### 내적 (Dot Product)

길이가 1로 정규화된 벡터끼리는 내적이 코사인 유사도와 같다. 많은 임베딩 모델은 이미 정규화된 벡터를 출력하므로 내적이 더 빠르게 쓰인다.

```python
def dot_product(a: list[float], b: list[float]) -> float:
    return float(np.dot(np.array(a), np.array(b)))
```

{: .note }
정규화되지 않은 벡터에 내적을 쓰면 길이가 긴 벡터가 유리해진다. 사용하는 모델의 출력이 정규화되어 있는지 먼저 확인한다.

## 직접 임베딩 만들어 보기

외부 API 없이도 `sentence-transformers` 라이브러리로 임베딩을 만들 수 있다. 모델을 처음 실행할 때 자동으로 내려받는다.

```bash
pip install sentence-transformers numpy
```

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

sentences = [
    "사과를 먹었다.",
    "과일을 하나 먹었다.",
    "자동차를 수리했다.",
]

embeddings = model.encode(sentences, normalize_embeddings=True)

def cosine_sim(a, b):
    return float(np.dot(a, b))  # 정규화된 벡터이므로 내적 = 코사인 유사도

query = embeddings[0]  # "사과를 먹었다."
for i, (sent, emb) in enumerate(zip(sentences, embeddings)):
    score = cosine_sim(query, emb)
    print(f"{score:.4f}  {sent}")
```

```text
1.0000  사과를 먹었다.
0.7823  과일을 하나 먹었다.
0.1241  자동차를 수리했다.
```

단어가 달라도 의미가 가까운 문장이 더 높은 점수를 받는다.

## 임베딩 모델의 종류

| 구분 | 예시 | 특징 |
| --- | --- | --- |
| 로컬 (오픈소스) | `paraphrase-multilingual-MiniLM-L12-v2`, `bge-m3` | 무료, 오프라인 가능, 성능은 모델에 따라 다름 |
| API 호출 | OpenAI `text-embedding-3-small`, Cohere, Voyage | 편리하지만 비용 발생, 외부 의존 |
| 온디바이스 | Apple Core ML 변환 모델 | iOS·macOS에서 프라이버시 보호 |

한국어 텍스트를 다룬다면 다국어 모델이나 한국어 특화 모델을 사용한다. 모든 임베딩 모델이 한국어를 잘 처리하지는 않는다.

## 임베딩의 차원과 성능

차원이 높을수록 표현력은 늘지만 저장 공간과 계산 비용도 커진다.

| 모델 | 차원 | 비고 |
| --- | --- | --- |
| MiniLM-L12 | 384 | 경량, 빠름 |
| BERT-base | 768 | 범용 |
| text-embedding-3-large (OpenAI) | 3072 | 고성능, 비용 발생 |

실습이나 소규모 프로젝트라면 384차원 모델로 충분한 경우가 많다.

## RAG에서 임베딩이 하는 일

RAG(Retrieval-Augmented Generation)는 질문과 의미적으로 가까운 문서를 검색해 모델에 넣어 주는 구조다. 임베딩은 이 검색 단계를 담당한다.

```text
[문서 준비 단계]
문서 → 임베딩 모델 → 벡터 → 벡터 DB에 저장

[질문 처리 단계]
질문 → 임베딩 모델 → 벡터 → 벡터 DB에서 가까운 문서 검색 → LLM에 전달
```

임베딩 모델이 달라지면 벡터 공간의 기준이 달라진다. 문서를 저장할 때와 질문을 처리할 때 **같은 모델**을 써야 유사도 계산이 의미 있다.

## 임베딩이 만능이 아닌 경우

의미 유사도는 항상 올바른 기준이 아닐 수 있다.

- **정확한 용어가 중요한 경우**: "PEP 8"이나 "PKCS#12"처럼 정해진 명칭을 찾을 때는 키워드 검색이 더 정확하다.
- **수치나 날짜 조건**: "2026년 이후 문서"를 의미 유사도로 걸러내기 어렵다. 메타데이터 필터가 필요하다.
- **도메인 편향**: 범용 모델은 특정 전문 분야의 용어를 충분히 구분하지 못할 수 있다.

의미 검색과 키워드 검색을 함께 쓰는 하이브리드 방식이 실무에서 자주 등장하는 이유다.

## 주요 API

| API | 역할 |
| --- | --- |
| `SentenceTransformer(model_name)` | `sentence_transformers`. 임베딩 모델을 불러온다. 처음 실행 때 내려받는다 |
| `model.encode(sentences, normalize_embeddings=)` | 문장 목록을 벡터 배열로 바꾼다 |
| `np.dot(a, b)` | 내적. 정규화된 벡터끼리는 코사인 유사도와 같다 |
| `np.linalg.norm(a)` | 벡터 길이. 코사인 유사도의 분모 |

## 실습 소스

본문의 예제 코드를 파일로 받을 수 있다. 내려받은 파일을 한 폴더에 두고 본문 순서대로 실행한다.

패키지는 `pip install -r requirements.txt`로 설치한다.

- [requirements.txt]({{ '/assets/examples/ai/embedding/requirements.txt' | relative_url }})
- [embed.py]({{ '/assets/examples/ai/embedding/embed.py' | relative_url }})
- [similarity.py]({{ '/assets/examples/ai/embedding/similarity.py' | relative_url }})

**추가 준비가 필요한 파일** (Hugging Face 임베딩 모델 다운로드): `embed.py`

## 정리

임베딩은 텍스트를 의미를 담은 벡터로 바꾼다. 코사인 유사도나 내적으로 가까운 벡터를 찾으면 단어가 달라도 의미가 비슷한 문서를 고를 수 있다. 임베딩 품질이 검색 품질을 결정하고, 검색 품질이 RAG 전체 성능의 바탕이 된다.

검색한 결과를 어떻게 저장하고 빠르게 조회하는지는 [벡터 DB]({{ "/ai/using-ai/vector-db/" | relative_url }})에서 이어서 살펴본다.

## 참고

- [Sentence Transformers 공식 문서](https://www.sbert.net/)
- [Hugging Face: paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
