from pydantic import BaseModel
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import (
    JsonOutputParser, PydanticOutputParser,
)
from langchain_core.exceptions import OutputParserException

class Answer(BaseModel):
    answer: str
    sources: list[str]
    found: bool

bad = [
    "답은 3개입니다.",                      # JSON이 아님
    '{"answer": "3개", "found": true}',    # 필드 빠짐
]
for text in bad:
    for p in (JsonOutputParser(),
              PydanticOutputParser(pydantic_object=Answer)):
        name = type(p).__name__
        try:
            print(name, "->", p.invoke(AIMessage(text)))
        except OutputParserException as e:
            first = str(e).splitlines()[0]
            print(name, "-> 실패:", first[:70])
