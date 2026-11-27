---
title: "벡터 DB"
description: "벡터를 저장하고 빠르게 검색하는 원리를 ANN 인덱스와 메타데이터 필터 중심으로 설명합니다. ChromaDB 예제로 문서 저장부터 RAG 연결까지 확인합니다."
parent: AI
nav_order: 11
permalink: /ai/using-ai/vector-db/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-27
tags: [AI, Vector-DB, RAG, ChromaDB, Python]
---

# 벡터 DB
{: .no_toc }

{% include article-toc.md %}

[임베딩]({{ "/ai/using-ai/embedding/" | relative_url }})으로 문서를 벡터로 바꿀 수 있다면, 그 벡터를 어디에 어떻게 저장하고 빠르게 꺼낼까? 문서가 수백만 개가 되면 모든 벡터와 질문 벡터를 하나씩 비교하는 방식으로는 버티기 어렵다. 벡터 DB는 이 검색 문제를 해결하기 위해 만들어진 저장소다.

## 일반 DB와 무엇이 다른가

일반 관계형 DB는 "나이가 30 이상인 사용자"처럼 조건이 정확히 일치하는 행을 찾는다. 텍스트 검색도 단어가 포함돼 있는지를 확인한다.

벡터 DB는 "이 벡터와 가장 가까운 k개의 벡터를 찾아 줘"라는 질문에 답한다. 조건이 정확한 일치가 아니라 거리나 각도다.

| 구분 | 질문 형태 | 적합한 사례 |
| --- | --- | --- |
| 관계형 DB | `WHERE category = 'ios'` | 조건이 명확한 필터링 |
| 전문 검색 | `MATCH '동시성'` | 키워드 포함 여부 |
| 벡터 DB | 가장 가까운 k개의 벡터 | 의미 기반 유사도 검색 |

## ANN: 정확하지 않아도 충분히 빠른 검색

벡터 수가 많아지면 모든 벡터와 거리를 계산하는 완전 탐색(Brute Force)은 느리다. 대부분의 벡터 DB는 **근사 최근접 이웃(ANN, Approximate Nearest Neighbor)** 알고리즘으로 이를 해결한다.

정확한 답 대신, 아주 가까운 답을 훨씬 빠르게 찾는다. 실제로 "사과"를 검색할 때 완벽히 1위인 문서 대신 2~3위 문서가 반환되어도 품질 차이를 거의 느끼지 못한다.

### HNSW

Hierarchical Navigable Small World. 계층 그래프로 가까운 이웃끼리 연결해 두고, 검색할 때 계층을 타고 내려오며 후보를 좁힌다. ChromaDB, Weaviate 등 여러 벡터 DB에서 기본 인덱스로 쓴다.

```text
[계층 2] ←→ 듬성듬성 연결 (큰 그림)
[계층 1] ←→ 보통 연결
[계층 0] ←→ 촘촘하게 연결 (실제 데이터)
```

삽입할 때 그래프를 구성해 두기 때문에 검색이 빠르다. 데이터가 늘어날수록 초기 삽입보다 검색 성능이 더 중요한 경우에 적합하다.

### IVF (Inverted File Index)

벡터를 클러스터로 묶어 두고, 질문 벡터와 가까운 클러스터만 탐색한다. 클러스터 수(`nlist`)와 탐색 범위(`nprobe`)를 조정해 속도와 정확도를 균형 있게 맞출 수 있다.

## 메타데이터 필터

벡터 DB는 벡터와 함께 메타데이터(카테고리, 날짜, 출처 등)도 저장한다. 유사도 검색 전에 메타데이터 조건으로 범위를 좁히면 불필요한 계산을 줄이고 정확도를 높일 수 있다.

```text
질문: "Swift에서 메모리 관리하는 법"
필터: category = "swift" AND date >= "2025-01-01"
→ swift 카테고리의 최근 문서 중에서 의미 검색
```

의미 유사도만으로는 "2026년 이후 문서"나 "iOS 카테고리만" 같은 조건을 처리하기 어렵다. 메타데이터 필터와 조합해야 한다.

## ChromaDB로 직접 해 보기

