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

query = "비동기 프로그래밍 패턴"
query_vector = embedding_model.encode([query], normalize_embeddings=True).tolist()

results = collection.query(
    query_embeddings=query_vector,
    n_results=2,
)

for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"거리: {distance:.4f} | {doc}")

query = "AI 에이전트 도구"
query_vector = embedding_model.encode([query], normalize_embeddings=True).tolist()

results = collection.query(
    query_embeddings=query_vector,
    n_results=2,
    where={"category": "ai"},  # ai 카테고리만
)

for doc in results["documents"][0]:
    print(doc)
