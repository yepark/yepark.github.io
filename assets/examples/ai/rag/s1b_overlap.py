from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

text = "가 나 다 라 마 바 사 아 자 차 카 타 파 하"
for overlap in (0, 4):
    s = RecursiveCharacterTextSplitter(
        chunk_size=12,
        chunk_overlap=overlap,
    )
    print(overlap, s.split_text(text))
