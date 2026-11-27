from typing import Literal
from typing_extensions import TypedDict, Annotated
from pydantic import BaseModel, Field
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
text = "어제 산 키보드가 이틀 만에 고장 났어요. 환불해 주세요."

class Ticket(BaseModel):
    """고객 문의를 분류한 결과."""
    category: Literal["환불", "배송", "기타"]
    urgent: bool = Field(description="빨리 처리해야 하면 true")
    summary: str = Field(description="한 문장 요약")

t = llm.with_structured_output(Ticket).invoke(text)
print(type(t).__name__, t)

class TicketTD(TypedDict):
    """고객 문의를 분류한 결과."""
    category: Annotated[str, ..., "환불, 배송, 기타 중 하나"]
    urgent: Annotated[bool, ..., "급하면 true"]

print(llm.with_structured_output(TicketTD).invoke(text))

out = llm.with_structured_output(
    Ticket, include_raw=True).invoke(text)
print(out.keys())
print(out["raw"].tool_calls[0]["name"],
      out["parsing_error"])
