from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch, RunnableLambda)
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel)

prompt = ChatPromptTemplate.from_messages(
    [("human", "{q}")])
model = FakeListChatModel(responses=["모델의 답"])
chain = prompt | model | StrOutputParser()
print(chain.invoke({"q": "안녕"}))
print([s.__class__.__name__ for s in chain.steps])

# 분기 1: RunnableBranch
branch = RunnableBranch(
    (lambda d: "코드" in d["q"],
     RunnableLambda(lambda d: "코드 담당")),
    RunnableLambda(lambda d: "일반 담당"),  # 기본값
)
print(branch.invoke({"q": "코드 리뷰"}),
      branch.invoke({"q": "날씨"}))

# 분기 2: 함수가 Runnable을 돌려주면 그것이 실행된다
code = RunnableLambda(lambda d: "코드 담당")
chat = RunnableLambda(lambda d: "일반 담당")
route = RunnableLambda(
    lambda d: code if "코드" in d["q"] else chat)
print(route.invoke({"q": "코드 리뷰"}))
