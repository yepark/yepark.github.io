from pydantic import BaseModel, Field
from langchain_core.output_parsers import (
    PydanticOutputParser,
)
from langchain_core.prompts import ChatPromptTemplate
from store import store
from prompt import format_docs
from llm import model

class Answer(BaseModel):
    answer: str = Field(description="질문에 대한 답")
    sources: list[str] = Field(description="근거 파일 이름")
    found: bool = Field(description="자료에 답이 있으면 true")

parser = PydanticOutputParser(pydantic_object=Answer)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "자료만 보고 답하라.\n{format}\n\n자료:\n{context}"),
    ("human", "{question}"),
]).partial(format=parser.get_format_instructions())

retriever = store.as_retriever(search_kwargs={"k": 2})
q = "무료 플랜은 프로젝트를 몇 개 만들 수 있나요?"
docs = retriever.invoke(q)
msg = (prompt | model).invoke(
    {"context": format_docs(docs), "question": q}
)
print("모델 원문:", repr(msg.content))
result = parser.invoke(msg)
print("파싱 결과:", repr(result))
print("result.sources:", result.sources)
