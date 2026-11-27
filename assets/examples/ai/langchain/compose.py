from langchain_core.runnables import (
    RunnableLambda, RunnableParallel, RunnablePassthrough)

clean = RunnableLambda(lambda s: s.strip())
upper = RunnableLambda(lambda s: s.upper())
chain = clean | upper
print(type(chain).__name__, chain.invoke("  hello  "))

both = RunnableParallel(
    length=RunnableLambda(len),
    words=RunnableLambda(lambda s: s.split()),
)
print(both.invoke("a b c"))

add = RunnablePassthrough.assign(
    n_chars=lambda d: len(d["question"]))
print(add.invoke({"question": "리스트란?"}))

# 딕셔너리는 자동으로 RunnableParallel이 된다
auto = clean | {"orig": RunnablePassthrough(),
                "up": upper}
print(auto.invoke(" hi "))
