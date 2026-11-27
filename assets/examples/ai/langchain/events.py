import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)

model = GenericFakeChatModel(messages=iter(["안녕 하세요 반가워요"]))
chain = (ChatPromptTemplate.from_messages([("human", "{q}")])
         | model | StrOutputParser()).with_config(
             run_name="greeter")

async def main():
    async for ev in chain.astream_events(
            {"q": "hi"}, version="v2"):
        kind = ev["event"]
        if kind == "on_chat_model_stream":
            print(kind, repr(ev["data"]["chunk"].content))
        elif kind.endswith(("_start", "_end")):
            print(kind, ev["name"])
asyncio.run(main())
