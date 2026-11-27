from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from store import store
from llm import model

rewrite = ChatPromptTemplate.from_messages([
    ("system",
     "대화와 후속 질문을 보고, 혼자 읽어도 뜻이 "
     "통하는 검색용 질문 한 줄로 바꿔라. "
     "질문만 출력하라."),
    ("human", "대화:\n{history}\n\n후속 질문: {question}"),
]) | model | StrOutputParser()

history = ("사용자: E-4013 오류가 뭐예요?\n"
           "상담원: 카드 한도를 넘었다는 뜻입니다.")
q = "그럼 4012는요?"

def top(text):
    hits = store.similarity_search_with_score(text, k=2)
    return [(d.metadata["source"], round(s, 3))
            for d, s in hits]

print("원래 질문:", q, top(q))
new_q = rewrite.invoke({"history": history, "question": q})
print("바꾼 질문:", new_q, top(new_q))
