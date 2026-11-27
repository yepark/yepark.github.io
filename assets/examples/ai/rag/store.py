from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from docs import raw

MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
emb = HuggingFaceEmbeddings(
    model_name=f"sentence-transformers/{MODEL}",
    encode_kwargs={"normalize_embeddings": True},
)

def build(size, overlap):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap
    )
    chunks = splitter.split_documents(raw)
    return InMemoryVectorStore.from_documents(chunks, emb)

store = build(200, 20)
