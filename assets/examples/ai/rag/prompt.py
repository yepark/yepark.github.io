from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "아래 자료만 보고 한국어로 짧게 답하라. "
     "답 끝에 근거로 쓴 자료의 대괄호 이름을 붙여라. "
     "자료에 답이 없으면 '자료에 없습니다'라고만 답하라."
     "\n\n자료:\n{context}"),
    ("human", "{question}"),
])

def format_docs(docs):
    return "\n".join(
        f"[{d.metadata['source']}] "
        + d.page_content.replace("\n", " ")
        for d in docs
    )
