import json, re, uuid
from typing import Any
from mlx_lm import load, generate
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import (
    convert_to_openai_tool,
)

ROLE = {"system": "system", "human": "user",
        "ai": "assistant", "tool": "tool"}
TAG = "<tool_call>"
NAME = re.compile(r'"name":\s*"([^"]+)"')
ARGS = re.compile(r'"arguments":\s*')
DEC = json.JSONDecoder()


def parse_calls(text):
    """<tool_call> 뒤에서 name과 arguments만 꺼낸다."""
    parts = text.split(TAG)
    calls = []
    for part in parts[1:]:
        name = NAME.search(part).group(1)
        start = ARGS.search(part).end()
        args, _ = DEC.raw_decode(part[start:])
        calls.append({"name": name, "args": args,
                      "id": "call_" + uuid.uuid4().hex[:8]})
    return parts[0].strip(), calls


def to_dict(m):
    d = {"role": ROLE[m.type], "content": m.content}
    if m.type == "ai" and m.tool_calls:
        d["tool_calls"] = [
            {"type": "function", "function": {
                "name": c["name"], "arguments": c["args"]}}
            for c in m.tool_calls]
    return d


class ChatMLX(BaseChatModel):
    """mlx-lm 모델을 LangChain 채팅 모델로 감싼다."""
    model_id: str
    max_tokens: int = 256
    tools: list = []
    forced: str | None = None   # 강제로 부를 도구 이름
    _mt: Any = None

    def model_post_init(self, _):
        self._mt = load(self.model_id)

    @property
    def _llm_type(self):
        return "mlx-local"

    def bind_tools(self, tools, *, tool_choice=None, **kw):
        specs = [convert_to_openai_tool(t) for t in tools]
        forced = None
        if tool_choice not in (None, "auto", "none"):
            # "any"나 도구 이름: 첫 번째(또는 그) 도구를 강제
            forced = (specs[0]["function"]["name"]
                      if tool_choice == "any" else tool_choice)
        clone = self.model_copy(
            update={"tools": specs, "forced": forced})
        return clone.bind(**kw) if kw else clone

    def _generate(self, messages, stop=None,
                  run_manager=None, **kw):
        model, tok = self._mt
        prompt = tok.apply_chat_template(
            [to_dict(m) for m in messages],
            tools=self.tools or None,
            add_generation_prompt=True, tokenize=False)
        head = ""
        if self.forced:  # 답의 앞부분을 미리 채워 호출을 강제
            head = (TAG + '\n{"name": "%s", '
                    '"arguments": ' % self.forced)
        text = head + generate(model, tok, prompt=prompt + head,
                               max_tokens=self.max_tokens)
        content, calls = parse_calls(text)
        n_in = len(tok.encode(prompt + head))
        n_out = len(tok.encode(text[len(head):]))
        msg = AIMessage(
            content=content, tool_calls=calls,
            usage_metadata={"input_tokens": n_in,
                            "output_tokens": n_out,
                            "total_tokens": n_in + n_out})
        return ChatResult(generations=[ChatGeneration(message=msg)])
