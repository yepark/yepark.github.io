from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from docs import raw

splitter = RecursiveCharacterTextSplitter(
    chunk_size=60,
    chunk_overlap=10,
)
chunks = splitter.split_documents(raw)

print("청크 수:", len(chunks))
for c in chunks:
    src = c.metadata["source"]
    print(f"[{src}] {c.page_content!r}")
