import sys
from store import build

size = int(sys.argv[1])
store = build(size, 10)
q = "결제하고 10일 지났는데 환불되나요?"
hits = store.similarity_search_with_score(q, k=3)
for doc, score in hits:
    src = doc.metadata["source"]
    text = doc.page_content[:20].replace("\n", " ")
    print(f"{score:.4f} [{src}] {text}")
