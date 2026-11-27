from pydantic import BaseModel, Field
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
text = "어제 산 키보드가 이틀 만에 고장 났어요. 환불해 주세요."

class Short(BaseModel):
    """문의 요약."""
    summary: str = Field(max_length=5)

out = llm.with_structured_output(
    Short, include_raw=True).invoke(text)
print("raw args:", out["raw"].tool_calls[0]["args"])
print("parsed:", out["parsed"])
print("error:", type(out["parsing_error"]).__name__)

schema = {
    "title": "Sentiment",
    "description": "문장의 감정",
    "type": "object",
    "properties": {"label": {
        "type": "string", "enum": ["긍정", "부정"]}},
    "required": ["label"],
}
print(llm.with_structured_output(schema).invoke(text))
