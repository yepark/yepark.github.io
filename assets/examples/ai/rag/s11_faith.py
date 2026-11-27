import re
from langchain_core.output_parsers import StrOutputParser
from store import store
from prompt import prompt, format_docs
from llm import model

retriever = store.as_retriever(search_kwargs={"k": 2})
answer_chain = prompt | model | StrOutputParser()

def check(q):
    docs = retriever.invoke(q)
    context = format_docs(docs)
    answer = answer_chain.invoke(
        {"context": context, "question": q}
    )
    got = {d.metadata["source"] for d in docs}
    cited = set(re.findall(r"\[([\w.-]+\.md)\]", answer))
    nums = set(re.findall(r"\d[\d,]*", answer))
    ctx_nums = set(re.findall(r"\d[\d,]*", context))
    print("Q:", q)
    print("A:", answer)
    print("  인용이 검색 결과 안에 있나:", cited <= got, cited)
    print("  답의 숫자가 자료에 있나:", nums <= ctx_nums,
          nums - ctx_nums or "")

for q in ["결제하고 10일 지났는데 환불되나요?",
          "프로 플랜은 한 달에 얼마예요?"]:
    check(q)