ChromaDB는 로컬에서 바로 실행할 수 있는 오픈소스 벡터 DB다. API 키나 서버 없이 메모리나 로컬 파일에 저장한다.

```bash
pip install chromadb sentence-transformers
```

### 문서 저장

```python
import chromadb
from sentence_transformers import SentenceTransformer

# 모델과 DB 준비
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
client = chromadb.Client()  # 메모리 저장. 파일 저장은 PersistentClient(path="./db")
collection = client.create_collection("dev-notes")

# 저장할 문서
documents = [
    "Swift의 async/await는 비동기 코드를 동기 코드처럼 작성하게 해 준다.",
    "ARC는 참조 카운트가 0이 되면 메모리를 자동으로 해제한다.",
    "Core Data는 객체 그래프와 영속성을 관리하는 Apple의 프레임워크다.",
    "LangGraph는 상태를 가진 멀티 에이전트 그래프를 실행하는 라이브러리다.",
    "RAG는 모델이 외부 문서를 검색해 답변 품질을 높이는 기법이다.",
]

metadatas = [
    {"category": "swift", "date": "2026-11-01"},
    {"category": "swift", "date": "2026-11-02"},
    {"category": "ios",   "date": "2026-11-03"},
    {"category": "ai",    "date": "2026-11-04"},
    {"category": "ai",    "date": "2026-11-05"},
]

# 임베딩 생성
vectors = embedding_model.encode(documents, normalize_embeddings=True).tolist()

collection.add(
    ids=[str(i) for i in range(len(documents))],
    embeddings=vectors,
    documents=documents,
    metadatas=metadatas,
)

print(f"저장된 문서 수: {collection.count()}")
```

### 유사도 검색

```python
query = "비동기 프로그래밍 패턴"
query_vector = embedding_model.encode([query], normalize_embeddings=True).tolist()

results = collection.query(
    query_embeddings=query_vector,
    n_results=2,
)

for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"거리: {distance:.4f} | {doc}")
```

```text
거리: 0.1842 | Swift의 async/await는 비동기 코드를 동기 코드처럼 작성하게 해 준다.
거리: 0.5631 | ARC는 참조 카운트가 0이 되면 메모리를 자동으로 해제한다.
```

{: .note }
ChromaDB의 `distances`는 코사인 거리(1 - 유사도)를 반환한다. 거리가 작을수록 가까운 문서다.

### 메타데이터 필터와 함께 검색

```python
query = "AI 에이전트 도구"
query_vector = embedding_model.encode([query], normalize_embeddings=True).tolist()

results = collection.query(
    query_embeddings=query_vector,
    n_results=2,
    where={"category": "ai"},  # ai 카테고리만
)

for doc in results["documents"][0]:
    print(doc)
```

```text
LangGraph는 상태를 가진 멀티 에이전트 그래프를 실행하는 라이브러리다.
RAG는 모델이 외부 문서를 검색해 답변 품질을 높이는 기법이다.
```

## 청킹: 문서를 얼마나 잘라야 할까

임베딩 모델은 입력 길이에 제한이 있다. 긴 문서는 여러 조각(청크)으로 나눠 각각 임베딩한다. 청킹 방식이 검색 품질에 직접 영향을 미친다.

| 방식 | 설명 | 주의점 |
| --- | --- | --- |
| 고정 크기 | 500자마다 자른다 | 문장이나 문단 중간에서 잘릴 수 있다 |
| 문장 단위 | 문장 경계에서 자른다 | 짧은 문장의 맥락이 부족할 수 있다 |
| 문단 단위 | 문단 기준으로 자른다 | 블로그 글·기술 문서에 적합 |
| 겹치기 (overlap) | 앞 청크와 일부 겹치게 자른다 | 경계 주변 맥락을 보존 |

```text
나쁜 청킹: "Swift의 async/await는 비동기 코드를|동기 코드처럼 작성하게 해 준다."
좋은 청킹: "Swift의 async/await는 비동기 코드를 동기 코드처럼 작성하게 해 준다."
```

검색할 때는 작은 청크로 위치를 찾고, 모델에 넣을 때는 더 넓은 문맥을 함께 제공하는 방식을 쓰기도 한다.

## 주요 벡터 DB 비교

