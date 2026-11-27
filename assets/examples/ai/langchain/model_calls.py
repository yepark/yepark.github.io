import asyncio
from langchain.messages import (
    SystemMessage, HumanMessage, AIMessage)
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)

fake = GenericFakeChatModel(messages=iter([
    "리스트는 여러 값을 순서대로 담는다.",
    "첫째 답", "둘째 답",
    "비동기 답",
]))

# 1) invoke: 메시지 객체 / 딕셔너리 / 튜플 모두 된다
msgs = [SystemMessage("두 문장으로 설명하세요."),
        {"role": "user", "content": "리스트란?"}]
r = fake.invoke(msgs)
print(type(r).__name__, "|", r.content)
print(r.content_blocks)

# 2) batch: 입력 여러 개를 한 번에
print([m.content for m in fake.batch(["질문1", "질문2"])])

# 3) ainvoke: 비동기 버전
print(asyncio.run(fake.ainvoke("질문")).content)
