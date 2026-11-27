from sentence_transformers import CrossEncoder
from store import store

RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
ce = CrossEncoder(RERANKER)

q = "E-4012 오류가 떴어요"
cands = store.similarity_search(q, k=4)   # 1차: 넓게
print("벡터 순서:", [d.metadata["source"] for d in cands])

scores = ce.predict([(q, d.page_content) for d in cands])
ranked = sorted(zip(scores, cands), key=lambda x: -x[0])
print("재정렬 후:")
for s, d in ranked:
    print(f"  {s:7.3f} {d.metadata['source']}")
