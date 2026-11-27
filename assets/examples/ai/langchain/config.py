import time, asyncio
from langchain_core.runnables import (
    RunnableLambda, ConfigurableField)
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel)

# 1) 실행 시 바꿀 수 있는 필드
model = FakeListChatModel(responses=["A"]).configurable_fields(
    responses=ConfigurableField(id="answers"))
print(model.invoke("q").content)
print(model.invoke("q", config={
    "configurable": {"answers": ["B"]}}).content)

# 2) 갈아 끼울 수 있는 대안
alt = FakeListChatModel(responses=["기본 모델"]) \
    .configurable_alternatives(
        ConfigurableField(id="llm"), default_key="main",
        backup=FakeListChatModel(responses=["백업 모델"]))
print(alt.invoke("q").content,
      alt.with_config(configurable={"llm": "backup"})
         .invoke("q").content)

# 3) batch와 max_concurrency
slow = RunnableLambda(lambda x: time.sleep(0.5) or x)
for mc in (1, 4):
    t = time.perf_counter()
    slow.batch([1, 2, 3, 4], config={"max_concurrency": mc})
    print(f"max_concurrency={mc}: "
          f"{time.perf_counter() - t:.1f}s")