| 이름 | 특징 | 적합한 상황 |
| --- | --- | --- |
| ChromaDB | 로컬 실행, 간단한 API | 프로토타입, 소규모 |
| Qdrant | 고성능 Rust 구현, 메타데이터 필터 강력 | 중대형 서비스 |
| Weaviate | 그래프 + 벡터 혼합, GraphQL API | 복잡한 관계가 있는 데이터 |
| Pinecone | 완전 관리형 클라우드 | 운영 편의가 중요할 때 |
| pgvector | PostgreSQL 확장 | 기존 Postgres 환경 |

규모가 작다면 ChromaDB로 시작하고, 운영 환경에서는 Qdrant나 pgvector를 많이 선택한다.

## RAG 전체 흐름에서 벡터 DB의 위치

```text
[준비]
문서 → 청킹 → 임베딩 → 벡터 DB 저장

[실행]
질문 → 임베딩 → 벡터 DB 검색 (ANN + 메타데이터 필터)
     → 상위 k개 문서 → LLM 프롬프트에 삽입 → 응답
```

벡터 DB는 검색의 범위와 정확도를 결정한다. 임베딩 모델이 좋아도 청킹이 잘못되면 엉뚱한 조각이 검색되고, 검색된 조각이 맥락이 없으면 LLM도 올바른 답을 내기 어렵다.

## 운영할 때 주의할 점

**같은 모델을 유지한다.**  
저장할 때와 검색할 때 모델이 달라지면 벡터 공간 기준이 맞지 않아 유사도 계산이 의미 없어진다. 모델을 교체하면 전체 벡터를 다시 만들어야 한다.

**인덱스를 필요할 때 만든다.**  
HNSW 인덱스는 삽입 후에 구성된다. 문서를 먼저 모두 올리고 인덱스를 한 번에 만드는 편이 순서대로 올리며 계속 갱신하는 것보다 빠르다.

**검색 결과를 그대로 믿지 않는다.**  
유사도 점수가 높아도 답변에 필요한 내용이 없을 수 있다. 검색 단계와 생성 단계를 각각 평가해야 한다. 검색이 맞았는지와 생성이 맞았는지는 별개의 문제다.

## 주요 API

| API | 역할 |
| --- | --- |
| `chromadb.Client()` | 메모리에 저장하는 클라이언트 |
| `chromadb.PersistentClient(path=)` | 로컬 폴더에 저장하는 클라이언트 |
| `client.create_collection(name, metadata=)` | 컬렉션 생성. `{"hnsw:space": "cosine"}`로 거리 방식을 정한다 |
| `client.get_or_create_collection(name)` | 있으면 가져오고 없으면 만든다 |
| `collection.add(ids=, documents=, embeddings=, metadatas=)` | 문서와 벡터, 메타데이터 저장 |
| `collection.query(query_embeddings=, n_results=, where=)` | 가까운 벡터 검색. `where`로 메타데이터 필터 |
| `collection.count()` | 저장된 항목 수 |

## 실습 소스

본문의 예제 코드를 파일로 받을 수 있다. 내려받은 파일을 한 폴더에 두고 본문 순서대로 실행한다.

패키지는 `pip install -r requirements.txt`로 설치한다.

- [requirements.txt]({{ '/assets/examples/ai/vector-db/requirements.txt' | relative_url }})
- [chroma_demo.py]({{ '/assets/examples/ai/vector-db/chroma_demo.py' | relative_url }})

**추가 준비가 필요한 파일** (Hugging Face 임베딩 모델 다운로드): `chroma_demo.py`

## 정리

벡터 DB는 임베딩 벡터를 저장하고 ANN으로 빠르게 유사한 벡터를 찾아 주는 저장소다. 메타데이터 필터와 조합하면 의미 검색과 조건 필터링을 함께 쓸 수 있다. 청킹 방식, 모델 일관성, 검색 결과 평가가 RAG 품질을 결정하는 주요 변수다.

## 참고

- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [Qdrant 공식 문서](https://qdrant.tech/documentation/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [HNSW 논문 요약 (Pinecone 블로그)](https://www.pinecone.io/learn/series/faiss/hnsw/)
