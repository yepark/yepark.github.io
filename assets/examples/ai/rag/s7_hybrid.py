from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from docs import raw
from store import store

chunks = RecursiveCharacterTextSplitter(
    chunk_size=200, chunk_overlap=20
).split_documents(raw)

bm25 = BM25Retriever.from_documents(
    chunks, preprocess_func=str.split, k=2
)
vector = store.as_retriever(search_kwargs={"k": 2})

def names(docs):
    return [d.metadata["source"] for d in docs]

q = "E-4012 오류가 떴어요"
print("BM25:", names(bm25.invoke(q)))
print("벡터:", names(vector.invoke(q)))
for w in ([0.5, 0.5], [0.7, 0.3]):
    hybrid = EnsembleRetriever(
        retrievers=[bm25, vector], weights=w
    )
    print("하이브리드", w, names(hybrid.invoke(q)))
