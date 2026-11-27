from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)
fake = GenericFakeChatModel(messages=iter(
    ["리스트는 여러 값을 순서대로 담는다."]))
full = None
for chunk in fake.stream("리스트란?"):
    print(repr(chunk.content), end=" ")
    full = chunk if full is None else full + chunk
print()
print(type(full).__name__, "|", full.content)
